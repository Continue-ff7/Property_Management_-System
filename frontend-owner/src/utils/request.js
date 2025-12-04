import axios from 'axios'
import { showToast } from 'vant'
import store from '@/store'

// 获取后端服务器地址
export const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8088'

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
        showToast('登录已过期，请重新登录')
        store.commit('CLEAR_TOKEN')
        // 跳转到登录页
        setTimeout(() => {
          window.location.href = '/login'
        }, 1500)
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
