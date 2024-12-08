import { createRouter, createWebHistory } from 'vue-router';
import LoginPage from './components/LoginPage.vue';
import RSSFeeds from './components/RSSFeeds.vue';
import MagnetManager from './components/MagnetManager.vue';
import LogViewer from './components/LogViewer.vue';
import NotFound from './components/NotFound.vue'; // 引入 404 页面组件
import LoginLogs from './components/LoginLogs.vue'; // 登录记录页面组件

const routes = [
  {
    path: '/',
    name: 'RSSFeeds',
    component: RSSFeeds,
    meta: { requiresAuth: true } // 需要登录才能访问
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginPage
  },
  {
    path: '/magnets/:rssFeedId',
    name: 'MagnetManager',
    component: MagnetManager,
    meta: { requiresAuth: true },
    props: true // 允许通过路由传递参数给组件
  },
  {
    path: '/logs',
    name: 'LogViewer',
    component: LogViewer,
    meta: { requiresAuth: true }
  },
  {
    path: '/login-logs',
    name: 'LoginLogs',
    component: LoginLogs,
    meta: { requiresAuth: true } // 确保只有登录后可以访问
  },
  {
    path: '/:pathMatch(.*)*', // 匹配所有未定义的路径
    name: 'NotFound',
    component: NotFound
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (token) {
      next(); // 有 Token 继续访问
    } else {
      next({ name: 'Login' }); // 没有 Token 跳转到登录页面
    }
  } else {
    next(); // 不需要认证的页面可以访问
  }
});

export default router;
