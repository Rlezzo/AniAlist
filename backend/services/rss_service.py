#rss_service.py
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from backend.utils import rss_parser
from backend.database.models import RSSFeed, Magnet
from backend.database.database import async_session
from .magnet_service import save_magnets_to_db

# 查找
async def get_all_rss_feeds():
    """
    从数据库中获取所有 RSS 订阅。
    """
    async with async_session() as session:
        try:
            result = await session.execute(select(RSSFeed))
            feeds = result.scalars().all()
            return feeds
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None

async def get_rss_feed_by_id(rss_id):
    """
    从数据库中获取特定 ID 的 RSS 订阅。
    """
    async with async_session() as session:
        try:
            result = await session.execute(select(RSSFeed).where(RSSFeed.id == rss_id))
            feed = result.scalars().first()
            return feed
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None

# 增加
async def create_rss_feed(name, url):
    """
    在数据库中创建新的 RSS 订阅。
    """
    async with async_session() as session:
        try:
            new_feed = RSSFeed(
                name=name,
                url=url,
                last_updated=datetime.now()
            )
            session.add(new_feed)
            await session.commit()
            return new_feed
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            await session.rollback()
            return None

# 修改
async def update_rss_feed(rss_id, data):
    """
    更新 RSS 订阅信息。
    :param rss_id: 要更新的 RSS 订阅的 ID
    :param data: 包含更新信息的字典
    :return: 成功返回 True，失败返回 False 和错误信息
    """
    async with async_session() as session:
        try:
            result = await session.execute(select(RSSFeed).where(RSSFeed.id == rss_id))
            feed = result.scalars().first()
            if feed:
                feed.name = data.get('name', feed.name)
                feed.url = data.get('url', feed.url)
                feed.last_updated = data.get('last_updated', feed.last_updated)
                await session.commit()
                return True, None
            return False, "RSS feed not found"
        except SQLAlchemyError as e:
            await session.rollback()  # 在出现错误时回滚
            return False, str(e)

async def patch_rss_feed(rss_id, update_data):
    """
    更新 RSS 源的部分字段。
    :param rss_id: 要更新的 RSS 订阅的 ID
    :param update_data: 包含要更新的字段和值的字典
    :return: 成功返回 True，失败返回 False
    """
    async with async_session() as session:
        try:
            # 查询目标 RSS 订阅
            result = await session.execute(select(RSSFeed).where(RSSFeed.id == rss_id))
            rss_feed = result.scalars().first()

            if not rss_feed:
                return False

            # 更新允许的字段
            for key, value in update_data.items():
                setattr(rss_feed, key, value)

            # 提交更新
            await session.commit()
            return True
        except SQLAlchemyError as e:
            await session.rollback()  # 回滚更改以防止不一致
            print(f"Database error: {e}")
            return False
        
# 删除
async def delete_rss_feed(rss_id):
    """
    根据给定的 rss_id 删除对应的 RSS 订阅及其相关的任务。
    """
    async with async_session() as session:
        try:
            # 查找 RSS 源
            result = await session.execute(select(RSSFeed).where(RSSFeed.id == rss_id))
            feed = result.scalars().first()
            if feed:
                # 查找与该 RSS 源相关的任务
                tasks_to_delete = await session.execute(select(Magnet).where(Magnet.rss_feed_id == rss_id))
                tasks = tasks_to_delete.scalars().all()

                # 删除所有任务
                for task in tasks:
                    await session.delete(task)

                # 删除 RSS 源
                await session.delete(feed)
                await session.commit()

                return {"message": "RSS feed and associated tasks deleted successfully!"}, 200
            else:
                return {"error": "RSS feed not found"}, 404
        except SQLAlchemyError as e:
            await session.rollback()
            return {"error": str(e)}, 500
        
# 订阅更新
async def refresh_all_rss_feeds():
    """
    更新所有的 RSS 源，并将新的磁力链接保存到数据库。
    """
    rss_feeds = await get_all_rss_feeds()
    if not rss_feeds:
        return False, "Failed to fetch RSS feeds."

    # 提取 打勾的 RSS 源的 URL 和 ID
    feed_urls_with_ids = [
        (rss_feed.url, rss_feed.id)
        for rss_feed in rss_feeds
        if rss_feed.should_update
    ]

    # 解析 RSS 并获取新的磁力链接
    torrents = await rss_parser.parse_multiple_rss(feed_urls_with_ids)

    # 将新的磁力链接保存到数据库
    await save_magnets_to_db(torrents)

    # 更新所有 RSS 源的 `last_updated` 字段
    for rss_feed in rss_feeds:
        await update_rss_feed(rss_feed.id, {"last_updated": datetime.now()})

    return True, "RSS feeds updated and new tasks have been added."

async def refresh_rss_feed(rss_id):
    """
    更新指定的 RSS 源，并将新的磁力链接保存到数据库。
    """
    rss_feed = await get_rss_feed_by_id(rss_id)
    if not rss_feed:
        return False, "RSS feed not found."

    # 解析指定的 RSS 源
    torrents = await rss_parser.parse_rss_feed(rss_feed.url, rss_feed.id)

    # 将新的磁力链接保存到数据库
    await save_magnets_to_db(torrents)

    # 更新 RSS 源的 `last_updated` 字段
    await update_rss_feed(rss_id, {"last_updated": datetime.now()})

    return True, f"RSS feed '{rss_feed.name}' updated and new tasks have been added."