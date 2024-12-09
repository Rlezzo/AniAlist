import os
from loguru import logger

# 程序日志路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
# 登录日志目录路径
LOGIN_LOG_DIR = os.path.join(LOGS_DIR, "login")
LOGIN_LOG_FILE = os.path.join(LOGS_DIR, 'login', 'login.log')

# 检查目录是否存在，不存在则创建
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(LOGIN_LOG_DIR, exist_ok=True)

# 清除默认的处理器
logger.remove()

# 配置程序日志
logger.add(
    os.path.join(LOGS_DIR, "app_{time:YYYY-MM-DD}.log"),
    rotation="00:00",
    retention="90 days",
    compression="zip",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{function}:{line} - {message}",
    enqueue=True,  # 异步写入日志，防止阻塞
)

# 配置登录日志
logger.add(
    os.path.join(LOGIN_LOG_DIR, "login.log"),
    format="{time:YYYY-MM-DD HH:mm:ss} | 用户: {extra[username]} | IP 地址: {extra[ip_address]}",
    rotation="1 MB",
    level="INFO",
    filter=lambda record: "username" in record["extra"] and "ip_address" in record["extra"],
    enqueue=True,
)

# 导出 logger 实例
loguru_logger = logger
