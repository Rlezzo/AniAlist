# magnet_service.py
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from backend.database.models import Magnet
from backend.database.database import async_session
from backend.utils.logging_config import loguru_logger as logger

async def get_all_magnets():
    async with async_session() as session:
        result = await session.execute(select(Magnet))
        magnets = result.scalars().all()
        return magnets

async def get_magnet_by_id(magnet_id):
    async with async_session() as session:
        result = await session.execute(select(Magnet).where(Magnet.id == magnet_id))
        return result.scalars().first()

async def get_magnets_by_rss(rss_id):
    async with async_session() as session:
        result = await session.execute(select(Magnet).where(Magnet.rss_feed_id == rss_id))
        return result.scalars().all()
        
async def create_magnet(data):
    async with async_session() as session:
        new_magnet = Magnet(
            rss_feed_id=data['rss_feed_id'],
            title=data['title'],
            magnet_link=data['magnet_link'],
            name=data.get('name') or data['title'],
            status=False
        )
        session.add(new_magnet)
        await session.commit()

async def update_magnet(magnet_id, data):
    async with async_session() as session:
        result = await session.execute(select(Magnet).where(Magnet.id == magnet_id))
        magnet = result.scalars().first()
        if magnet:
            magnet.name = data.get('name', magnet.name)
            magnet.status = data.get('status', magnet.status)
            await session.commit()
            return True
        return False

async def delete_magnet(magnet_id):
    async with async_session() as session:
        result = await session.execute(select(Magnet).where(Magnet.id == magnet_id))
        magnet = result.scalars().first()
        if magnet:
            await session.delete(magnet)
            await session.commit()
            return True
        return False

async def save_magnets_to_db(torrents):
    """
    将解析到的磁力链接保存到数据库中的 magnet 表，并确保每个任务绑定到相应的 rss_feed_id。
    """
    async with async_session() as session:
        try:
            for torrent in torrents:
                # 检查是否已经存在这个磁力链接，避免重复
                existing_magnet = await session.execute(
                    select(Magnet).where(Magnet.magnet_link == torrent['magnet_link'])
                )
                if existing_magnet.scalars().first() is None:
                    new_magnet = Magnet(
                        rss_feed_id=torrent['rss_feed_id'],  # 绑定到相应的 RSSFeed
                        title=torrent['title'],
                        name=torrent['title'],  # 默认情况下，name = title
                        magnet_link=torrent['magnet_link'],
                        status=False
                    )
                    session.add(new_magnet)
            await session.commit()
            logger.debug("所有任务已成功保存到数据库。")
        except SQLAlchemyError as e:
            logger.error(f"数据库操作失败: {e}")
            await session.rollback()

async def get_pending_magnets():
    """
    从数据库中获取所有未完成的任务。
    """
    async with async_session() as session:
        try:
            result = await session.execute(select(Magnet).where(Magnet.status == False))
            magnets = result.scalars().all()
            return magnets
        except Exception as e:
            logger.error(f"从数据库加载任务时出错: {e}")
            return []