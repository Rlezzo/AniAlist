#alist_service.py
#和alist的相关交互操作
from typing import List, Optional
from dataclasses import dataclass, field
from .rss_service import get_rss_feed_by_id
from backend.database.models import Magnet
from backend.utils.logging_config import loguru_logger as logger
from backend.services.alist_api import AlistTaskManager, DirectoryManager
from backend.services.alist_api.task_constants import TaskType, DeletePolicy, ExecutionState

@dataclass
class AlistService:
    delete_policy: DeletePolicy 
    root_save_path: str
    task_manager: Optional[AlistTaskManager] = field(default=None)
    directory_manager: Optional[DirectoryManager] = field(default=None)

    def set_dependencies(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):  # 如果字段名和参数名一致，才能正确设置
                setattr(self, key, value)
                logger.debug(f"{self.__class__.__name__} 成功设置依赖 {key}")
            else:
                logger.warning(f"{self.__class__.__name__} 不存在属性 {key}，跳过设置")

    async def cancel_all_tasks(self, task_type: TaskType, task_state: ExecutionState = ExecutionState.UNDONE):
        """取消所有完成/未完成的下载任务"""
        try:
            # 获取所有完成/未完成的下载任务
            tasks_to_cancel = await self.task_manager.list_tasks(task_type=task_type, status=task_state)
            
            # 遍历取消所有符合条件的任务
            for task in tasks_to_cancel:
                await self.task_manager.cancel_task(task.tid, task_type)
                logger.debug(f"{'下载' if task_type == TaskType.DOWNLOAD else '上传'} 任务 {task.tid} 已成功取消。")
        except Exception as e:
            logger.error(f"取消所有任务时出现错误: {e}")

    async def reset_all_offline_tasks(self):
        """重置所有离线下载和上传任务，包括取消未完成任务和清除已完成任务"""
        try:
            # 1. 取消所有未完成的离线下载任务
            await self.cancel_all_tasks(task_type=TaskType.DOWNLOAD, task_state=ExecutionState.UNDONE)

            # 2. 取消所有未完成的离线上传任务
            await self.cancel_all_tasks(task_type=TaskType.TRANSFER, task_state=ExecutionState.UNDONE)

            # 3. 清除所有已完成的下载任务和上传任务
            await self.task_manager.clear_done_tasks(TaskType.DOWNLOAD)
            await self.task_manager.clear_done_tasks(TaskType.TRANSFER)
        except Exception as e:
            logger.error(f"重置所有离线任务时出现错误: {e}")

    async def retry_download_task(self, save_path: str, urls: List[str]):
        """重试下载任务，先取消所有未完成的任务，再清除已完成的任务，最后添加新任务"""
        try:
            await self.reset_all_offline_tasks()
            # 4. 添加新的离线下载任务
            await self.task_manager.add_download_task(save_path, urls, self.delete_policy)
        except Exception as e:
            logger.error(f"重试下载任务时出现错误: {e}")

    async def get_task_save_path(self, magnet: Magnet) -> str:
        # 1. 获取 task 对应 rss 的 name
        rss = await get_rss_feed_by_id(magnet.rss_feed_id)
        if not rss:
            raise ValueError(f"RSS Feed with id {magnet.rss_feed_id} not found")

        # 拼接完整的保存路径，例如：/downloads/rss_name/
        save_path = f"{self.root_save_path}/{rss.name}"

        # 2. 检查路径是否存在，不存在则创建
        
        # 检查目录是否存在
        exists = await self.directory_manager.check_path_exists(save_path)
        if not exists:
            # 目录不存在，创建目录
            await self.directory_manager.create_directory(save_path)

        # 3. 返回完整路径
        return save_path