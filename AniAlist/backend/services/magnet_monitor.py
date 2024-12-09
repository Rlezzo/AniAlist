# magnet_monitor.py
import asyncio
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .magnet_service import update_magnet
from backend.database.models import Magnet
from backend.services.alist_api import AlistTaskManager
from backend.services.alist_api.task_constants import TaskStatus, TaskType, ExecutionState
from backend.core.config import interval_time
from backend.utils.logging_config import loguru_logger as logger

@dataclass
class MagnetMonitor:
    timeout: timedelta  # 示例默认值
    task_manager: Optional[AlistTaskManager] = field(default=None) # 延迟注入
    monitored_magnet: Optional[Magnet] = field(default=None)
    start_time: Optional[datetime] = field(default=None)
    queue_manager = None  # 延迟注入

    def set_dependencies(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):  # 如果字段名和参数名一致，才能正确设置
                setattr(self, key, value)
                logger.debug(f"{self.__class__.__name__} 成功设置依赖 {key}")
            else:
                logger.warning(f"{self.__class__.__name__} 不存在属性 {key}，跳过设置")

    async def start_monitoring(self, magnet: Magnet):
        """
        开始监控一个任务。
        """
        if magnet:
            self.monitored_magnet = magnet
            self.start_time = datetime.now()
            logger.info(f"开始监控任务: {magnet.name}")
            # 调用监控任务
            await self.monitor_magnet()

    async def stop_monitoring(self):
        """
        停止监控任务。
        """
        if self.monitored_magnet:
            logger.info(f"停止监控任务: {self.monitored_magnet.name}")
        self.monitored_magnet = None
        self.start_time = None
        # 通知queue_manager开始下一个任务
        await self.queue_manager.process_magnet_queue()

    async def monitor_magnet(self):
        """
        定期检查被监控任务的状态。
        """
        while True:
            await asyncio.sleep(interval_time)  # 每X秒检查一次

            if not self.monitored_magnet:
                break

            # 检查任务状态
            try:
                if await self.check_status():
                    return
            except Exception as e:
                logger.error(f"检查任务状态时发生错误: {e}")

            if self.start_time and datetime.now() - self.start_time > self.timeout:
                # 任务超时处理
                logger.warning(f"任务超时: {self.monitored_magnet.name}")
                await self.stop_monitoring()
                break

    async def mark_magnet_as_completed(self):
        """
        标记任务为完成状态。
        """
        if not self.monitored_magnet:
            return

        try:
            # 更新数据库中的任务状态
            await update_magnet(self.monitored_magnet.id, {"status": True})
            logger.info(f"任务 {self.monitored_magnet.name} 已标记为完成")
        except Exception as e:
            logger.error(f"标记任务为完成时发生错误: {e}")

    async def check_status(self) -> bool:
        """
        检查任务状态，下载为2成功，且上传为2成功，表示任务成功。
        """
        if not self.monitored_magnet:
            return False

        try:
            download_tasks = await self.task_manager.list_tasks(task_type=TaskType.DOWNLOAD, status=ExecutionState.DONE)
            transfer_tasks = await self.task_manager.list_tasks(task_type=TaskType.TRANSFER, status=ExecutionState.DONE)
            
            if len(download_tasks) > 1 or len(transfer_tasks) > 1:
                logger.warning("监控到2个以上任务同时进行")
                for dl_task in download_tasks:
                    logger.debug(f"可能同时进行的任务：{dl_task.file_name}")

            # 都有成功记录的时候再检查，理论上应该是一个下载成功，一个上传成功
            if download_tasks and transfer_tasks: 
                dl_task = download_tasks[0]
                tf_task = transfer_tasks[0]
                if not await self.compare_tasks(self.monitored_magnet, dl_task.file_name):
                    logger.warning("当前监控任务与已完成任务不同")
                    logger.debug(f"监控的任务：{self.monitored_magnet.name}，已完成的任务：{dl_task.file_name}")
                    return False
                if dl_task.status == TaskStatus.SUCCEEDED and tf_task.status == TaskStatus.SUCCEEDED:  # 2 表示下载已完成
                    logger.info(f"监控的离线上传任务已完成: {self.monitored_magnet.name}")
                    await self.mark_magnet_as_completed()
                    await self.stop_monitoring()
                    return True
        except Exception as e:
            logger.error(f"检查任务时发生错误: {e}")
        return False

    async def compare_tasks(self, monitored_magnet: Magnet, magnet_link: str) -> bool:
        """根据磁力链散列值来比较任务"""
        if not monitored_magnet or not magnet_link:
            return False
        magnet_hash = Magnet.generate_magnet_hash(magnet_link)
        return monitored_magnet.magnet_hash == magnet_hash