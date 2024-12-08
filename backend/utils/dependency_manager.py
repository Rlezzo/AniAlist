from enum import Enum
from backend.utils.logging_config import loguru_logger as logger

class DependencyKeys(Enum):
    ALIST_CLIENT = 'AlistClient' # alist通信客户端
    ALIST_TASK_MANAGER = 'AlistTaskManager' # alist任务操作通信管理
    DIRECTORY_MANAGER = 'DirectoryManager' # alist文件目录管理
    ALIST_SERVICE = 'AlistService' # alist综合任务管理
    MAGNET_QUEUE_MANAGER = 'MagnetQueueManager' # 下载队列管理
    MAGNET_MONITOR = 'MagnetMonitor' # 下载队列监控

class DependencyManager:
    def __init__(self):
        self.instances = {}

    def register(self, key, instance):
        """注册实例"""
        self.instances[key] = instance

    def get(self, key):
        """获取已注册的实例"""
        return self.instances.get(key)

    def inject(self, target, dependencies, inject_method):
        """
        动态注入依赖关系
        :param target: 注入目标的 key
        :param dependencies: 注入的依赖项字典
        :param inject_method: 注入方法
        """
        target_instance = self.get(target)
        dependency_instances = {name: self.get(key) for name, key in dependencies.items()}

        if target_instance and all(dependency_instances.values()):
            inject_method(**dependency_instances)
        else:
            missing_deps = [name for name, instance in dependency_instances.items() if not instance]
            if not target_instance:
                missing_deps.append(target)
            logger.error(f"依赖注入失败，缺失依赖：{', '.join(missing_deps)}")

    def inject_dependencies(self):
        """延迟注入依赖关系"""
        try:
            # AlistService 依赖注入
            self.inject(
                target=DependencyKeys.ALIST_SERVICE,
                dependencies={
                    'task_manager': DependencyKeys.ALIST_TASK_MANAGER,
                    'directory_manager': DependencyKeys.DIRECTORY_MANAGER
                },
                inject_method=lambda **kwargs: self.get(DependencyKeys.ALIST_SERVICE).set_dependencies(**kwargs)
            )

            # MagnetQueueManager 依赖注入
            self.inject(
                target=DependencyKeys.MAGNET_QUEUE_MANAGER,
                dependencies={
                    'alist_service': DependencyKeys.ALIST_SERVICE,
                    'monitor': DependencyKeys.MAGNET_MONITOR
                },
                inject_method=lambda **kwargs: self.get(DependencyKeys.MAGNET_QUEUE_MANAGER).set_dependencies(**kwargs)
            )

            # MagnetMonitor 依赖注入
            self.inject(
                target=DependencyKeys.MAGNET_MONITOR,
                dependencies={
                    'task_manager': DependencyKeys.ALIST_TASK_MANAGER,
                    'queue_manager': DependencyKeys.MAGNET_QUEUE_MANAGER
                },
                inject_method=lambda **kwargs: self.get(DependencyKeys.MAGNET_MONITOR).set_dependencies(**kwargs)
            )
        except Exception as e:
            logger.error(f"依赖注入过程中出现异常: {e}")

dependency_manager = DependencyManager()