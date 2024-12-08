# alist_task.py
from typing import Optional
from dataclasses import dataclass
from .task_constants import TaskStatus
from backend.utils.logging_config import loguru_logger as logger

@dataclass
class AlistTask:
    tid: str
    action: str   # 动作类型，如 'download' 或 'upload'
    file_name: str  # 文件名
    target_path: str  # 目标路径
    status: TaskStatus
    progress: int
    error_msg: Optional[str] = None


    @classmethod
    def from_json(cls, json_data: dict):
        """从 JSON 数据创建 AlistTask 对象"""
        tid = json_data.get("id")
        description = json_data.get("name", "No description")
        state_value = json_data.get("state")
        progress = json_data.get("progress", 0)
        error_str = json_data.get("error")

        # 解析动作类型、文件名和目标路径
        action, file_name, target_path = cls.parse_description(description)

        # 将状态值转换为 TaskStatus 枚举值
        try:
            # 判断状态是否是整数
            if isinstance(state_value, int):
                status = TaskStatus(state_value)
            else:
                raise ValueError("Unexpected state value type")
        except ValueError:
            logger.warning(f"Unknown task status '{state_value}' for task {tid}")
            status = TaskStatus.UNKNOWN

        return cls(
            tid=tid,
            action=action,
            file_name=file_name, # 磁链部分
            target_path=target_path,
            status=status,
            progress=progress,
            error_msg=error_str
        )

    @staticmethod
    def parse_description(description: str):
        """按照给定逻辑解析 description 字段，将其分解为动作类型、文件名和目标路径"""
        # 1. 找到第一个空格，前面的部分是 action
        first_space_index = description.find(" ")
        if first_space_index == -1:
            # 如果没有找到空格，直接返回 'unknown'
            return "unknown", "unknown", "unknown"

        action = description[:first_space_index]  # 第一个空格前是 action

        # 2. 从第一个空格之后查找 " to "，作为分隔符
        rest = description[first_space_index + 1:]
        to_index = rest.find(" to ")

        if to_index == -1:
            # 如果没有找到 " to "，返回剩余部分作为文件名，路径未知
            file_name = rest
            return action, file_name, "unknown"

        # 3. 分割出文件名和目标路径
        file_name = rest[:to_index]
        target_path = rest[to_index + 4:]  # " to " 后面的部分是目标路径

        # 4. 去掉路径中的 `[]` 或 `()` 符号
        target_path = target_path.strip("[]()")

        return action, file_name, target_path
    
    def update_status(self, status: TaskStatus):
        """更新任务状态"""
        self.status = status

    def __repr__(self) -> str:
        # 设定文件名和路径的长度限制
        max_length = 20

        # 文件名和路径超过限制时截断并加上省略号
        file_name_display = (self.file_name[:max_length] + '...') if len(self.file_name) > max_length else self.file_name
        target_path_display = (self.target_path[:max_length] + '...') if len(self.target_path) > max_length else self.target_path

        # 构建并返回字符串
        return (
            f"<Task_ID: {self.tid}, "
            f"Status: {self.status.name}, "
            f"Progress: {self.progress}%, "
            f"Action: {self.action}, "
            f"File_Name: {file_name_display}, "
            f"Target_Path: {target_path_display}>"
        )
