import axios from 'axios';

// 创建一个 axios 实例
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:5000/api', // 后端 API 的基础 URL
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true // 允许发送跨域请求时携带凭据
});

// 获取所有 RSS 订阅
export const fetchFeeds = () => {
  return apiClient.get('/rss');
};

// 创建新的 RSS 订阅
export const createFeed = (feedData) => {
  return apiClient.post('/rss', feedData);
};

export const deleteFeed = (rssId) => {
  return apiClient.delete(`/rss/${rssId}`);
};

// put更新某个 RSS 订阅的基本信息
export const updateFeed = (rssId, updateData) => {
  return apiClient.put(`/rss/${rssId}`, updateData);
};

// patch更新某个 RSS 订阅的单项信息
export const patchRssFeed = (rssId, updateData) => {
  return apiClient.patch(`/rss/${rssId}`, updateData);
};

// 重命名 RSS 源的名称和网盘文件夹
export const renameRssFeed = (rssId, updateData) => {
  return apiClient.patch(`/rss/${rssId}/rename`, updateData);
};

// 刷新单个 RSS 订阅
export const refreshSingleFeed = (rssId) => {
  return apiClient.post(`/rss/${rssId}/refresh`);
};

// 刷新多个 RSS 订阅
export const refreshAllFeeds = (rssIdList) => {
  const requests = rssIdList.map((rssId) => {
    return refreshSingleFeed(rssId);
  });
  return Promise.all(requests);
};

// 增加获取单个 RSS 订阅的方法（可选）
export const fetchRSSFeedById = (rssId) => {
  return apiClient.get(`/rss/${rssId}`);
};

// 封装 Magnet API 调用
export const fetchMagnets = () => {
  return apiClient.get('/magnets');
};

export const deleteMagnet = (magnetId) => {
  return apiClient.delete(`/magnets/${magnetId}`);
};

// 获取特定 RSS 源的所有任务
export const fetchMagnetsByRss = (rssId) => {
  return apiClient.get(`/magnets/rss/${rssId}`);
};

// 重试任务 - 使用路径参数传递 magnetId
export const retryMagnet = (magnetId) => {
  return apiClient.post(`/magnets/${magnetId}/retry`);
};

// 获取日志数据
export const fetchLogs = (level, startDate, endDate, includeDetails, page, pageSize) => {
  return apiClient.get('/logs', {
    params: {
      level: level || 'ALL',
      start_date: startDate || '',
      end_date: endDate || '',
      include_details: includeDetails,
      page: page || 1,
      page_size: pageSize || 20,
    }
  });
};

// 用户登录请求
export const loginUser = async (username, password) => {
  try {
    const response = await apiClient.post('/auth/login', { username, password });
    const token = response.data.token;
    if (token) {
      localStorage.setItem('token', token); // 存储 Token 到 localStorage
    }
    return response.data;
  } catch (error) {
    console.error('登录失败:', error.response?.data?.message || error.message);
    throw error;
  }
};

// 添加请求拦截器，确保所有请求都附带 Token
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token'); // 从 localStorage 获取 token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`; // 附加 Bearer Token
  }
  return config;
}, error => {
  console.error('请求拦截器错误:', error);
  return Promise.reject(error);
});


apiClient.interceptors.response.use(
  response => response, // 对成功响应直接返回
  async error => {
    if (error.response?.status === 401 && error.response?.data?.message === 'Token has expired!') {
      try {
        // 调用刷新接口
        const refreshResponse = await apiClient.post('/auth/refresh');
        const newToken = refreshResponse.data.token;

        if (newToken) {
          localStorage.setItem('token', newToken); // 更新 Token
          error.config.headers.Authorization = `Bearer ${newToken}`; // 设置新 Token
          return apiClient.request(error.config); // 重试原始请求
        }
      } catch {
        // 清除无效 Token 并重定向到登录页面
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error); // 其他错误继续抛出
  }
);

export const getLoginLogs = () => {
  return apiClient.get('/login_logs');
};

// 导出 axios 实例以供组件直接使用
export default apiClient;