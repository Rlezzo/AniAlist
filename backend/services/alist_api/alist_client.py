# AlistClient.py
import aiohttp
import urllib.parse
from dataclasses import dataclass
from .task_constants import TaskType, ExecutionState

@dataclass
class AlistClient:
    # alist地址
    base_url: str
    # 令牌
    token: str

    def __post_init__(self):
        # 初始化 HTTP 请求头，包含认证信息
        self.headers = {
            "User-Agent": "Alist-Mikanirss/v0.0",
            "Content-Type": "application/json",
            "Authorization": self.token,
        }

    async def _request(self, method: str, endpoint: str, **kwargs):
        """基础请求方法，用于发送 HTTP 请求"""
        url = urllib.parse.urljoin(self.base_url, endpoint)
        async with aiohttp.ClientSession(trust_env=True) as session:
            # 使用对应的 HTTP 方法发送请求
            async with session.request(method, url, headers=self.headers, **kwargs) as response:
                # 检查响应状态
                response.raise_for_status()
                json_data = await response.json()
                
                # 如果响应中包含错误代码，抛出异常
                if json_data.get("code", 200) != 200:
                    raise aiohttp.ClientResponseError(
                        response.request_info,
                        response.history,
                        status=json_data["code"],
                        message=json_data.get("message", "Unknown error"),
                        headers=response.headers,
                    )
                return json_data.get("data")

    async def get(self, endpoint: str, **kwargs):
        """发送 GET 请求"""
        return await self._request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs):
        """发送 POST 请求"""
        return await self._request("POST", endpoint, **kwargs)

    async def put(self, endpoint: str, **kwargs):
        """发送 PUT 请求"""
        return await self._request("PUT", endpoint, **kwargs)

    async def get_alist_version(self) -> str:
        """获取 Alist 服务端版本信息"""
        data = await self.get("/api/public/settings")
        return data.get("version", "unknown").lstrip("v")

    async def list_tasks(self, task_type: TaskType, status: ExecutionState = ExecutionState.UNDONE):
        """调用 Alist 的 API 来列出指定类型和状态的任务"""
        endpoint = f"/api/admin/task/{task_type.value}/{status.value}"
        return await self.get(endpoint)
    
    async def add_offline_download_task(self, save_path: str, urls: list, delete_policy: str, downloader_tool: str):
        """封装添加离线下载任务的请求"""
        endpoint = "/api/fs/add_offline_download"
        body = {
            "delete_policy": delete_policy,
            "path": save_path,
            "urls": urls,
            "tool": downloader_tool
        }
        return await self.post(endpoint, json=body)

    async def cancel_task(self, task_type: TaskType, task_id: str):
        """封装取消任务的 API 请求"""
        endpoint = f"/api/admin/task/{task_type.value}/cancel?tid={task_id}"
        await self.post(endpoint)

    async def clear_done_tasks(self, task_type: TaskType):
        """封装清除已完成任务的 API 请求"""
        endpoint = f"/api/admin/task/{task_type.value}/clear_done"
        await self.post(endpoint)

    async def check_path_exists(self, path: str) -> bool:
        """封装检查路径是否存在的 API 请求"""
        endpoint = "/api/fs/dirs"
        body = {"path": path, "password": "", "force_root": False}
        await self.post(endpoint, json=body)

    async def create_directory(self, path: str) -> bool:
        """封装创建目录的 API 请求"""
        endpoint = "/api/fs/mkdir"
        body = {"path": path}
        await self.post(endpoint, json=body)

    async def rename_directory(self, current_path: str, new_name: str) -> bool:
        """封装重命名目录的 API 请求"""
        endpoint = "/api/fs/rename"
        body = {
            "name": new_name,
            "path": current_path
        }
        await self.post(endpoint, json=body)

    async def delete_directory(self, dir_path: str, names: list) -> bool:
        """封装删除目录内容的 API 请求"""
        endpoint = "/api/fs/remove"
        body = {
            "dir": dir_path,
            "names": names
        }
        await self.post(endpoint, json=body)