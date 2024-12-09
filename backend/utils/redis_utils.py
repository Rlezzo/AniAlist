from redis.asyncio import Redis
    
class RedisLock:
    """异步 Redis 锁封装"""
    def __init__(self, lock_name: str, timeout: int = 30):
        self.lock_name = lock_name
        self.timeout = timeout
        self.redis_client = Redis(host="localhost", port=6379, decode_responses=False)

    async def acquire(self) -> bool:
        """异步获取锁"""
        return await self.redis_client.set(self.lock_name, "locked", ex=self.timeout, nx=True)

    async def release(self):
        """异步释放锁"""
        if await self.redis_client.get(self.lock_name):
            await self.redis_client.delete(self.lock_name)

    async def is_locked(self) -> bool:
        """检查锁是否存在"""
        return await self.redis_client.exists(self.lock_name) == 1

# 创建redis锁实例
lock = RedisLock("task_lock", timeout=30)