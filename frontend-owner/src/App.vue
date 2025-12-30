<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
import { computed, onMounted, onUnmounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { showNotify } from 'vant'
import { getWebSocketUrl } from '@/utils/request'

export default {
  name: 'App',
  setup() {
    const store = useStore()
    const router = useRouter()
    const userInfo = computed(() => store.state.userInfo)
    let ws = null
    
    // 初始化WebSocket连接（仅业主和维修人员）
    const initWebSocket = () => {
      if (!userInfo.value || !userInfo.value.id) return
      
      const role = userInfo.value.role
      // 只为业主和维修人员建立WebSocket连接
      if (role !== 'owner' && role !== 'maintenance') return
      
      const token = localStorage.getItem('token')
      const userId = userInfo.value.id
      
      const wsPath = role === 'owner' 
        ? `/ws/owner/${userId}?token=${token}`
        : `/ws/maintenance/${userId}?token=${token}`
      
      ws = new WebSocket(getWebSocketUrl(wsPath))
      
      ws.onopen = () => {
        console.log('WebSocket连接成功')
        // 启动心跳
        setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send('ping')
          }
        }, 30000)
      }
      
      ws.onmessage = (event) => {
        if (event.data === 'pong') return
        
        try {
          const message = JSON.parse(event.data)
          
          if (role === 'owner') {
            // 业主端消息处理
            if (message.type === 'repair_status_update') {
              const notifyType = message.data.deleted ? 'danger' : 'primary'
              const notifyMessage = message.data.deleted 
                ? `工单 ${message.data.order_number}\n${message.data.message}`
                : message.data.message || '工单状态已更新'
              
              const notify = showNotify({
                type: notifyType,
                message: notifyMessage,
                duration: 0,  // 不自动关闭，需用户手动点击
                onClick: () => {
                  notify.close()  // 点击后手动关闭通知
                  if (!message.data.deleted) {
                    router.push(`/repair/${message.data.id}`)
                  } else {
                    router.push('/repairs')
                  }
                }
              })
              
              // 通过Vuex通知页面更新
              store.dispatch('notifyRepairStatusUpdate', message.data)
            }
          } else if (role === 'maintenance') {
            // 维修人员端消息处理
            if (message.type === 'new_workorder') {
              const notify = showNotify({
                type: 'primary',
                message: `您有新的维修工单！\n工单号：${message.data.order_number}`,
                duration: 0,  // 不自动关闭
                onClick: () => {
                  notify.close()  // 点击后手动关闭通知
                  router.push(`/maintenance/workorder/${message.data.id}`)
                }
              })
              
              // 通过Vuex通知页面更新
              store.dispatch('notifyNewWorkorder', message.data)
            } else if (message.type === 'workorder_deleted') {
              const notify = showNotify({
                type: 'danger',
                message: `工单 ${message.data.order_number}\n${message.data.message}`,
                duration: 0,  // 不自动关闭
                onClick: () => {
                  notify.close()  // 点击后手动关闭通知
                  router.push('/maintenance/workorders')  // 跳转到工单列表
                }
              })
              
              // 通过Vuex通知页面更新
              store.dispatch('notifyWorkorderDeleted', message.data)
            }
          }
        } catch (error) {
          console.error('WebSocket消息解析失败:', error)
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket错误:', error)
      }
      
      ws.onclose = () => {
        console.log('WebSocket连接关闭')
        // 3秒后重连
        setTimeout(() => {
          if (userInfo.value && userInfo.value.id) {
            initWebSocket()
          }
        }, 3000)
      }
    }
    
    const closeWebSocket = () => {
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

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: #f7f8fa;
}

#app {
  width: 100%;
  min-height: 100vh;
}
</style>
