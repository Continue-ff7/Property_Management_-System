import { createRouter, createWebHistory } from 'vue-router'
import store from '@/store'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: () => import('@/layout/Index.vue'),
    redirect: '/home',
    children: [
      {
        path: '/home',
        name: 'Home',
        component: () => import('@/views/Home.vue'),
        meta: { title: '首页' }
      },
      {
        path: '/bills',
        name: 'Bills',
        component: () => import('@/views/Bills.vue'),
        meta: { title: '我的账单' }
      },
      {
        path: '/repairs',
        name: 'Repairs',
        component: () => import('@/views/Repairs.vue'),
        meta: { title: '我的报修' }
      },
      {
        path: '/profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '我的' }
      }
    ]
  },
  {
    path: '/repair/create',
    name: 'RepairCreate',
    component: () => import('@/views/RepairCreate.vue'),
    meta: { title: '提交报修' }
  },
  {
    path: '/repair/:id',
    name: 'RepairDetail',
    component: () => import('@/views/RepairDetail.vue'),
    meta: { title: '维修详情' }
  },
  {
    path: '/announcements',
    name: 'Announcements',
    component: () => import('@/views/Announcements.vue'),
    meta: { title: '公告通知' }
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  document.title = to.meta.title || '智慧物业'
  
  const token = store.state.token
  if (to.path !== '/login' && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
