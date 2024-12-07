<template>
    <div class="container">
      <header class="header">
        <h2>登录记录</h2>
        <button class="primary-button return-button" @click="$router.push({ name: 'RSSFeeds' })">
          返回 RSS 管理
        </button>
      </header>
  
      <section class="logs-section">
        <!-- 登录记录表格显示 -->
        <table class="login-log-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>IP 地址</th>
              <th>用户名</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(log, index) in logs" :key="log.id" :class="getRowClass(index)">
              <td>{{ log.time }}</td>
              <td>{{ log.ip_address }}</td>
              <td>{{ log.username }}</td>
            </tr>
          </tbody>
        </table>
  
        <!-- 没有记录时的显示 -->
        <p v-if="logs.length === 0" class="no-logs-message">没有找到相关的登录记录。</p>
      </section>
    </div>
  </template>
  
  <script>
  import { getLoginLogs } from '../api/axios';
  
  export default {
    data() {
      return {
        logs: [] // 登录记录数据
      };
    },
    methods: {
      fetchLoginLogs() {
        getLoginLogs()
          .then(response => {
            this.logs = response.data.logs;
          })
          .catch(error => {
            console.error('无法获取登录记录:', error);
            alert('无法获取登录记录，请检查控制台日志。');
          });
      },
      getRowClass(index) {
        return index % 2 === 0 ? 'even-log-row' : 'odd-log-row';
      }
    },
    mounted() {
      this.fetchLoginLogs(); // 加载页面时获取数据
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
  
  .return-button {
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
  
  .return-button:hover {
    background-color: #0069d9;
    transform: translateY(-2px);
  }
  
  .return-button:disabled {
    background-color: #a0a0a0 !important; /* 使用较浅的灰色表示禁用状态 */
    cursor: not-allowed;
    opacity: 0.7;
  }
  
  /* 登录记录部分 */
  .logs-section {
    background-color: #ffffff;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  }
  
  /* 表格样式 */
  .login-log-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 25px;
  }
  
  .login-log-table th,
  .login-log-table td {
    padding: 14px 20px;
    border: 1px solid #e0f7fa; /* 使用淡蓝色边框替代灰色 */
    text-align: center;
    font-size: 0.95em;
    color: #333333;
  }
  
  .login-log-table th {
    background-color: #e0f7fa; /* 淡蓝色背景 */
    font-weight: 600;
  }
  
  .login-log-table tbody tr:hover {
    background-color: #c5c5c56d; /* 淡樱花色悬停效果 */
  }
  
  .login-log-table a {
    color: #007bff;
    text-decoration: none;
    transition: color 0.3s ease;
  }
  
  .login-log-table a:hover {
    color: #0056b3;
    text-decoration: underline;
  }
  
  /* 任务行样式 */
  .even-log-row {
    background-color: #ffffff; /* 奇数行白色背景 */
  }
  
  .odd-log-row {
    background-color: #f1f1f1; /* 偶数行淡灰色背景 */
  }
  
  /* 没有记录时的消息 */
  .no-logs-message {
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
  
    .login-log-table th,
    .login-log-table td {
      padding: 10px 12px;
      font-size: 0.85em;
    }
  
    .return-button {
      padding: 8px 16px;
      font-size: 0.9em;
    }
  }
  </style>
  