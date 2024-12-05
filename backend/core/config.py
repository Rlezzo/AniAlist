from backend.services.alist_api.task_constants import DeletePolicy

base_url = "http://localhost:5244"  # 替换为你的 Alist 服务地址
token = "alist-391ab7ce-01ba-4f05-b3b9-7e26c8b59a363mdCDmKaQaAiiNMVUriWzKYyzwJQT1akK06oLiuz05xi2MfxcI5LK05FUqJCUARb"               # 替换为你的认证令牌
root_save_path = '/123pan/test'
delete_policy = DeletePolicy.DELETE_ALWAYS
over_time = 90 # 任务超时时间，分钟
interval_time = 10 # 监视任务完成间隔，秒

# 配置数据库连接，使用异步 SQLite
DATABASE_URL = "sqlite+aiosqlite:///backend/database/rss_magnet.db"