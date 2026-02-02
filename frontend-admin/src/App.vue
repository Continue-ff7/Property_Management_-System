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
    let reconnectTimer = null  // 重连定时器
    
    // 消息去重集合（记录最近收到的消息ID）
    const recentMessageIds = new Set()
    const MESSAGE_CACHE_TIME = 5000  // 5秒内的重复消息忽略
    
    // 检查消息是否重复
    const isDuplicateMessage = (messageType, messageId) => {
      const key = `${messageType}_${messageId}`
      if (recentMessageIds.has(key)) {
        console.log(`[去重] 忽略重复消息: ${key}`)
        return true
      }
      
      // 记录该消息，5秒后自动清除
      recentMessageIds.add(key)
      setTimeout(() => {
        recentMessageIds.delete(key)
      }, MESSAGE_CACHE_TIME)
      
      return false
    }
    
    const initWebSocket = () => {
      const token = localStorage.getItem('token')
      const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
      
      // 只为管理员建立WebSocket
      if (!token || userInfo.role !== 'manager' || !userInfo.id) return
          
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
      // 添加用户ID到URL，后端根据ID管理连接
      ws = new WebSocket(getWebSocketUrl(`/ws/manager/${userInfo.id}?token=${token}`))
      
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
            // ✅ 消息去重检查
            if (isDuplicateMessage('new_repair', message.data.id)) {
              return  // 忽略重复消息
            }
            
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
          else if (message.type === 'repair_status_update') {
            // ✅ 消息去重检查
            if (isDuplicateMessage('repair_status_update', message.data.id || message.data.order_number)) {
              return
            }
            
            // 收到工单状态更新通知（维修人员开始/完成维修）
            ElNotification({
              title: '工单状态更新',
              message: `工单号：${message.data.order_number}\n${message.data.message}`,
              type: 'success',
              duration: 5000,  // 5秒后自动关闭
              onClick: () => {
                router.push('/repairs')
              }
            })
            
            // 通过Vuex通知页面刷新
            store.dispatch('notifyRepairStatusUpdate', message.data)
          } else if (message.type === 'repair_evaluated') {
            // ✅ 消息去重检查
            if (isDuplicateMessage('repair_evaluated', message.data.id || message.data.order_number)) {
              return
            }
            
            // ✅ 新增：处理评价通知
            ElNotification({
              title: '工单已评价',
              message: `工单号：${message.data.order_number}\n${message.data.message}\n评论: ${message.data.comment || '无'}`,
              type: 'success',
              duration: 0,  // 不自动关闭
              onClick: () => {
                router.push('/repairs')
              }
            })
            
            // 通过Vuex通知页面刷新
            store.dispatch('notifyRepairStatusUpdate', message.data)
          }
        } catch (error) {
          console.error('WebSocket消息解析失败:', error)
        }
      }
      
      ws.onerror = (error) => {
        console.error('管理员WebSocket错误:', error)
      }
      
      ws.onclose = (event) => {
        console.log('管理员WebSocket连接关闭', event.code, event.reason)
        if (heartbeatInterval) {
          clearInterval(heartbeatInterval)
          heartbeatInterval = null
        }
        
        // 清除旧的重连定时器
        if (reconnectTimer) {
          clearTimeout(reconnectTimer)
        }
        
        // 3秒后尝试重连
        reconnectTimer = setTimeout(() => {
          const currentUserInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
          if (currentUserInfo.role === 'manager') {
            console.log('尝试重新连接WebSocket...')
            initWebSocket()
          }
        }, 3000)
      }
    }
    
    const closeWebSocket = () => {
      // 清除所有定时器
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval)
        heartbeatInterval = null
      }
      if (reconnectTimer) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
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
