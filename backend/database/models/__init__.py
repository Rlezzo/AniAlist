# backend/database/models
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# 导入所有模型以便于外部可以访问
from .rss_feed import RSSFeed
from .task import Magnet
