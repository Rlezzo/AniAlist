<template>
    <div class="not-found">
      <h1>404 - 页面未找到</h1>
      <p>抱歉，您访问的页面不存在。</p>
    </div>
  </template>
  
  <script>
  export default {
    name: 'NotFound'
  };
  </script>
  
  <style scoped>
  .not-found {
    text-align: center;
    margin-top: 50px;
  }
  .not-found h1 {
    font-size: 48px;
    color: #ff6b6b;
  }
  .not-found p {
    font-size: 18px;
    color: #555;
  }
  </style>
  