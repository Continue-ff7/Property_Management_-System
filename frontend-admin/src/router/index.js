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
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '数据看板', icon: 'DataAnalysis' }
      },
      {
        path: 'owners',
        name: 'Owners',
        component: () => import('@/views/owners/Index.vue'),
        meta: { title: '业主管理', icon: 'User' }
      },
      {
        path: 'properties',
        name: 'Properties',
        component: () => import('@/views/properties/Index.vue'),
        meta: { title: '房产管理', icon: 'OfficeBuilding' }
      },
      {
        path: 'bills',
        name: 'Bills',
        component: () => import('@/views/bills/Index.vue'),
        meta: { title: '账单管理', icon: 'Tickets' }
      },
      {
        path: 'repairs',
        name: 'Repairs',
        component: () => import('@/views/repairs/Index.vue'),
        meta: { title: '报修管理', icon: 'Tools' }
      },
      {
        path: 'maintenance',
        name: 'Maintenance',
        component: () => import('@/views/maintenance/Index.vue'),
        meta: { title: '维修人员', icon: 'UserFilled' }
      },
      {
        path: 'announcements',
        name: 'Announcements',
        component: () => import('@/views/announcements/Index.vue'),
        meta: { title: '公告管理', icon: 'Bell' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 智慧物业` : '智慧物业'
  
  if (to.meta.requiresAuth && !store.getters.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && store.getters.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router
