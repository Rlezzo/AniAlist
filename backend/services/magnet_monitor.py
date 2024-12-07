# magnet_monitor.py
import asyncio
from typing import Optional
from datetime import datetime, timedelta

from backend.database.models import Magnet
from .magnet_service import update_magnet
from backend.services.alist_api import AlistTaskManager
from backend.services.alist_api.task_constants import TaskStatus, TaskType, ExecutionState
from backend.core.config import over_time, interval_time

class MagnetMonitor:
    def __init__(self, task_manager: AlistTaskManager):
        self.monitored_magnet: Optional[Magnet] = None
        self.start_time: Optional[datetime] = None
        self.timeout: timedelta = timedelta(minutes=over_time)  # 超时时间
        self.task_manager = task_manager
        self.queue_manager = None  # 队列管理器实例，延迟注入

    def set_queue_manager(self, queue_manager):
        """设置队列管理器实例"""
        self.queue_manager = queue_manager

    async def start_monitoring(self, magnet: Magnet):
        """
        开始监控一个任务。
        """
        if magnet:
            self.monitored_magnet = magnet
            self.start_time = datetime.now()
            print(f"开始监控任务: {magnet.name}")
            # 调用监控任务
            await self.monitor_magnet()

    async def stop_monitoring(self):
        """
        停止监控任务。
        """
        if self.monitored_magnet:
            print(f"停止监控任务: {self.monitored_magnet.name}")
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
                print("没有任务需要监控。")
                break

            # 检查任务状态
            try:
                if await self.check_status():
                    return
            except Exception as e:
                print(f"检查任务状态时发生错误: {e}")

            if self.start_time and datetime.now() - self.start_time > self.timeout:
                # 任务超时处理
                print(f"任务超时: {self.monitored_magnet.name}")
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
            print(f"任务 {self.monitored_magnet.name} 已标记为完成")
        except Exception as e:
            print(f"标记任务为完成时发生错误: {e}")

    async def check_status(self) -> bool:
        """
        检查任务状态，下载为2成功，且上传为2成功，表示任务成功。
        """
        if not self.monitored_magnet:
            return False

        try:
            download_tasks = await self.task_manager.list_tasks(task_type=TaskType.DOWNLOAD, status=ExecutionState.DONE)
            transfer_tasks = await self.task_manager.list_tasks(task_type=TaskType.TRANSFER, status=ExecutionState.DONE)

            # 都有成功记录的时候再检查，理论上应该是一个下载成功，一个上传成功
            if download_tasks and transfer_tasks: 
                dl_task = download_tasks[0]
                tf_task = transfer_tasks[0]
                if not await self.compare_tasks(self.monitored_magnet, dl_task.file_name):
                    print("当前监控任务与已完成任务不同")
                    return False
                if dl_task.status == TaskStatus.SUCCEEDED and tf_task.status == TaskStatus.SUCCEEDED:  # 2 表示下载已完成
                    print(f"监控任务任务离线上传已完成: {self.monitored_magnet.name}")
                    await self.mark_magnet_as_completed()
                    await self.stop_monitoring()
                    return True
        except Exception as e:
            print(f"检查任务时发生错误: {e}")
        return False

    async def compare_tasks(self, monitored_magnet: Magnet, magnet_link: str) -> bool:
        """根据磁力链散列值来比较任务"""
        if not monitored_magnet or not magnet_link:
            return False
        magnet_hash = Magnet.generate_magnet_hash(magnet_link)
        return monitored_magnet.magnet_hash == magnet_hash