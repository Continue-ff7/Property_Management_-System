import axios from 'axios'
import { showToast } from 'vant'
import store from '@/store'

// 获取后端服务器地址
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
  baseURL: '/api/v1',
  timeout: 10000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    const token = store.state.token
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
request.interceptors.response.use(
  response => {
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
          // token过期，清空并跳转
          showToast('登录已过期，请重新登录')
          store.commit('CLEAR_TOKEN')
          setTimeout(() => {
            window.location.href = '/login'
          }, 1500)
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
