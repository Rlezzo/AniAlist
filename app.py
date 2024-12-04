from flask import Flask
from backend.database.models import Base
from backend.database.database import engine
from flask_cors import CORS
import asyncio
from backend.views import rss_blueprint, magnet_blueprint
from backend.services.alist_api.alist_client import AlistClient
from backend.services.alist_api.alist_task_manager import AlistTaskManager
from backend.services.magnet_queue_manager import MagnetQueueManager
from backend.services.alist_api.directory_manager import DirectoryManager
from backend.services.alist_service import AlistService
from backend.core.config import base_url, token, root_save_path

base_url = "http://localhost:5244"  # 替换为你的 Alist 服务地址
token = "alist-391ab7ce-01ba-4f05-b3b9-7e26c8b59a363mdCDmKaQaAiiNMVUriWzKYyzwJQT1akK06oLiuz05xi2MfxcI5LK05FUqJCUARb"               # 替换为你的认证令牌

def create_app():
    app = Flask(__name__)

    # 离线下载存储根目录
    app.config['ROOT_SAVE_PATH'] = root_save_path

    # 创建 AlistClient 等 的唯一实例
    alist_client = AlistClient(base_url=base_url, token=token)
    alist_task_manager = AlistTaskManager(client=alist_client)
    directory_manager = DirectoryManager(client=alist_client)
    alist_service = AlistService(task_manager=alist_task_manager, directory_manager=directory_manager)
    magnet_queue_manager = MagnetQueueManager(alist_service)

    # 将实例存入 app 的配置中
    app.config['ALIST_CLIENT'] = alist_client
    app.config['ALIST_TASK_MANAGER'] = alist_task_manager
    app.config['DIRECTORY_MANAGER'] = directory_manager
    app.config['ALIST_SERVICE'] = alist_service
    app.config['MAGNET_QUEUE_MANAGER'] = magnet_queue_manager

    CORS(app)

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # 初始化数据库
    asyncio.run(init_models())

    # 注册蓝图
    app.register_blueprint(rss_blueprint, url_prefix='/api')
    app.register_blueprint(magnet_blueprint, url_prefix='/api')

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
