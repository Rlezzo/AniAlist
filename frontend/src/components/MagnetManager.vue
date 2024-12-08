<template>
  <div class="container">
    <header class="header">
      <h2 v-if="rssFeed">任务管理 - {{ rssFeed.name }} (共{{ totalEpisodes }}集)</h2>
      <h2 v-else>正在加载任务管理...</h2>
      <button @click="$router.push({ name: 'RSSFeeds' })" class="primary-button back-button">返回 RSS 管理</button>
    </header>

    <section class="tasks-section">
      <!-- 任务列表表格显示 -->
      <table class="magnet-table">
        <thead>
          <tr>
            <th>序号</th>
            <th>标题</th>
            <th>状态</th>
            <th>磁力链接</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(magnet, index) in sortedMagnets" :key="magnet.id" :class="{
            'incomplete-task-row': !magnet.status,
            'completed-task-row': magnet.status
          }">
            <td>{{ index + 1 }}</td> <!-- 递增序号 -->
            <td v-html="highlightEpisodeNumber(magnet.title)"></td> <!-- 突出显示集数 -->
            <td>{{ magnet.status ? '已上传' : '未上传' }}</td> <!-- 状态 -->
            <td><a :href="magnet.magnet_link" target="_blank">查看链接</a></td>
            <td>
              <button @click="retryMagnet(magnet)" :disabled="retryingMagnetId === magnet.id"
                class="primary-button retry-button">
                重试
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 没有任务时的显示 -->
      <p v-if="sortedMagnets.length === 0" class="no-tasks-message">没有找到相关的任务。</p>
    </section>
  </div>
</template>

<script>
import { fetchMagnetsByRss, retryMagnet as retryMagnetAPI, fetchRSSFeedById } from '../api/axios';

export default {
  props: {
    rssFeedId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      rssFeed: null, // 保存当前 RSS 详情
      magnets: [],
      retryingMagnetId: null,
      patterns: [
        /\[(\d{2})\]/,               // 匹配方括号包围的两位数，如 [01], [10]
        /第\s*(\d{2})\s*集/,          // 匹配“第10集”, “第00集”
        /第\s*(\d{2})\s*話/,          // 匹配“第10話”, “第00話” (繁体)
        /\s+(\d{2})\s+/,             // 匹配两边有空格的两位数，如 " 87 "
        /\b(\d{2})\b/,               // 匹配独立的两位数，避免匹配720p等
        // 未来添加更多模式...
      ],
    };
  },
  computed: {
    // 计算属性：对 magnets 进行排序
    sortedMagnets() {
      return this.magnets.slice().sort((a, b) => {
        const aEpisode = this.extractEpisodeNumber(a.title);
        const bEpisode = this.extractEpisodeNumber(b.title);

        if (aEpisode !== null && bEpisode !== null) {
          return bEpisode - aEpisode; // 按集数降序排序
        } else if (aEpisode !== null) {
          return -1; // a 有集数，b 没有集数
        } else if (bEpisode !== null) {
          return 1; // b 有集数，a 没有集数
        } else {
          return b.id - a.id; // 都没有集数，按 id 降序
        }
      });
    },
    // 计算属性：总集数
    totalEpisodes() {
      return this.sortedMagnets.length;
    },
  },
  created() {
    this.fetchRssFeedDetails();
  },
  methods: {
    // 获取特定 RSS 的详细信息
    async fetchRssFeedDetails() {
      try {
        const response = await fetchRSSFeedById(this.rssFeedId);
        this.rssFeed = response.data;
        this.fetchMagnets(); // 获取到 RSS 详情后再获取对应的磁力链接任务
      } catch (error) {
        console.error('Error fetching RSS feed details:', error);
        alert('无法加载 RSS Feed 详情，请检查控制台日志。');
      }
    },
    // 获取选中 RSS 的任务
    async fetchMagnets() {
      try {
        const response = await fetchMagnetsByRss(this.rssFeed.id);
        this.magnets = response.data;
      } catch (error) {
        console.error('Error fetching magnets:', error);
        alert('获取任务时发生错误，请检查控制台日志。');
      }
    },
    // 重试任务
    async retryMagnet(magnet) {
      this.retryingMagnetId = magnet.id; // 标记正在重试的任务 ID
      try {
        // 直接传递 magnet.id 给后端
        await retryMagnetAPI(magnet.id);
        alert(`任务 ID ${magnet.id} 重试成功！`);
        this.fetchMagnets(); // 刷新任务列表，获取最新的任务状态
      } catch (error) {
        console.error('Error retrying magnet:', error);
        alert('重试任务时发生错误，请检查控制台日志');
      } finally {
        this.retryingMagnetId = null; // 解除任务重试标记
      }
    },
    // 提取标题中的集数，返回数字或 null
    extractEpisodeNumber(title) {
      for (const pattern of this.patterns) {
        const match = title.match(pattern);
        if (match && match[1]) {
          return parseInt(match[1], 10);
        }
      }
      // 如果无法提取集数，记录日志
      console.warn(`无法提取集数的标题: ${title}`);
      return null;
    },
    // 突出显示标题中的集数
    highlightEpisodeNumber(title) {
      let highlightedTitle = title;
      this.patterns.forEach(pattern => {
        highlightedTitle = highlightedTitle.replace(pattern, match => `<strong class="highlight">${match}</strong>`);
      });
      return highlightedTitle;
    },
  },
};
</script>

<style scoped>
/* 基础样式 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #ffffff;
  /* 纯白色背景 */
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
  border-bottom: 2px solid #e0f7fa;
  /* 使用淡蓝色边框替代灰色 */
}

.header h2 {
  color: #333;
  font-size: 1.8em;
  margin: 0;
}

.back-button {
  padding: 10px 22px;
  background-color: #007bff;
  color: #fff;
  border: none;
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
  background-color: #a0a0a0 !important;
  /* 使用较浅的灰色表示禁用状态 */
  cursor: not-allowed;
  opacity: 0.7;
}

/* 任务部分 */
.tasks-section {
  background-color: #ffffff;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

/* 表格样式 */
.magnet-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 25px;
}

.magnet-table th,
.magnet-table td {
  padding: 14px 20px;
  border: 1px solid #e0f7fa;
  /* 使用淡蓝色边框替代灰色 */
  text-align: left;
  font-size: 0.95em;
  color: #333333;
}

.magnet-table th {
  background-color: #e0f7fa;
  /* 淡蓝色背景 */
  font-weight: 600;
}

.magnet-table tbody tr:hover {
  background-color: #ffffff;
  /* 淡樱花色悬停效果 */
}

.magnet-table a {
  color: #007bff;
  text-decoration: none;
  transition: color 0.3s ease;
}

.magnet-table a:hover {
  color: #0056b3;
  text-decoration: underline;
}

/* 可点击标题中的集数高亮 */
.highlight {
  color: #42b983;
  font-weight: bold;
}

/* 操作按钮 */
.primary-button {
  padding: 8px 20px;
  background-color: #007bff;
  color: #fff;
  border: none;
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
  background-color: #a0a0a0 !important;
  /* 使用较浅的灰色表示禁用状态 */
  cursor: not-allowed;
  opacity: 0.7;
}

.retry-button {
  background-color: #28a745;
}

.retry-button:hover {
  background-color: #218838;
}

.retry-button:disabled {
  background-color: #a0a0a0 !important;
  /* 使用较浅的灰色表示禁用状态 */
  cursor: not-allowed;
  opacity: 0.7;
}

/* 任务行样式 */
.incomplete-task-row {
  background-color: rgba(255, 255, 204, 0.6);
  /* 浅黄色背景，表示未完成的任务 */
}

.completed-task-row {
  background-color: rgba(224, 255, 224, 0.6);
  /* 浅绿色背景，表示已完成的任务 */
}

/* 没有任务时的消息 */
.no-tasks-message {
  text-align: center;
  color: #555;
  font-size: 1em;
  margin-top: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
  }

  .magnet-table th,
  .magnet-table td {
    padding: 10px 12px;
    font-size: 0.85em;
  }

  .primary-button {
    padding: 8px 16px;
    font-size: 0.9em;
  }

  .highlight {
    display: block;
  }
}
</style>
