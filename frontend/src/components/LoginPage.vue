<template>
  <div class="login-container">
    <h2>登录系统</h2>
    <div class="login-form">
      <input v-model="username" type="text" placeholder="请输入用户名" class="login-input" />
      <input v-model="password" type="password" placeholder="请输入密码" class="login-input" />
      <button @click="login" class="login-button">登录</button>
      <div v-if="loginError" class="error-message">{{ loginError }}</div>
    </div>
  </div>
</template>

<script>
import { loginUser } from '../api/axios';

export default {
  data() {
    return {
      username: '',
      password: '',
      loginError: ''
    };
  },
  methods: {
    async login() {
      try {
        const response = await loginUser(this.username, this.password);
        const token = response.token; // 修改为直接从 response 中获取
        localStorage.setItem('token', token); // 保存 Token
        this.$router.push({ name: 'RSSFeeds' }); // 登录成功后跳转到 RSSFeeds 主页
      } catch (error) {
        this.loginError = '用户名或密码错误，请重试';
      }
    }
  }
};
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 100px auto;
  padding: 20px;
  text-align: center;
  border: 1px solid #ccc;
  border-radius: 10px;
  background-color: #f9f9f9;
}

.login-input {
  width: 80%;
  padding: 10px;
  margin-bottom: 20px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.login-button {
  padding: 10px 20px;
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.login-button:hover {
  background-color: #218838;
}

.error-message {
  color: #dc3545;
  margin-top: 10px;
}
</style>