from datetime import timedelta
from backend.services.alist_api.task_constants import DeletePolicy

# 用户存储
users = {
    "admin": b"$2b$12$QEYV2GWRV8EsOuZEJ0vgs.cLpiFwsQR8wN3APqQ2klrcdFTeS0xHm"
}

# 设置代理
PROXIES = {
    "http": "http://host.docker.internal:7897",
    "https": "http://host.docker.internal:7897"
}

base_url = "http://localhost:5244"  # 替换为你的 Alist 服务地址
token = "alist-391ab7ce-01ba-4f05-b3b9-7e26c8b59a363mdCDmKaQaAiiNMVUriWzKYyzwJQT1akK06oLiuz05xi2MfxcI5LK05FUqJCUARb"               # 替换为你的认证令牌

# 网盘存储目录
root_save_path = '/123pan/test'
# 离线任务完成后对于下载资源的操作
delete_policy = DeletePolicy.DELETE_ALWAYS
timeout = 90 # 任务超时时间，分钟
interval_time = 10 # 监视任务完成间隔，秒

SECRET_KEY = 'your_super_secret_key'

BLOCKED_WORDS = [
    "全集",
    "合集"
    # 添加更多屏蔽词...
]

# token过期刷新窗口为 10 分钟
REFRESH_WINDOW = timedelta(minutes=10)  