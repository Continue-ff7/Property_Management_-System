import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// API基础地址 - 动态检测
const getApiBaseUrl = () => {
  // 如果有环境变量配置，优先使用
  if (process.env.VUE_APP_API_BASE_URL) {
    return process.env.VUE_APP_API_BASE_URL
  }
  
  // 否则根据当前访问地址动态决定
  const hostname = window.location.hostname
  
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8088'
  } else {
    // 使用当前主机的IP地址
    return `http://${hostname}:8088`
  }
}

export const API_BASE_URL = getApiBaseUrl()

// 获取WebSocket地址
export const getWebSocketUrl = (path) => {
  const wsUrl = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://')
  return `${wsUrl}${path}`
}

// 创建axios实例
const service = axios.create({
  baseURL: '/api/v1',
  timeout: 15000
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('响应错误:', error)
    
    if (error.response) {
      const errorMsg = error.response.data.detail || '请求失败'
      
      switch (error.response.status) {
        case 401:
          // 区分登录失败和 token 过期
          if (errorMsg.includes('用户名') || errorMsg.includes('密码')) {
            // 登录失败，不清除token
            ElMessage.error(errorMsg)
          } else {
            // token过期
            ElMessage.error('登录已过期,请重新登录')
            localStorage.removeItem('token')
            localStorage.removeItem('userInfo')
            router.push('/login')
          }
          break
        case 403:
          ElMessage.error('没有权限访问')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器错误')
          break
        default:
          ElMessage.error(errorMsg)
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

export default service
