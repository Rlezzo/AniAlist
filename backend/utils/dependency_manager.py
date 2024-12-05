class DependencyManager:
    def __init__(self):
        # 用来保存所有实例
        self.instances = {}

    def register(self, name, instance):
        """注册组件实例"""
        self.instances[name] = instance

    def get(self, name):
        """获取已注册的组件实例"""
        return self.instances.get(name)

    def inject_dependencies(self):
        """延迟注入依赖关系"""
        # 例如，MagnetQueueManager 需要 MagnetMonitor 的引用
        queue_manager = self.get('MagnetQueueManager')
        monitor = self.get('MagnetMonitor')
        
        if queue_manager and monitor:
            queue_manager.set_monitor(monitor)
            print("已成功注入 MagnetMonitor 到 MagnetQueueManager")

        # 同时也可以让 monitor 知道 queue_manager
        if monitor and queue_manager:
            monitor.set_queue_manager(queue_manager)
            print("已成功注入 MagnetQueueManager 到 MagnetMonitor")
