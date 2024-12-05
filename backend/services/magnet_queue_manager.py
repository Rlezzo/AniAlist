# task_queue_manager.py

from . import AlistService
from typing import List, Optional
from backend.database.models import Magnet
from backend.utils.unique_magnet_queue import UniqueMagnetQueue as UMQueue

class MagnetQueueManager:
    def __init__(self, alist_service: AlistService):
        self.download_queue = UMQueue()  # 下载任务队列
        self.suspended_queue = UMQueue()  # 被挂起的任务队列
        self.current_magnet: Optional[Magnet] = None  # 当前正在执行的 magnet
        self.alist_service = alist_service
        self.monitor = None  # 监控器实例，延迟注入

    def set_monitor(self, monitor):
        """设置监控器实例"""
        self.monitor = monitor

    async def add_magnets_to_queue(self, magnets: List[Magnet]):
        """
        将传入的未完成磁链列表加入到下载队列中，确保磁链的唯一性。
        """
        added_count = 0
        for magnet in magnets:
            # 这里不再需要手动操作 self.magnet_ids_in_queue，因为 UniqueMagnetQueue 会管理唯一性
            if magnet.id not in self.download_queue:  # 直接使用队列来检查唯一性
                await self.download_queue.put(magnet)
                added_count += 1
                print(f"磁链已加入队列: {magnet.name}")
            else:
                print(f"磁链已存在于队列中: {magnet.name}")

        print(f"加载了 {added_count} 个新磁链到队列中，共 {len(magnets)} 个磁链尝试加入。")

    async def process_magnet_queue(self):
        """
        监控模块监控完一个磁链后调用他，推送下一个新磁链（默认self.current_magnet应该为空）
        """
        # 监控结束后，先清除当前magnet和alist任务信息
        import datetime
        print(f"进入队列处理，当前时间: {datetime.datetime.now()}，当前任务: {self.current_magnet.name if self.current_magnet else ''}")

        if self.current_magnet:
            self.current_magnet = None
            await self.alist_service.reset_all_offline_tasks()

        print(f"进入队列处理检查，当前时间: {datetime.datetime.now()}，当前任务: {self.current_magnet.name if self.current_magnet else ''}")

        # 处理挂起队列的任务
        if not self.suspended_queue.empty():
            # 从挂起队列中获取一个磁链任务
            self.current_magnet = await self.suspended_queue.get()
            print(f"从挂起队列中恢复任务: {self.current_magnet.name}")
            await self.push_magnet_to_task(self.current_magnet)
        # 没有挂起的任务，处理正常下载队列
        elif not self.download_queue.empty():
            # 从下载队列中获取一个磁链任务
            self.current_magnet = await self.download_queue.get()
            print(f"开始处理任务: {self.current_magnet.name}")
            await self.push_magnet_to_task(self.current_magnet)

        print(f"结束队列处理，当前时间: {datetime.datetime.now()}，当前任务: {self.current_magnet.name if self.current_magnet else ''}")

    async def interrupt_and_retry_task(self, magnet: Magnet):
        """
        添加一个插队任务，中止当前正在运行的任务，并将当前任务挂起。
        """
        if not self.current_magnet:
            # 如果当前没有任务
            self.current_magnet = magnet
            print(f"置顶任务: {magnet.name}")
            await self.push_magnet_to_task(magnet)
        else:
            # 如果存在运行中的任务
            if self.current_magnet.id == magnet.id:
                # 和运行中的任务是同一个任务
                print(f"重试当前任务: {magnet.name}")
                await self.push_magnet_to_task(magnet)
            else:
                # 挂起当前运行任务
                await self.suspended_queue.put(self.current_magnet)
                self.current_magnet = magnet
                print(f"任务 {self.current_magnet.name} 被挂起，准备插队任务 {magnet.name}")
                await self.push_magnet_to_task(magnet)

    async def push_magnet_to_task(self, magnet: Magnet):
        """
        推送离线下载任务，推送监控。
        """
        try:
            await self.alist_service.retry_download_task(
                save_path=await self.alist_service.get_task_save_path(magnet), 
                urls=[magnet.magnet_link]
            )
            print(f"任务 {magnet.name} 推送成功")
            # 通知monitor开始监控
            await self.monitor.start_monitoring(magnet)
        except Exception as e:
            print(f"执行任务时出错: {e}")


