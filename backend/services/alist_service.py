#alist_service.py
#和alist的相关交互操作
from typing import List
from flask import current_app
from backend.services.alist_api.task_constants import TaskType, DeletePolicy, ExecutionState
from backend.services.alist_api.alist_task_manager import AlistTaskManager
from backend.services.alist_api.directory_manager import DirectoryManager
from backend.services import rss_service
from backend.database.models import Magnet

class AlistService:
    def __init__(self, task_manager: AlistTaskManager, directory_manager: DirectoryManager, delete_policy: DeletePolicy = None, root_save_path: str = None):
        self.task_manager = task_manager
        self.directory_manager = directory_manager
        # 如果未传入 delete_policy，默认从 Flask 配置中获取
        self.delete_policy = delete_policy or DeletePolicy(current_app.config.get('DELETE_POLICY', DeletePolicy.DELETE_ALWAYS))
        self.root_save_path = root_save_path or current_app.config.get('ROOT_SAVE_PATH', '/yidong/bangumi')

    async def cancel_all_tasks(self, task_type: TaskType, task_state: ExecutionState = ExecutionState.UNDONE):
        """取消所有完成/未完成的下载任务"""
        try:
            # 获取所有完成/未完成的下载任务
            tasks_to_cancel = await self.task_manager.list_tasks(task_type=task_type, status=task_state)
            
            # 遍历取消所有符合条件的任务
            for task in tasks_to_cancel:
                await self.task_manager.cancel_task(task.tid, task_type)
                print(f"{'下载' if task_type == TaskType.DOWNLOAD else '上传'} 任务 {task.id} 已成功取消。")
        except Exception as e:
            print(f"取消所有任务时出现错误: {e}")

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
            print(f"重置所有离线任务时出现错误: {e}")

    async def retry_download_task(self, save_path: str, urls: List[str]):
        """重试下载任务，先取消所有未完成的任务，再清除已完成的任务，最后添加新任务"""
        try:
            await self.reset_all_offline_tasks()
            # 4. 添加新的离线下载任务
            await self.task_manager.add_download_task(save_path, urls, self.delete_policy)
        except Exception as e:
            print(f"重试下载任务时出现错误: {e}")

    async def get_task_save_path(self, magnet: Magnet) -> str:
        # 1. 获取 task 对应 rss 的 name
        rss = await rss_service.get_rss_feed_by_id(magnet.rss_feed_id)
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