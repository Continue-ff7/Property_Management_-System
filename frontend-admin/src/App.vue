<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
import { onMounted, onUnmounted } from 'vue'
import { ElNotification } from 'element-plus'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { getWebSocketUrl } from '@/utils/request'

export default {
  name: 'App',
  setup() {
    const router = useRouter()
    const store = useStore()
    let ws = null
    let heartbeatInterval = null
    
    const initWebSocket = () => {
      const token = localStorage.getItem('token')
      const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
      
      // 只为管理员建立WebSocket
      if (!token || userInfo.role !== 'manager') return
          
      // 如果已经有连接，先关闭旧连接
      if (ws) {
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          console.log('WebSocket已存在，先关闭旧连接')
          try {
            ws.close()
          } catch (e) {
            console.error('关闭旧WebSocket失败:', e)
          }
          ws = null
        }
      }
          
      // 清除旧的心跳
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval)
        heartbeatInterval = null
      }
          
      console.log('创建WebSocket连接...')
      ws = new WebSocket(getWebSocketUrl(`/ws/manager?token=${token}`))
      
      ws.onopen = () => {
        console.log('管理员WebSocket连接成功')
        // 启动心跳
        heartbeatInterval = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send('ping')
          }
        }, 30000)
      }
      
      ws.onmessage = (event) => {
        if (event.data === 'pong') return
        
        try {
          const message = JSON.parse(event.data)
          
          if (message.type === 'new_repair') {
            // 收到新报修通知
            ElNotification({
              title: '新报修工单',
              message: `${message.data.owner_name} 提交了新的报修申请\n地址：${message.data.property_info}`,
              type: 'info',
              duration: 0,  // 0表示不自动关闭，需要用户手动点击
              onClick: () => {
                router.push('/repairs')
              }
            })
            
            // 通过Vuex通知页面刷新
            store.dispatch('notifyNewRepair', message.data)
          }
        } catch (error) {
          console.error('WebSocket消息解析失败:', error)
        }
      }
      
      ws.onerror = (error) => {
        console.error('管理员WebSocket错误:', error)
      }
      
      ws.onclose = () => {
        console.log('管理员WebSocket连接关闭')
        if (heartbeatInterval) {
          clearInterval(heartbeatInterval)
          heartbeatInterval = null
        }
        // 3秒后重连
        setTimeout(() => {
          const currentUserInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
          if (currentUserInfo.role === 'manager') {
            initWebSocket()
          }
        }, 3000)
      }
    }
    
    const closeWebSocket = () => {
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval)
        heartbeatInterval = null
      }
      if (ws) {
        ws.close()
        ws = null
      }
    }
    
    onMounted(() => {
      // 等待用户信息加载
      setTimeout(() => {
        initWebSocket()
      }, 1000)
    })
    
    onUnmounted(() => {
      closeWebSocket()
    })
  }
}
</script>

<style lang="scss">
#app {
  width: 100%;
  height: 100%;
}
</style>
