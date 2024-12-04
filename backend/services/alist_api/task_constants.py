# task_constants.py
from enum import Enum

class TaskType(Enum):
    DOWNLOAD = "offline_download"
    TRANSFER = "offline_download_transfer"  # 表示上传任务

class TaskStatus(Enum):
    PENDING = 0
    RUNNING = 1
    SUCCEEDED = 2
    CANCELING = 3
    CANCELED = 4
    ERRORED = 5
    FAILING = 6
    FAILED = 7
    WAITING_RETRY = 8
    BEFORE_RETRY = 9
    UNKNOWN = 10

class ExecutionState(Enum):
    DONE = 'done'
    UNDONE = 'undone'

class DeletePolicy(Enum):
    DELETE_ON_UPLOAD_SUCCEED = "delete_on_upload_succeed"
    DELETE_ON_UPLOAD_FAILED = "delete_on_upload_failed"
    DELETE_NEVER = "delete_never"
    DELETE_ALWAYS = "delete_always"
    
class DownloaderType(Enum):
    ARIA = "aria2"
    QBIT = "qBittorrent"