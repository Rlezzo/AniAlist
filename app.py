import asyncio
from flask import Flask
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler

from backend.database.models import Base
from backend.database.database import engine

from backend.services import rss_service, magnet_service, MagnetQueueManager, MagnetMonitor, AlistService
from backend.services.alist_api import AlistClient, AlistTaskManager, DirectoryManager

from backend.core.config import base_url, token, delete_policy, root_save_path, timeout
from backend.views import rss_blueprint, magnet_blueprint, log_blueprint, auth_blueprint
from backend.utils.dependency_manager import DependencyManager, DependencyKeys as DKeys
from backend.utils.token_required_middleware import token_required_middleware
# from backend.utils.file_lock import FileLock

def create_app():
    app = Flask(__name__)

    # 创建 AlistClient 等 的唯一实例
    alist_client = AlistClient(base_url=base_url, token=token)
    alist_task_manager = AlistTaskManager(client=alist_client)
    directory_manager = DirectoryManager(client=alist_client)
    alist_service = AlistService(delete_policy=delete_policy, root_save_path=root_save_path)
    magnet_queue_manager = MagnetQueueManager()
    magnet_monitor = MagnetMonitor(timeout=timeout)

    # 初始化依赖注入管理器
    dependency_manager = DependencyManager()
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

    async def init_models():
        """异步初始化数据库模型"""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    # 初始化数据库
    asyncio.run(init_models())

    # 应用中间件
    token_required_middleware([rss_blueprint, magnet_blueprint, log_blueprint])

    # 注册蓝图
    app.register_blueprint(rss_blueprint, url_prefix='/api')
    app.register_blueprint(magnet_blueprint, url_prefix='/api')
    app.register_blueprint(log_blueprint, url_prefix='/api')
    app.register_blueprint(auth_blueprint, url_prefix='/api')

    # 重载app.run(debug=True, use_reloader=True)模式下会有多次运行的情况
    # 创建文件锁实例
    # lock = FileLock(lock_file_path='scheduler.lock', expiration_time=10)
    # count = 1
    # async def update_rss_and_process_queue():
    #     """
    #     启动任务队列处理。
    #     """
    #     import datetime
    #     # 检查锁文件是否存在且未过期
    #     if lock.is_locked():
    #         print(f"任务已在短时间内执行，跳过本次运行。当前时间: {datetime.datetime.now()}")
    #         return
        
    #     # 创建锁文件或更新其时间戳
    #     lock.acquire_lock()

    #     try:
    #         print(count)
    #         print(f"{datetime.datetime.now()}")
    #     finally:
    #     # 更新锁文件的时间戳（相当于保留锁但刷新时间）
    #         lock.acquire_lock()

    async def update_rss_and_process_queue():
        """
        启动任务队列处理。
        """
        await rss_service.refresh_all_rss_feeds()
        # 从数据库中获取未完成的任务
        pending_magnets = await magnet_service.get_pending_magnets()
        await magnet_queue_manager.add_magnets_to_queue(pending_magnets)

        # 如果没有正在进行的任务，尝试处理任务
        if not magnet_queue_manager.current_magnet:
            await magnet_queue_manager.process_magnet_queue()

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=lambda: asyncio.run(update_rss_and_process_queue()), trigger="interval", minutes=90)
    scheduler.start()
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)
