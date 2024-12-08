import hashlib
from . import Base
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey

class Magnet(Base):
    __tablename__ = 'magnets'

    id = Column(Integer, primary_key=True)
    rss_feed_id = Column(Integer, ForeignKey('rss_feeds.id'), nullable=False)
    title = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    magnet_link = Column(String(255), unique=True, nullable=False)
    magnet_hash = Column(String(64), nullable=False)  # 新增字段用于存储磁力链的散列值
    status = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.now())

    rss_feed = relationship('RSSFeed', back_populates='magnets')

    def __init__(self, rss_feed_id, title, magnet_link, name=None, status=False):
        self.rss_feed_id = rss_feed_id
        self.title = title
        self.name = name or title
        self.magnet_link = magnet_link
        self.magnet_hash = self.generate_magnet_hash(magnet_link)  # 生成磁力链的散列值
        print(self.magnet_hash)
        self.status = status

    @staticmethod
    def generate_magnet_hash(magnet_link: str) -> str:
        """生成磁力链的 MD5 散列值"""
        return hashlib.md5(magnet_link.encode('utf-8')).hexdigest()
