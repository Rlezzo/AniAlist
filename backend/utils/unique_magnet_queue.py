import asyncio
from typing import Generic, TypeVar
from backend.utils.logging_config import loguru_logger as logger

T = TypeVar('T')

class UniqueMagnetQueue(Generic[T]):
    def __init__(self):
        self.queue = asyncio.Queue()  # 用于存储队列中的任务
        self.item_ids = set()  # 用于存储队列中的唯一项（基于 ID）
        self.lock = asyncio.Lock()  # 用于保证队列和 set 的同步操作

    async def put(self, item: T):
        """将新元素加入队列，确保唯一性"""
        async with self.lock:
            # 使用 item.id 来判断是否唯一
            item_id = getattr(item, 'id', None)
            if item_id is None:
                raise ValueError("Item does not have an 'id' attribute")

            if item_id not in self.item_ids:
                await self.queue.put(item)
                self.item_ids.add(item_id)
                logger.debug(f"Item {item_id} added to the queue.")
            else:
                logger.debug(f"Item {item_id} is already in the queue.")

    async def get(self) -> T:
        """从队列中取出一个元素"""
        async with self.lock:
            item = await self.queue.get()
            item_id = getattr(item, 'id', None)
            if item_id is not None:
                self.item_ids.remove(item_id)
            return item

    async def remove(self, item: T):
        """从队列和集合中移除指定元素"""
        async with self.lock:
            item_id = getattr(item, 'id', None)
            if item_id in self.item_ids:
                # 创建一个新的队列来过滤掉要移除的项
                new_queue = asyncio.Queue()
                while not self.queue.empty():
                    current_item = await self.queue.get()
                    current_item_id = getattr(current_item, 'id', None)
                    if current_item_id != item_id:
                        await new_queue.put(current_item)
                self.queue = new_queue
                self.item_ids.remove(item_id)
                logger.debug(f"Item {item_id} removed from the queue.")

    def empty(self) -> bool:
        """检查队列是否为空"""
        return self.queue.empty()

    def __contains__(self, item: T) -> bool:
        """检查元素是否在队列中"""
        item_id = getattr(item, 'id', None)
        return item_id in self.item_ids

    def __len__(self) -> int:
        """返回队列中元素的数量"""
        return len(self.item_ids)
