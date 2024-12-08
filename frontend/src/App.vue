<template>
  <div id="app">
    <header v-if="!isLoginOrNotFound">
      <h1>欢迎使用 RSS 管理系统</h1>
    </header>
    <router-view></router-view> <!-- 根据路由展示页面 -->
  </div>
</template>

<script>
export default {
  name: 'App',
  computed: {
    isLoginOrNotFound() {
      // 根据路由名称判断是否为登录页或 404 页
      return this.$route.name === 'Login' || this.$route.name === 'NotFound';
    }
  }
};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}

.primary-button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.3s ease;
  margin: 5px;
  color: #fff;
  font-weight: bold;
  background-color: #007bff; /* 蓝色 */
}

.primary-button:hover {
  background-color: #0069d9; /* 深蓝色 */
}

button:disabled {
  background-color: #e0e0e0;
  cursor: not-allowed;
  opacity: 0.6;
}

/* 鼠标悬停效果 - 提升视觉反馈 */
button:hover {
  transform: translateY(-3px);
}
</style>
