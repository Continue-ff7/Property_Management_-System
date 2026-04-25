import axios from 'axios'
import { showToast } from 'vant'

// 获取当前角色（本地开发版）
const getCurrentRole = () => {
  const path = window.location.pathname
  
  // 本地开发：pathname 包含 /maintenance
  if (path.startsWith('/maintenance')) {
    return 'maintenance'
  }
  
  // 默认业主
  return 'owner'
}

// 获取token key
const getTokenKey = (role) => {
  return role === 'maintenance' ? 'maintenance_token' : 'owner_token'
}

// 获取userInfo key
const getUserInfoKey = (role) => {
  return role === 'maintenance' ? 'maintenance_userInfo' : 'owner_userInfo'
}

// 获取当前token（根据当前路径）
const getToken = () => {
  const role = getCurrentRole()
  return localStorage.getItem(getTokenKey(role)) || ''
}

// 获取后端服务器地址
// API基础地址 - 动态检测
const getApiBaseUrl = () => {
  // 如果有环境变量配置，优先使用
  if (process.env.VUE_APP_API_BASE_URL) {
    return process.env.VUE_APP_API_BASE_URL
  }
  
  // 本地开发环境
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8088'
  }
  
  // 部署环境：使用相对路径，让Nginx代理处理
  return ''
}

export const API_BASE_URL = getApiBaseUrl()

// 获取WebSocket地址
export const getWebSocketUrl = (path) => {
  // 部署环境（相对路径）：使用 wss:// 或 ws:// 根据当前协议
  if (API_BASE_URL === '') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}${path}`
  }
  // 本地开发
  const wsUrl = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://')
  return `${wsUrl}${path}`
}

// 处理图片URL
export const getImageUrl = (url) => {
  if (!url) return ''
  // 如果已经是完整URL，直接返回
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  // 拼接完整URL
  return `${API_BASE_URL}${url}`
}

const request = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 10000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 每次请求都重新获取 token（确保角色判断正确）
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
let logoutTimer = null  // 存储1.5秒延迟跳转的定时器ID
let isLoggingOut = false  // 标记是否正在执行登出流程

request.interceptors.response.use(
  response => {
    // 请求成功，取消之前的跳转定时器
    if (logoutTimer) {
      clearTimeout(logoutTimer)
      logoutTimer = null
      isLoggingOut = false
    }
    return response.data
  },
  error => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        // 分别处理登录失败和 token 过期
        const errorMsg = data.detail || '认证失败'
        
        if (errorMsg.includes('用户名') || errorMsg.includes('密码')) {
          // 登录失败，不跳转，只显示错误
          showToast(errorMsg)
        } else {
          // token过期，准备跳转
          // 如果已经在登出流程中，不重复处理
          if (!isLoggingOut) {
            isLoggingOut = true
            showToast('登录已过期，请重新登录')
            
            // 取消之前的定时器
            if (logoutTimer) {
              clearTimeout(logoutTimer)
            }
            
            // 设置新的定时器，在跳转前清空token
            logoutTimer = setTimeout(() => {
              // 清除当前角色和所有token
              localStorage.removeItem('current_role_owner')
              localStorage.removeItem('current_role_maintenance')
              localStorage.removeItem('owner_token')
              localStorage.removeItem('maintenance_token')
              localStorage.removeItem('owner_userInfo')
              localStorage.removeItem('maintenance_userInfo')
              window.location.href = '/login'
            }, 1500)
          }
        }
      } else {
        showToast(data.detail || '请求失败')
      }
    } else {
      showToast('网络错误')
    }
    return Promise.reject(error)
  }
)

export default request
