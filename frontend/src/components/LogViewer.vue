<template>
  <div class="container">
    <header class="header">
      <h2>系统日志查看器</h2>
      <button @click="$router.push({ name: 'RSSFeeds' })" class="primary-button back-button">
        <i class="fas fa-arrow-left"></i> 返回 RSS 管理
      </button>
    </header>

    <section class="log-viewer-section">
      <div class="filter-container">
        <div class="filter-item">
          <label for="log-level">日志级别：</label>
          <select id="log-level" v-model="selectedLevel" class="select-input">
            <option value="ALL">所有</option>
            <option value="DEBUG">DEBUG</option>
            <option value="INFO">INFO</option>
            <option value="WARNING">WARNING</option>
            <option value="ERROR">ERROR</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
        </div>

        <div class="filter-item">
          <label for="start-date">开始日期：</label>
          <input type="date" id="start-date" v-model="startDate" class="date-input" />
        </div>

        <div class="filter-item">
          <label for="end-date">结束日期：</label>
          <input type="date" id="end-date" v-model="endDate" class="date-input" />
        </div>

        <div class="filter-item checkbox-filter">
          <label for="include-details">显示详细信息：</label>
          <input type="checkbox" id="include-details" v-model="includeDetails" class="checkbox-input" />
        </div>

        <div class="filter-item filter-button">
          <button class="primary-button" @click="fetchLogs(1)">筛选日志</button>
        </div>
      </div>

      <div v-if="isLoading" class="loading-spinner">
        <i class="fas fa-spinner fa-spin"></i> 正在加载日志...
      </div>

      <div v-if="!isLoading && logs.length === 0" class="no-logs-message">没有找到符合条件的日志</div>
      <div v-else class="logs-container">
        <div
          v-for="(line, index) in logs"
          :key="index"
          :class="getLogLineClass(line)"
          class="log-line"
        >
          <span class="log-time">{{ extractLogTime(line) }}</span>
          <span class="log-level">{{ extractLogLevel(line) }}</span>
          <span class="log-message">{{ extractLogMessage(line) }}</span>
        </div>
      </div>

      <div v-if="totalPages > 1" class="pagination">
        <button class="secondary-button" @click="changePage(page - 1)" :disabled="page <= 1">
          上一页
        </button>
        <span class="pagination-info">第 {{ page }} 页，共 {{ totalPages }} 页</span>
        <button class="secondary-button" @click="changePage(page + 1)" :disabled="page >= totalPages">
          下一页
        </button>
      </div>
    </section>
  </div>
</template>

<script>
import { fetchLogs } from '../api/axios'; // 引入封装的日志 API
import '@fortawesome/fontawesome-free/css/all.css'; // 引入 Font Awesome 图标库

export default {
  data() {
    return {
      logs: [],
      selectedLevel: 'ALL',    // 默认选择所有日志
      startDate: '',           // 起始日期
      endDate: '',             // 结束日期
      includeDetails: false,   // 默认显示详细信息
      page: 1,                 // 当前页码
      pageSize: 20,            // 每页大小
      totalPages: 1,           // 总页数
      isLoading: false,        // 加载状态
    };
  },
  methods: {
    fetchLogs(page) {
      this.page = page; // 设置当前页
      this.isLoading = true; // 开始加载
      fetchLogs(this.selectedLevel, this.startDate, this.endDate, this.includeDetails, this.page, this.pageSize)
        .then(response => {
          if (response.data.logs && response.data.logs.length > 0) {
            this.logs = response.data.logs;
            this.totalPages = response.data.total_pages;
          } else {
            this.logs = [];
            this.totalPages = 1;
          }
        })
        .catch(error => {
          console.error('无法获取日志:', error);
          alert('获取日志时发生错误，请检查控制台日志。');
        })
        .finally(() => {
          this.isLoading = false; // 结束加载
        });
    },
    changePage(newPage) {
      if (newPage > 0 && newPage <= this.totalPages) {
        this.fetchLogs(newPage);
      }
    },
    getLogLineClass(line) {
      if (line.includes('| DEBUG |')) {
        return 'log-line-debug';
      } else if (line.includes('| INFO |')) {
        return 'log-line-info';
      } else if (line.includes('| WARNING |')) {
        return 'log-line-warning';
      } else if (line.includes('| ERROR |')) {
        return 'log-line-error';
      } else if (line.includes('| CRITICAL |')) {
        return 'log-line-critical';
      } else {
        return 'log-line';
      }
    },
    extractLogTime(line) {
      return line.split(' | ')[0];
    },
    extractLogLevel(line) {
      return line.split(' | ')[1];
    },
    extractLogMessage(line) {
      return line.split(' | ').slice(2).join(' | ');
    }
  },
  mounted() {
    this.fetchLogs(this.page); // 组件挂载时获取第一页日志
  }
};
</script>

<style scoped>
/* 基础样式 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #ffffff; /* 纯白色背景 */
  min-height: 100vh;
  box-sizing: border-box;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
}

/* 头部样式 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0f7fa; /* 使用淡蓝色边框替代灰色 */
}

.header h2 {
  color: #333;
  font-size: 1.8em;
  margin: 0;
}

.back-button {
  background-color: #007bff;
  color: #fff;
  border: none;
  padding: 10px 22px;
  font-size: 0.95em;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.back-button:hover {
  background-color: #0069d9;
  transform: translateY(-2px);
}

.back-button:disabled {
  background-color: #a0a0a0 !important; /* 使用较浅的灰色表示禁用状态 */
  cursor: not-allowed;
  opacity: 0.7;
}

/* 日志查看器部分 */
.log-viewer-section {
  background-color: #ffffff;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

/* 筛选条件的容器 */
.filter-container {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: flex-start;
  margin-bottom: 25px;
  align-items: center; /* 确保所有筛选项垂直居中对齐 */
}

/* 筛选项的样式 */
.filter-item {
  flex: 1 1 200px;
  min-width: 150px;
  display: flex;
  flex-direction: column;
  font-size: 0.95em;
  color: #555;
}

.filter-item label {
  margin-bottom: 8px;
  font-weight: 500;
}

/* 覆盖checkbox-filter的布局并添加偏移和下移 */
.filter-item.checkbox-filter {
  flex-direction: row;
  align-items: center;
  white-space: nowrap; /* 防止内容换行 */
  margin-left: 20px;   /* 向右偏移 */
  margin-top: 10px;    /* 向下移动 */
}

/* 增加标签和勾选框之间的间距 */
.filter-item.checkbox-filter label {
  margin-bottom: 0;
  margin-right: 10px; /* 增加标签和勾选框之间的间距 */
  white-space: nowrap; /* 防止标签文本换行 */
}

/* 确保checkbox-input的宽度适应内容 */
.checkbox-input {
  width: auto;
  flex-shrink: 0; /* 防止勾选框被压缩 */
}

/* 筛选按钮样式 */
.filter-button {
  display: flex;
  align-items: flex-end;
}

/* 按钮样式 */
.primary-button {
  background-color: #007bff;
  color: #fff;
  border: none;
  padding: 10px 22px;
  font-size: 0.95em;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.primary-button:hover {
  background-color: #0069d9;
  transform: translateY(-2px);
}

.primary-button:disabled {
  background-color: #a0a0a0 !important; /* 使用较浅的灰色表示禁用状态 */
  cursor: not-allowed;
  opacity: 0.7;
}

.secondary-button {
  background-color: #6c757d;
  color: #fff;
  border: none;
  padding: 10px 20px;
  font-size: 0.95em;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.secondary-button:hover {
  background-color: #5a6268;
  transform: translateY(-2px);
}

.secondary-button:disabled {
  background-color: #a0a0a0 !important; /* 使用较浅的灰色表示禁用状态 */
  cursor: not-allowed;
  opacity: 0.7;
}

/* 日志行的样式 */
.logs-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.log-line {
  font-family: monospace;
  white-space: pre-wrap;  /* 自动换行 */
  word-wrap: break-word;  /* 强制长词换行 */
  text-align: left;
  margin: 5px 0;
  padding: 10px;
  border-radius: 5px;
  max-width: 100%;  /* 防止内容超出背景区域 */
  font-size: 1.1em;  /* 增大日志文本的字体大小 */
}

.log-line-debug {
  background-color: #e7f3fe;
  border-left: 4px solid #007bff;
}

.log-line-info {
  background-color: #e9f7ef;
  border-left: 4px solid #28a745;
}

.log-line-warning {
  background-color: #fff3cd;
  border-left: 4px solid #ffc107;
}

.log-line-error {
  background-color: #f8d7da;
  border-left: 4px solid #dc3545;
}

.log-line-critical {
  background-color: #f5c6cb;
  border-left: 4px solid #bd2130;
}

/* 区分日志的各个部分 */
.log-time {
  color: #6c757d; /* 灰色，突出时间部分 */
  margin-right: 10px;
}

.log-level {
  font-weight: bold;
  margin-right: 10px;
}

.log-message {
  color: #333; /* 默认深色用于消息内容 */
}

.no-logs-message {
  text-align: center;
  font-size: 1em;
  color: #6c757d;
  margin-top: 20px;
}

/* 加载状态样式 */
.loading-spinner {
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.2em;
  color: #007bff;
  margin-top: 20px;
}

/* 分页组件的样式 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 25px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.pagination-info {
  font-size: 0.95em;
  color: #555;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-container {
    flex-direction: column; /* 改为垂直排列以适应小屏幕 */
    align-items: flex-start;
    gap: 15px;
  }

  .filter-item {
    flex: 1 1 100%;
    min-width: 100%;
  }

  /* 保持checkbox-filter为行内布局，并调整偏移和下移 */
  .filter-item.checkbox-filter {
    flex-direction: row;
    align-items: center;
    margin-left: 0;      /* 小屏幕上取消向右偏移 */
    margin-top: 10px;    /* 保持向下移动 */
    width: auto;
  }

  .filter-item.checkbox-filter label,
  .filter-item.checkbox-filter .checkbox-input {
    width: auto;
    white-space: nowrap; /* 防止标签文本换行 */
  }

  .log-line {
    font-size: 1em; /* 适当增大 */
  }

  .primary-button,
  .secondary-button {
    width: 100%;
    max-width: 300px;
  }

  .log-time,
  .log-level,
  .log-message {
    display: block;
    margin-bottom: 5px;
  }
}
</style>
