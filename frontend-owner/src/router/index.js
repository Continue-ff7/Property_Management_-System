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
    path: '/home',
    component: () => import('@/layout/Index.vue'),
    redirect: '/home/index',
    meta: { role: 'owner' },
    children: [
      {
        path: '/home/index',
        name: 'Home',
        component: () => import('@/views/Home.vue'),
        meta: { title: '首页', role: 'owner' }
      },
      {
        path: '/bills',
        name: 'Bills',
        component: () => import('@/views/Bills.vue'),
        meta: { title: '我的账单', role: 'owner' }
      },
      {
        path: '/repairs',
        name: 'Repairs',
        component: () => import('@/views/Repairs.vue'),
        meta: { title: '我的报修', role: 'owner' }
      },
      {
        path: '/profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '我的', role: 'owner' }
      }
    ]
  },
  {
    path: '/repair/create',
    name: 'RepairCreate',
    component: () => import('@/views/RepairCreate.vue'),
    meta: { title: '提交报修', role: 'owner' }
  },
  {
    path: '/repair/:id',
    name: 'RepairDetail',
    component: () => import('@/views/RepairDetail.vue'),
    meta: { title: '维修详情', role: 'owner' }
  },
  {
    path: '/repair/:id/chat',
    name: 'RepairChat',
    component: () => import('@/views/RepairChat.vue'),
    meta: { title: '聊天', role: 'owner' }
  },
  {
    path: '/announcements',
    name: 'Announcements',
    component: () => import('@/views/Announcements.vue'),
    meta: { title: '公告通知', role: 'owner' }
  },
  {
    path: '/ai-assistant',
    name: 'AIAssistant',
    component: () => import('@/views/AIAssistant.vue'),
    meta: { title: 'AI助手', role: 'owner' }
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
  const userInfo = store.state.userInfo
  const userRole = userInfo?.role
  
  // 访问根路径，始终跳转到登录页
  if (to.path === '/') {
    next('/login')
    return
  }
  
  // 未登录访问需要权限的页面，跳转到登录页
  if (to.path !== '/login' && !token) {
    next('/login')
    return
  }
  
  // 已登录访问登录页，允许访问（可以切换账号）
  if (to.path === '/login' && token) {
    next()
    return
  }
  
  // 角色权限验证
  if (to.meta.role && to.meta.role !== userRole) {
    // 访问的路由需要特定角色，但当前用户角色不匹配
    if (userRole === 'maintenance') {
      // 维修人员访问业主页面，重定向到维修人员首页
      next('/maintenance/workorders')
    } else if (userRole === 'owner') {
      // 业主访问维修人员页面，重定向到业主首页
      next('/home/index')
    } else {
      // 角色未知，跳转登录页
      store.dispatch('logout')
      next('/login')
    }
    return
  }
  
  next()
})

export default router
