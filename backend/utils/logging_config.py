from loguru import logger

# 配置 loguru 日志
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="90 days",
    compression="zip",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{function}:{line} - {message}"
)
