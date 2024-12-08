<template>
  <div class="container">
    <header class="header">
      <h2>RSS Feeds 管理</h2>
      <div class="user-controls">
        <p class="welcome-message">Welcome，{{ username }}！</p>
        <button @click="logout" class="logout-button">退出登录</button>
      </div>
    </header>

    <div class="button-group">
      <button @click="$router.push({ name: 'LoginLogs' })" class="button-group-item view-logs-button">查看登录记录</button>
      <button @click="viewLogs" class="button-group-item system-logs-button">查看系统日志</button>
      <button @click="refreshAllRssFeeds" :disabled="refreshingAll" class="button-group-item refresh-all-button">
        更新所有勾选的 RSS 源
      </button>
    </div>

    <section class="feeds-section">
      <h1>RSS Feeds</h1>

      <!-- 筛选条件 -->
      <div class="filter-options">
        <label class="filter-label">
          <span>按更新时间筛选：</span>
          <input type="date" v-model="filterDate" @change="applyFilters" class="date-input" />
        </label>
        <label class="filter-label">
          <span>是否更新：</span>
          <select v-model="filterShouldUpdate" @change="applyFilters" class="select-input">
            <option value="">全部</option>
            <option value="true">是</option>
            <option value="false">否</option>
          </select>
        </label>
        <label class="filter-label">
          <span>名称搜索：</span>
          <input type="text" v-model="searchName" @input="applyFilters" class="text-input" placeholder="搜索名称" />
        </label>
      </div>

      <!-- RSS Feeds 列表表格显示 -->
      <table class="rss-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>URL</th>
            <th>上次更新</th>
            <th>是否更新</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="feed in paginatedFeeds" :key="feed.id">
            <td @click="viewMagnets(feed)" class="clickable">{{ feed.name }}</td>
            <td><a :href="feed.url" target="_blank">订阅地址</a></td>
            <td>{{ feed.last_updated ? feed.last_updated : '未更新' }}</td>
            <td>
              <input type="checkbox" v-model="feed.should_update" @change="updateShouldUpdate(feed)" />
            </td>
            <td>
              <div v-if="!feed.isEditing" class="actions">
                <button @click="editFeed(feed)" class="edit-button">编辑</button>
                <button @click="confirmDeleteFeed(feed.id)" class="delete-button">删除</button>
                <button @click="refreshSingleRssFeed(feed.id)" :disabled="refreshingFeedId === feed.id" class="refresh-button">
                  更新订阅
                </button>
              </div>
              <div v-else class="edit-form">
                <input type="text" v-model="feed.newName" placeholder="名称" class="edit-input" />
                <input type="text" v-model="feed.newUrl" placeholder="URL" class="edit-input" />
                <div class="edit-actions">
                  <button @click="saveFeedChanges(feed)" class="save-button">保存</button>
                  <button @click="cancelEdit(feed)" class="cancel-button">取消</button>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 分页控件 -->
      <div class="pagination">
        <button @click="prevPage" :disabled="currentPage === 1" class="pagination-button prev-page-button">
          上一页
        </button>
        <span class="pagination-info">第 {{ currentPage }} 页，共 {{ totalPages }} 页</span>
        <button @click="nextPage" :disabled="currentPage === totalPages" class="pagination-button next-page-button">
          下一页
        </button>
        <div class="page-input-container">
          <label>
            跳转到：
            <input type="number" v-model.number="pageInput" min="1" :max="totalPages" class="page-input" />
          </label>
          <button @click="jumpToPage" class="jump-button">跳转</button>
        </div>
      </div>

      <!-- 添加新的 RSS 源 -->
      <div class="add-rss-container">
        <h3>添加新的 RSS 源</h3>
        <div class="add-rss-form">
          <input v-model="newFeed.name" placeholder="名称" class="add-input" />
          <input v-model="newFeed.url" placeholder="URL" class="add-input" />
          <button @click="addFeed" :disabled="addingFeed" class="add-button">添加</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { fetchFeeds, createFeed, deleteFeed, patchRssFeed, renameRssFeed, refreshAllFeeds, refreshSingleFeed } from '../api/axios';

export default {
  data() {
    return {
      feeds: [],
      newFeed: {
        name: '',
        url: ''
      },
      username: '', // 用于显示用户名
      refreshingAll: false,
      refreshingFeedId: null,
      deletingFeedId: null,
      addingFeed: false,
      pageSize: 10,
      currentPage: 1,
      pageInput: 1,
      filterDate: '',
      filterShouldUpdate: 'true',
      searchName: '',
      logs: []
    };
  },
  computed: {
    paginatedFeeds() {
      const startIndex = (this.currentPage - 1) * this.pageSize;
      return this.filteredFeeds.slice(startIndex, startIndex + this.pageSize);
    },
    totalPages() {
      return Math.ceil(this.filteredFeeds.length / this.pageSize);
    },
    filteredFeeds() {
      return this.feeds.filter(feed => {
        let matchesDate = true;
        let matchesShouldUpdate = true;
        let matchesSearchName = true;

        if (this.filterDate) {
          matchesDate = this.isSameDay(feed.last_updated, this.filterDate);
        }
        if (this.filterShouldUpdate) {
          matchesShouldUpdate = feed.should_update.toString() === this.filterShouldUpdate;
        }
        if (this.searchName) {
          matchesSearchName = feed.name.toLowerCase().includes(this.searchName.toLowerCase());
        }

        return matchesDate && matchesShouldUpdate && matchesSearchName;
      });
    }
  },
  created() {
    this.setDefaultFilters();
    this.fetchFeeds();
    this.getUsername(); // 在创建时获取用户名
  },

  methods: {
    viewLogs() {
      this.$router.push({ name: 'LogViewer' });
    },
    viewMagnets(feed) {
      this.$router.push({ name: 'MagnetManager', params: { rssFeedId: feed.id } });
    },
    getUsername() {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          this.username = payload.username;
        } catch (error) {
          console.error('无法解析 JWT token:', error);
        }
      }
    },
    logout() {
      localStorage.removeItem('token'); // 清除 Token
      this.$router.push({ name: 'Login' }); // 重定向到登录页面
    },
    setDefaultFilters() {
      const today = new Date();
      const year = today.getFullYear();
      const month = (today.getMonth() + 1).toString().padStart(2, '0');
      const day = today.getDate().toString().padStart(2, '0');
      this.filterDate = `${year}-${month}-${day}`; // 设置今天的日期为默认筛选日期
      this.filterShouldUpdate = 'true';
    },
    isSameDay(dateString, filterDate) {
      if (!dateString) return false;

      const date = new Date(dateString);
      const formattedDate = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;

      return formattedDate === filterDate;
    },
    async fetchFeeds() {
      try {
        const response = await fetchFeeds();
        this.feeds = response.data.map(feed => ({
          ...feed,
          should_update: feed.should_update,
          last_updated: feed.last_updated ? this.formatDate(feed.last_updated) : null,
          isEditing: false,
          newName: feed.name,
          newUrl: feed.url
        }));
      } catch (error) {
        console.error('Error fetching RSS feeds:', error);
      }
    },
    formatDate(dateString) {
      const date = new Date(dateString);
      const year = date.getFullYear();
      const month = (date.getMonth() + 1).toString().padStart(2, '0');
      const day = date.getDate().toString().padStart(2, '0');
      const hours = date.getHours().toString().padStart(2, '0');
      const minutes = date.getMinutes().toString().padStart(2, '0');
      const seconds = date.getSeconds().toString().padStart(2, '0');
      return `${year}/${month}/${day} ${hours}:${minutes}:${seconds}`;
    },
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
      }
    },
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
      }
    },
    jumpToPage() {
      if (this.pageInput >= 1 && this.pageInput <= this.totalPages) {
        this.currentPage = this.pageInput;
      }
    },
    async addFeed() {
      if (this.newFeed.name && this.newFeed.url) {
        this.addingFeed = true;
        try {
          await createFeed(this.newFeed);
          this.fetchFeeds();
          this.newFeed.name = '';
          this.newFeed.url = '';
        } catch (error) {
          console.error('Error adding RSS feed:', error);
        } finally {
          this.addingFeed = false;
        }
      }
    },
    confirmDeleteFeed(id) {
      if (confirm('确定要删除该 RSS 源吗？此操作不可撤销。')) {
        this.deleteFeed(id);
      }
    },
    async deleteFeed(id) {
      this.deletingFeedId = id;
      try {
        await deleteFeed(id);
        this.fetchFeeds();
      } catch (error) {
        console.error('Error deleting RSS feed:', error);
      } finally {
        this.deletingFeedId = null;
      }
    },
    async refreshAllRssFeeds() {
      this.refreshingAll = true;
      const selectedFeeds = this.feeds.filter(feed => feed.should_update);
      try {
        await refreshAllFeeds(selectedFeeds.map(feed => feed.id));
        alert('勾选的 RSS 源已刷新，新任务已添加！');
        await this.fetchFeeds(); // 操作成功后重新获取 RSS Feeds 列表
      } catch (error) {
        console.error('Error refreshing all RSS feeds:', error);
      } finally {
        this.refreshingAll = false;
      }
    },
    async refreshSingleRssFeed(id) {
      this.refreshingFeedId = id;
      try {
        await refreshSingleFeed(id);
        alert(`RSS 源 ID ${id} 已刷新，新任务已添加！`);
        await this.fetchFeeds(); // 操作成功后重新获取 RSS Feeds 列表
      } catch (error) {
        console.error('Error refreshing RSS feed:', error);
      } finally {
        this.refreshingFeedId = null;
      }
    },
    async updateShouldUpdate(feed) {
      try {
        await patchRssFeed(feed.id, {
          should_update: feed.should_update
        });
        // 操作成功后重新获取 RSS Feeds 列表
        await this.fetchFeeds();
      } catch (error) {
        console.error('Error updating should_update status:', error);
      }
    },
    editFeed(feed) {
      feed.isEditing = true;
    },
    async saveFeedChanges(feed) {
      try {
        if (feed.name !== feed.newName) {
          // 只有在名称改变时才调用重命名 API
          await renameRssFeed(feed.id, {
            old_name: feed.name,
            new_name: feed.newName
          });
        }

        // 对于 URL 或其他字段的更新仍然使用原来的 PATCH 方法
        await patchRssFeed(feed.id, {
          url: feed.newUrl,
          should_update: feed.should_update
        });

        // 更新前端状态
        feed.name = feed.newName;
        feed.url = feed.newUrl;
        feed.isEditing = false;
      } catch (error) {
        console.error('Error saving feed changes:', error);
      }
    },
    cancelEdit(feed) {
      feed.isEditing = false;
      feed.newName = feed.name;
      feed.newUrl = feed.url;
    },
    applyFilters() {
      this.currentPage = 1; // 每次筛选重置为第一页
    }
  }
}
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
}

/* 头部样式 */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0f7fa; /* 使用淡蓝色边框替代灰色 */
}

.header h2 {
  color: #333;
  font-size: 1.8em;
}

.user-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.welcome-message {
  font-size: 1em;
  color: #555;
}

.logout-button {
  padding: 8px 20px;
  background-color: #dc3545;
  color: #fff;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
  font-size: 0.95em;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.logout-button:hover {
  background-color: #c82333;
  transform: translateY(-2px);
}

/* 按钮组 */
.button-group {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
  flex-wrap: wrap;
}

.button-group-item {
  padding: 10px 25px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.3s ease, transform 0.2s ease;
  color: #fff;
  background-color: #6c757d;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.button-group-item:hover {
  transform: translateY(-2px);
  background-color: #5a6268;
}

.button-group-item:disabled {
  background-color: #a0a0a0 !important; /* 使用较浅的灰色表示禁用状态 */
  cursor: not-allowed;
  opacity: 0.7;
}

/* 不同按钮颜色 */
.view-logs-button {
  background-color: #007bff;
}

.view-logs-button:hover {
  background-color: #0069d9;
}

.system-logs-button {
  background-color: #17a2b8;
}

.system-logs-button:hover {
  background-color: #138496;
}

.refresh-all-button {
  background-color: #28a745;
}

.refresh-all-button:hover {
  background-color: #218838;
}

/* RSS Feeds 部分 */
.feeds-section {
  background-color: #ffffff;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.feeds-section h1 {
  text-align: center;
  color: #333;
  margin-bottom: 25px;
  font-size: 1.6em;
}

/* 筛选选项 */
.filter-options {
  background-color: #ffffff; /* 使用白色背景替代浅灰色 */
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  gap: 30px;
  flex-wrap: wrap;
  margin-bottom: 25px;
}

.filter-label {
  display: flex;
  flex-direction: column;
  font-size: 0.95em;
  color: #555;
}

.filter-label span {
  margin-bottom: 8px;
  font-weight: 500;
}

.date-input,
.select-input,
.text-input {
  padding: 10px 14px;
  border-radius: 5px;
  border: 1px solid #ced4da;
  width: 220px;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
  font-size: 0.95em;
}

.date-input:focus,
.select-input:focus,
.text-input:focus {
  border-color: #007bff;
  box-shadow: 0 0 5px rgba(0, 123, 255, 0.3);
  outline: none;
}

/* 表格样式 */
.rss-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 25px;
}

.rss-table th,
.rss-table td {
  padding: 14px 20px;
  border: 1px solid #e0f7fa; /* 使用淡蓝色边框替代灰色 */
  text-align: left;
  font-size: 0.95em;
  color: #333333;
}

.rss-table th {
  background-color: #e0f7fa; /* 淡蓝色背景 */
  font-weight: 600;
}

.rss-table tbody tr:nth-child(even) {
  background-color: #ffffff; /* 使用白色背景 */
}

.clickable {
  cursor: pointer;
  color: #007bff;
  transition: color 0.3s ease;
}

.clickable:hover {
  color: #0056b3;
  text-decoration: underline;
}

.rss-table a {
  color: #007bff;
  text-decoration: none;
  transition: color 0.3s ease;
}

.rss-table a:hover {
  color: #0056b3;
  text-decoration: underline;
}

/* 操作按钮 */
.actions {
  display: flex;
  gap: 10px;
}

.edit-button,
.delete-button,
.refresh-button {
  padding: 6px 14px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.85em;
  transition: background-color 0.3s ease, transform 0.2s ease;
  color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.edit-button {
  background-color: #007bff;
}

.edit-button:hover {
  background-color: #0069d9;
  transform: translateY(-2px);
}

.delete-button {
  background-color: #dc3545;
}

.delete-button:hover {
  background-color: #c82333;
  transform: translateY(-2px);
}

.refresh-button {
  background-color: #28a745;
}

.refresh-button:hover {
  background-color: #218838;
  transform: translateY(-2px);
}

.refresh-button:disabled {
  background-color: #a0a0a0 !important; /* 使用较浅的灰色表示禁用状态 */
  cursor: not-allowed;
  opacity: 0.7;
}

/* 编辑表单 */
.edit-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.edit-input {
  padding: 10px 14px;
  border-radius: 5px;
  border: 1px solid #ced4da;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
  font-size: 0.95em;
}

.edit-input:focus {
  border-color: #007bff;
  box-shadow: 0 0 5px rgba(0, 123, 255, 0.3);
  outline: none;
}

.edit-actions {
  display: flex;
  gap: 10px;
}

.save-button,
.cancel-button {
  padding: 8px 16px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.85em;
  transition: background-color 0.3s ease, transform 0.2s ease;
  color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.save-button {
  background-color: #17a2b8;
}

.save-button:hover {
  background-color: #138496;
  transform: translateY(-2px);
}

.cancel-button {
  background-color: #ffc107;
  color: #333;
}

.cancel-button:hover {
  background-color: #e0a800;
  transform: translateY(-2px);
}

/* 分页控件 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 25px;
  margin-bottom: 25px;
  flex-wrap: wrap;
}

.pagination-button {
  padding: 8px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.3s ease, transform 0.2s ease;
  color: #fff;
  background-color: #6c757d;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.pagination-button:hover {
  transform: translateY(-2px);
  background-color: #5a6268;
}

.pagination-button:disabled {
  background-color: #a0a0a0 !important; /* 使用较浅的灰色表示禁用状态 */
  cursor: not-allowed;
  opacity: 0.7;
}

.prev-page-button {
  background-color: #28a745;
}

.prev-page-button:hover {
  background-color: #218838;
}

.next-page-button {
  background-color: #17a2b8;
}

.next-page-button:hover {
  background-color: #138496;
}

.pagination-info {
  font-size: 0.95em;
  color: #555;
}

.page-input-container {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-input {
  padding: 8px 12px;
  border-radius: 5px;
  border: 1px solid #ced4da;
  width: 80px;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
  font-size: 0.95em;
}

.page-input:focus {
  border-color: #007bff;
  box-shadow: 0 0 5px rgba(0, 123, 255, 0.3);
  outline: none;
}

.jump-button {
  padding: 8px 16px;
  background-color: #6c757d;
  color: #fff;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.jump-button:hover {
  background-color: #5a6268;
  transform: translateY(-2px);
}

/* 添加 RSS 部分 */
.add-rss-container {
  background-color: #ffffff; /* 使用白色背景替代浅灰色 */
  padding: 25px 20px;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  text-align: center;
}

.add-rss-container h3 {
  color: #333;
  margin-bottom: 20px;
  font-size: 1.4em;
}

.add-rss-form {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.add-input {
  padding: 10px 16px;
  border-radius: 5px;
  border: 1px solid #ced4da;
  width: 220px;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
  font-size: 0.95em;
}

.add-input:focus {
  border-color: #007bff;
  box-shadow: 0 0 5px rgba(0, 123, 255, 0.3);
  outline: none;
}

.add-button {
  padding: 10px 22px;
  background-color: #28a745;
  color: #fff;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.add-button:hover {
  background-color: #218838;
  transform: translateY(-2px);
}

.add-button:disabled {
  background-color: #a0a0a0 !important; /* 使用较浅的灰色表示禁用状态 */
  cursor: not-allowed;
  opacity: 0.7;
}

/* 全局按钮样式 */
button {
  font-family: inherit;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-options,
  .button-group,
  .add-rss-form,
  .actions,
  .edit-actions,
  .pagination {
    flex-direction: column;
    align-items: center;
  }

  .date-input,
  .select-input,
  .text-input,
  .add-input,
  .page-input {
    width: 100%;
    max-width: 300px;
  }

  .rss-table {
    font-size: 0.85em;
  }
}
</style>
