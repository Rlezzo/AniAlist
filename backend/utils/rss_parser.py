import aiohttp
import feedparser
import asyncio

# 设置代理
PROXIES = {
    "http": "http://host.docker.internal:7897",
    "https": "http://host.docker.internal:7897"
}

async def parse_rss_feed(feed_url, rss_feed_id, proxy=None):
    """
    解析单个 RSSFeed，返回磁力链接列表，并包含对应的 rss_feed_id。
    """
    try:
        async with aiohttp.ClientSession() as http_session:
            async with http_session.get(feed_url, proxy=proxy, timeout=10) as response:
                if response.status != 200:
                    raise Exception(f"无法获取 RSSFeed: {response.status}")
                content = await response.text()
                feed = feedparser.parse(content)

                if feed.bozo:
                    raise Exception(f"解析 RSSFeed 失败: {feed.bozo_exception}")

                torrents = []
                for entry in feed.entries:
                    title = entry.title
                    magnet_link = None
                    for link in entry.get('links', []):
                        if link.get('rel') == "enclosure" and link.get('type') == "application/x-bittorrent":
                            magnet_link = link.get('href')
                            break
                        elif 'magnet' in link.get('href', ''):
                            magnet_link = link.get('href')
                            break

                    if magnet_link:
                        torrents.append({
                            "rss_feed_id": rss_feed_id,
                            "magnet_link": magnet_link,
                            "title": title
                        })

                return torrents

    except Exception as e:
        print(f"解析 RSSFeed '{feed_url}' 失败: {e}")
        # 尝试使用代理重新解析
        if not proxy:
            print(f"尝试使用代理重新解析 RSSFeed '{feed_url}'")
            return await parse_rss_feed(feed_url, rss_feed_id, proxy=PROXIES.get("http"))
        return []

async def parse_multiple_rss(feed_urls_with_ids):
    """
    解析多个 RSSFeeds，返回所有磁力链接。
    feed_urls_with_ids 是一个包含元组 (feed_url, rss_feed_id) 的列表。
    """
    all_torrents = []
    tasks = [parse_rss_feed(url, rss_feed_id) for url, rss_feed_id in feed_urls_with_ids]
    results = await asyncio.gather(*tasks)
    for torrents in results:
        all_torrents.extend(torrents)
    return all_torrents
