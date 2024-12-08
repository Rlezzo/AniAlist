# offline_download.py
from typing import List
from dataclasses import dataclass
from .alist_task import AlistTask
from .alist_client import AlistClient
from .task_constants import TaskType, DeletePolicy, DownloaderType, ExecutionState
from backend.utils.logging_config import loguru_logger as logger

@dataclass
class AlistTaskManager:
    client: AlistClient

    async def add_download_task(self, save_path: str, urls: list[str], delete_policy: DeletePolicy = DeletePolicy.DELETE_ALWAYS, downloader_tool=DownloaderType.QBIT):
        """添加一个新的离线下载任务"""
        try:
            # 使用 AlistClient 来发送请求
            response = await self.client.add_offline_download_task(
                save_path=save_path,
                urls=urls,
                delete_policy=delete_policy.value,
                downloader_tool=downloader_tool.value
            )
            # 从响应中提取任务 ID
            if response and 'tasks' in response and isinstance(response['tasks'], list):
                descriptions = [task['name'] for task in response['tasks']]
                logger.info("下载任务添加成功，任务描述：", ", ".join(descriptions))
            else:
                logger.debug("下载任务添加失败，未返回有效的任务信息")
        except Exception as e:
            logger.error(f"添加下载任务时出现错误: {e}")
        
    async def cancel_task(self, task_id: str, task_type: TaskType):
        """取消特定任务, 指取消进行中的下载上传任务"""
        try:
            await self.client.cancel_task(task_type, task_id)
            logger.debug(f"任务 {task_id} 取消成功。")
        except Exception as e:
            logger.error(f"取消任务时出现错误: {e}")

    async def clear_done_tasks(self, task_type: TaskType):
        """清除所有已完成的任务, 指清除所有非正在进行中的任务"""
        try:
            await self.client.clear_done_tasks(task_type)
            logger.debug(f"所有已完成的 {task_type.value} 任务已清除。")
        except Exception as e:
            logger.error(f"清除已完成任务时出现错误: {e}")

    async def list_tasks(self, task_type: TaskType, status: ExecutionState=ExecutionState.UNDONE) -> List[AlistTask]:
        """列出指定类型和状态的任务"""
        try:
            response = await self.client.list_tasks(task_type, status)
            if response:
                # 转换为AlistTask格式
                tasks = [AlistTask.from_json(task) for task in response]
                return tasks
            else:
                logger.debug(f"没有找到 {'下载' if task_type == TaskType.DOWNLOAD else '上传'} {'完成' if status == 'done' else '未完成'} 的任务。")
                return []
        except Exception as e:
            logger.error(f"获取任务列表时出现错误: {e}")
            return []