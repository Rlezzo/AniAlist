from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from . import Base  # 从 models 导入 Base

class RSSFeed(Base):
    __tablename__ = 'rss_feeds'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False, unique=True)
    last_updated = Column(DateTime, nullable=False)
    should_update = Column(Boolean, default=True)

    tasks = relationship('Magnet', back_populates='rss_feed')