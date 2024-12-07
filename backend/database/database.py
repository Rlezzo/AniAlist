from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 配置数据库连接，使用异步 SQLite
DATABASE_URL = "sqlite+aiosqlite:///backend/database/rss_magnet.db"

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 是否打印SQL日志
    future=True
)

# 创建异步 Session 工厂
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)
