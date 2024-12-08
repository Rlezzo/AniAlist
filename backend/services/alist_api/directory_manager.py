import aiohttp
from dataclasses import dataclass
from .alist_client import AlistClient
from backend.utils.logging_config import loguru_logger as logger

@dataclass
class DirectoryManager:
    client: AlistClient

    async def check_path_exists(self, path: str) -> bool:
        """检查给定的路径是否存在"""
        try:
            await self.client.check_path_exists(path)
            logger.debug(f"路径 {path} 存在。")
            return True
        except aiohttp.ClientResponseError as e:
            if e.status == 500:
                logger.debug(f"路径 {path} 不存在。")
            else:
                logger.error(f"检查路径时发生 HTTP 错误: {e.status}, {e.message}")
        except Exception as e:
            logger.error(f"检查路径时发生错误: {e}")
        return False

    async def create_directory(self, path: str) -> bool:
        """创建给定的目录"""
        try:
            await self.client.create_directory(path)
            logger.info(f"目录 {path} 创建成功。")
            return True
        except aiohttp.ClientResponseError as e:
            logger.error(f"创建目录时发生 HTTP 错误: {e.status}, {e.message}")
        except Exception as e:
            logger.error(f"创建目录时发生错误: {e}")
        return False

    async def rename_directory(self, current_path: str, new_name: str) -> bool:
        """重命名文件夹"""
        try:
            await self.client.rename_directory(current_path, new_name)
            logger.info(f"目录 {current_path} 成功重命名为 {new_name}")
            return True
        except aiohttp.ClientResponseError as e:
            logger.error(f"重命名目录时发生 HTTP 错误: {e.status}, {e.message}")
        except Exception as e:
            logger.error(f"重命名目录时发生错误: {e}")
        return False

    async def delete_directory(self, dir_path: str, names: list) -> bool:
        """删除指定目录下的文件夹或文件"""
        try:
            await self.client.delete_directory(dir_path, names)
            logger.info(f"目录 {dir_path} 下的文件/文件夹 {names} 删除成功")
            return True
        except aiohttp.ClientResponseError as e:
            logger.error(f"删除目录时发生 HTTP 错误: {e.status}, {e.message}")
        except Exception as e:
            logger.error(f"删除目录时发生错误: {e}")
        return False