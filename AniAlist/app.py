import asyncio
import threading
from flask import Flask
from flask_cors import CORS
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.database.models import Base
from backend.database.database import engine

from backend.services import MagnetQueueManager, MagnetMonitor, AlistService, rss_service, magnet_service
from backend.services.alist_api import AlistClient, AlistTaskManager, DirectoryManager

from backend.core.config import base_url, token, delete_policy, root_save_path, timeout
from backend.views import rss_blueprint, magnet_blueprint, log_blueprint, auth_blueprint
from backend.utils.dependency_manager import dependency_manager, DependencyKeys as DKeys
from backend.utils.token_required_middleware import token_required_middleware

def create_app():
    app = Flask(__name__)

    # 创建 AlistClient 等 的唯一实例
    alist_client = AlistClient(base_url=base_url, token=token)
    alist_task_manager = AlistTaskManager(client=alist_client)
    directory_manager = DirectoryManager(client=alist_client)
    alist_service = AlistService(delete_policy=delete_policy, root_save_path=root_save_path)
    magnet_queue_manager = MagnetQueueManager()
    magnet_monitor = MagnetMonitor(timeout=timeout)

    # 注册实例到管理器
    dependency_manager.register(DKeys.ALIST_CLIENT, alist_client)
    dependency_manager.register(DKeys.ALIST_SERVICE, alist_service)
    dependency_manager.register(DKeys.ALIST_TASK_MANAGER, alist_task_manager)
    dependency_manager.register(DKeys.DIRECTORY_MANAGER, directory_manager)
    dependency_manager.register(DKeys.MAGNET_QUEUE_MANAGER, magnet_queue_manager)
    dependency_manager.register(DKeys.MAGNET_MONITOR, magnet_monitor)

    # 延迟注入依赖关系
    dependency_manager.inject_dependencies()

    CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

    # 应用中间件
    token_required_middleware([rss_blueprint, magnet_blueprint, log_blueprint])

    # 注册蓝图
    app.register_blueprint(rss_blueprint, url_prefix='/api')
    app.register_blueprint(magnet_blueprint, url_prefix='/api')
    app.register_blueprint(log_blueprint, url_prefix='/api')
    app.register_blueprint(auth_blueprint, url_prefix='/api')

    # 重载app.run(debug=True, use_reloader=True)模式下，或者多worker下会有多次运行的情况

    async def init_models():
        """异步初始化数据库模型"""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def update_rss_and_process_queue():
        await rss_service.refresh_all_rss_feeds()
        # 获取待处理任务
        pending_magnets = await magnet_service.get_pending_magnets()
        await magnet_queue_manager.add_magnets_to_queue(pending_magnets)
        # 如果无正在进行的任务，则处理队列
        if not magnet_queue_manager.current_magnet:
            await magnet_queue_manager.process_magnet_queue()

    # 创建并设置独立事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 在后台线程中启动事件循环
    def run_loop():
        loop.run_forever()

    t = threading.Thread(target=run_loop, daemon=True)
    t.start()

    # 使用 run_coroutine_threadsafe 在后台运行 init_models
    future = asyncio.run_coroutine_threadsafe(init_models(), loop)
    future.result()  # 等待初始化完成（可选）

    scheduler = AsyncIOScheduler(event_loop=loop)
    scheduler.add_job(update_rss_and_process_queue, 'interval', minutes=90)
    scheduler.start()
    
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)
