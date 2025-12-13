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
    path: '/repair/:id/chat',
    name: 'RepairChat',
    component: () => import('@/views/RepairChat.vue'),
    meta: { title: '聊天' }
  },
  {
    path: '/announcements',
    name: 'Announcements',
    component: () => import('@/views/Announcements.vue'),
    meta: { title: '公告通知' }
  },
  // 维修人员端路由
  {
    path: '/maintenance/workorders',
    name: 'MaintenanceWorkorders',
    component: () => import('@/views/maintenance/Workorders.vue'),
    meta: { title: '我的工单', requiresAuth: true, role: 'maintenance' }
  },
  {
    path: '/maintenance/workorder/:id',
    name: 'MaintenanceWorkorderDetail',
    component: () => import('@/views/maintenance/WorkorderDetail.vue'),
    meta: { title: '工单详情', requiresAuth: true, role: 'maintenance' }
  },
  {
    path: '/maintenance/workorder/:id/complete',
    name: 'CompleteWorkorder',
    component: () => import('@/views/maintenance/CompleteWorkorder.vue'),
    meta: { title: '完成维修', requiresAuth: true, role: 'maintenance' }
  },
  {
    path: '/maintenance/profile',
    name: 'MaintenanceProfile',
    component: () => import('@/views/maintenance/Profile.vue'),
    meta: { title: '个人中心', requiresAuth: true, role: 'maintenance' }
  },
  // 维修人员端聊天
  {
    path: '/maintenance/workorder/:id/chat',
    name: 'MaintenanceChat',
    component: () => import('@/views/RepairChat.vue'),
    meta: { title: '聊天', requiresAuth: true, role: 'maintenance' }
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
