<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
import { computed, onMounted, onUnmounted, watch } from 'vue'
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
    let heartbeatInterval = null  // 心跳定时器
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
    
    // ✅ 新增：添加通知到本地存储
    const addNotification = (notification) => {
      const stored = localStorage.getItem('maintenance_notifications')
      const notifications = stored ? JSON.parse(stored) : []
      notifications.unshift(notification)  // 添加到开头
      // 只保留50条最新通知
      if (notifications.length > 50) {
        notifications.pop()
      }
      localStorage.setItem('maintenance_notifications', JSON.stringify(notifications))
      // 更新红点状态
      store.commit('SET_HAS_NEW_NOTIFICATION', true)
    }
    
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
        console.log(`WebSocket连接成功 [用户ID: ${userId}, 角色: ${role}]`)
        
        // 清除旧的心跳定时器
        if (heartbeatInterval) {
          clearInterval(heartbeatInterval)
            heartbeatInterval = null
          }
          
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
            
            // ✅ 关键修复：实时获取用户角色，而不是使用闭包中的role变量
            const currentRole = userInfo.value?.role
            console.log(`收到WebSocket消息，当前角色: ${currentRole}, 消息类型: ${message.type}`, message.data)
            
            if (currentRole === 'owner') {
              // 业主端消息处理
              if (message.type === 'repair_status_update') {
                // ✅ 消息去重检查
                if (isDuplicateMessage('repair_status_update', message.data.id || message.data.order_number)) {
                  return  // 忽略重复消息
                }
                
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
            } else if (currentRole === 'maintenance') {
              // 维修人员端消息处理
              if (message.type === 'new_workorder') {
                // ✅ 消息去重检查
                if (isDuplicateMessage('new_workorder', message.data.id)) {
                  return
                }
                
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
                // ✅ 新增：刷新统计数据
                store.dispatch('loadMaintenanceStats')
                // ✅ 新增：添加通知到本地
                addNotification({
                  type: 'new_workorder',
                  title: '新工单分配',
                  message: `您有新的维修工单：${message.data.order_number}`,
                  time: new Date().toISOString(),
                  read: false,
                  workorderId: message.data.id
                })
              } else if (message.type === 'workorder_deleted') {
                // ✅ 消息去重检查
                if (isDuplicateMessage('workorder_deleted', message.data.id || message.data.order_number)) {
                  return
                }
                
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
            } else if (message.type === 'repair_evaluated') {
              // ✅ 消息去重检查
              if (isDuplicateMessage('repair_evaluated', message.data.id || message.data.order_number)) {
                return
              }
              
              // ✅ 新增：处理评价通知
              const notify = showNotify({
                type: 'success',
                message: `工单 ${message.data.order_number}\n${message.data.message}\n评论：${message.data.comment || '无'}`,
                duration: 0,
                onClick: () => {
                  notify.close()
                  router.push(`/maintenance/workorder/${message.data.id}`)
                }
              })
              
              // 通过Vuex通知页面更新
              store.dispatch('notifyWorkorderEvaluated', message.data)
            }
          }
        } catch (error) {
          console.error('WebSocket消息解析失败:', error)
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket错误:', error)
      }
      
      ws.onclose = (event) => {
        console.log('WebSocket连接关闭', event.code, event.reason)
        
        // 清除心跳定时器
        if (heartbeatInterval) {
          clearInterval(heartbeatInterval)
          heartbeatInterval = null
        }
        
        // 清除重连定时器
        if (reconnectTimer) {
          clearTimeout(reconnectTimer)
        }
        
        // 3秒后重连
        reconnectTimer = setTimeout(() => {
          if (userInfo.value && userInfo.value.id) {
            console.log('尝试重新连接WebSocket...')
            initWebSocket()
          }
        }, 3000)
      }
    }
    
    const closeWebSocket = () => {
      if (ws) {
        console.log('WebSocket连接关闭')
        ws.close()
        ws = null
      }
      // 清除所有定时器
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval)
        heartbeatInterval = null
      }
      if (reconnectTimer) {
        clearTimeout(reconnectTimer)
        reconnectTimer = null
      }
    }
    
    onMounted(() => {
      // 等待用户信息加载
      setTimeout(() => {
        initWebSocket()
        
        // ✅ 新增：如果是维修人员，加载统计数据
        if (userInfo.value && userInfo.value.role === 'maintenance') {
          store.dispatch('loadMaintenanceStats')
          
          // ✅ 定时轮询（每60秒刷新一次）
          setInterval(() => {
            store.dispatch('loadMaintenanceStats')
          }, 60000)
        }
      }, 1000)
      
      // 监听网络变化（在线/离线）
      window.addEventListener('online', () => {
        console.log('网络已恢复，尝试重连WebSocket')
        setTimeout(() => {
          initWebSocket()
        }, 1000)
      })
      
      window.addEventListener('offline', () => {
        console.log('网络已断开')
        closeWebSocket()
      })
      
      // 监听页面可见性变化（切换标签页/最小化窗口）
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
          // 页面可见时检查连接状态
          if (!ws || ws.readyState !== WebSocket.OPEN) {
            console.log('页面恢复可见，检查WebSocket连接')
            setTimeout(() => {
              initWebSocket()
            }, 500)
          }
        }
      })
    })
    
    // ✅ 关键修复：监听用户信息变化，重新初始化WebSocket
    watch(
      () => userInfo.value?.id,
      (newUserId, oldUserId) => {
        // 用户ID变化时（登录/退出/切换用户）
        if (newUserId !== oldUserId) {
          console.log(`用户信息变化: ${oldUserId} -> ${newUserId}`)
          closeWebSocket()  // 关闭旧连接
          if (newUserId) {
            // 延迟500ms建立新连接，给旧连接断开的时间
            setTimeout(() => {
              initWebSocket()
            }, 500)
          }
        }
      }
    )
    
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
