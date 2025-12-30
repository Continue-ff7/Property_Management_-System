<template>
  <div class="chat-page">
    <!-- 顶部导航栏 -->
    <van-nav-bar
      :title="chatTitle"
      left-arrow
      @click-left="onBack"
      fixed
    >
      <template #right>
        <van-icon name="ellipsis" size="20" />
      </template>
    </van-nav-bar>
    
    <div class="chat-content" ref="chatContainer">
      <!-- 空状态 -->
      <div v-if="messages.length === 0" class="empty-state">
        <van-empty description="暂无消息，开始聊天吧~" />
      </div>
      
      <!-- 聊天消息列表 -->
      <div class="message-list">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['message-item', msg.isMine ? 'mine' : 'other']"
        >
          <!-- 时间戳 -->
          <div v-if="shouldShowTime(index)" class="time-divider">
            {{ formatTime(msg.timestamp) }}
          </div>
          
          <!-- 消息内容 -->
          <div class="message-wrapper">
            <van-image
              v-if="!msg.isMine"
              round
              width="36"
              height="36"
              :src="otherAvatar"
              class="avatar"
            />
            
            <div class="message-bubble">
              <div class="bubble-content">{{ msg.text }}</div>
            </div>
            
            <van-image
              v-if="msg.isMine"
              round
              width="36"
              height="36"
              :src="myAvatar"
              class="avatar"
            />
          </div>
        </div>
      </div>
    </div>
    
    <!-- 底部输入框 -->
    <div class="chat-footer">
      <van-icon name="smile-o" size="24" class="footer-icon" />
      <input
        v-model="messageText"
        type="text"
        placeholder="输入消息..."
        class="message-input"
        @keyup.enter="sendMessage"
      />
      <van-button
        type="primary"
        size="small"
        class="send-btn"
        @click="sendMessage"
        :disabled="!messageText.trim()"
      >
        发送
      </van-button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from 'vuex'
import { showToast } from 'vant'
import { getWebSocketUrl, API_BASE_URL, getImageUrl } from '@/utils/request'

export default {
  name: 'RepairChat',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const store = useStore()
    const userInfo = computed(() => store.state.userInfo)
    
    const repairId = route.params.id
    const messages = ref([])
    const messageText = ref('')
    const chatContainer = ref(null)
    // 头像：默认图片，后续从用户信息和工单中获取
    const myAvatar = ref('https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg')
    const otherAvatar = ref('https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg')
    const otherUserName = ref('')  // 对方用户名
    const chatTitle = ref('聊天')  // 聊天标题
    const workorder = ref(null)  // 工单信息
    
    let ws = null
    
    const onBack = () => {
      router.back()
    }
    
    // 获取工单信息和头像
    const loadWorkorderInfo = async () => {
      try {
        const token = localStorage.getItem('token')
        
        // 从 Vuex 获取用户信息，如果没有则从 localStorage 获取
        let currentUserInfo = userInfo.value
        if (!currentUserInfo || !currentUserInfo.role) {
          const storedUserInfo = localStorage.getItem('userInfo')
          if (storedUserInfo) {
            currentUserInfo = JSON.parse(storedUserInfo)
          }
        }
        
        const isOwner = currentUserInfo?.role === 'owner'
        
        // 调试日志
        console.log('=== loadWorkorderInfo 调试信息 ===')
        console.log('Vuex userInfo:', userInfo.value)
        console.log('localStorage userInfo:', localStorage.getItem('userInfo'))
        console.log('最终使用的 userInfo:', currentUserInfo)
        console.log('role:', currentUserInfo?.role)
        console.log('isOwner:', isOwner)
        console.log('repairId:', repairId)
        
        // 1. 设置自己的头像
        if (currentUserInfo?.avatar) {
          myAvatar.value = getImageUrl(currentUserInfo.avatar)
        }
        
        // 2. 获取工单信息和对方头像
        let apiUrl
        if (isOwner) {
          console.log('✅ 业主端：调用 /api/v1/owner/repairs')
          // 业主端：获取自己的工单
          const response = await fetch(`${API_BASE_URL}/api/v1/owner/repairs`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          if (response.ok) {
            const repairs = await response.json()
            workorder.value = repairs.find(r => r.id === parseInt(repairId))
            if (workorder.value) {
              if (workorder.value.maintenance_worker_name) {
                otherUserName.value = workorder.value.maintenance_worker_name
                chatTitle.value = `与维修人员：${workorder.value.maintenance_worker_name}`
              }
              // 设置维修人员头像
              if (workorder.value.maintenance_worker_avatar) {
                otherAvatar.value = getImageUrl(workorder.value.maintenance_worker_avatar)
                console.log('✅ 设置维修人员头像:', otherAvatar.value)
              } else {
                console.log('⚠️ 工单中没有 maintenance_worker_avatar 字段')
              }
            }
          }
        } else {
          console.log('✅ 维修人员端：调用 /api/v1/maintenance/orders/' + repairId)
          // 维修人员端：获取分配给自己的工单
          const response = await fetch(`${API_BASE_URL}/api/v1/maintenance/orders/${repairId}`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          if (!response.ok) {
            console.error(`❗ API 调用失败: ${response.status} ${response.statusText}`)
            if (response.status === 403) {
              console.error('⚠️ 403 Forbidden: 这个工单没有分配给当前维修人员')
              showToast('您没有权限查看这个工单')
            } else if (response.status === 404) {
              console.error('⚠️ 404 Not Found: 工单不存在')
              showToast('工单不存在')
            }
            return
          }
          
          if (response.ok) {
            workorder.value = await response.json()
            if (workorder.value) {
              if (workorder.value.owner_name) {
                otherUserName.value = workorder.value.owner_name
                chatTitle.value = `与业主：${workorder.value.owner_name}`
              }
              // 设置业主头像
              if (workorder.value.owner_avatar) {
                otherAvatar.value = getImageUrl(workorder.value.owner_avatar)
                console.log('✅ 设置业主头像:', otherAvatar.value)
              } else {
                console.log('⚠️ 工单中没有 owner_avatar 字段')
              }
            }
          }
        }
      } catch (error) {
        console.error('获取工单信息失败:', error)
      }
    }
    
    // 加载历史聊天记录
    const loadChatHistory = async () => {
      try {
        const token = localStorage.getItem('token')
        const response = await fetch(`${API_BASE_URL}/api/v1/chat/history/${repairId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        if (response.ok) {
          const history = await response.json()
          messages.value = history.map(msg => ({
            id: msg.id,
            text: msg.message,
            timestamp: new Date(msg.timestamp),
            isMine: msg.sender_id === userInfo.value?.id,
            senderName: msg.sender_name
          }))
          scrollToBottom()
        } else {
          console.error('加载历史消息失败:', response.status)
        }
      } catch (error) {
        console.error('加载历史消息失败:', error)
      }
    }
    
    // 初始化WebSocket连接
    const initWebSocket = () => {
      const token = localStorage.getItem('token')
      const userId = userInfo.value?.id
      
      if (!userId) {
        showToast('用户信息获取失败')
        return
      }
      
      ws = new WebSocket(getWebSocketUrl(`/ws/chat/${repairId}?token=${token}`))
      
      ws.onopen = () => {
        console.log('WebSocket连接成功')
        // 发送身份验证消息
        ws.send(JSON.stringify({
          user_id: userId
        }))
        
        // 启动心跳
        setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send('ping')
          }
        }, 30000)
      }
      
      ws.onmessage = (event) => {
        if (event.data === 'pong') {
          return
        }
        
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'connected') {
            console.log('聊天连接成功')
            // 加载历史消息
            loadChatHistory()
          } else if (data.type === 'message') {
            // 收到消息，检查是否已存在
            const exists = messages.value.some(m => m.id === data.id)
            if (!exists) {
              messages.value.push({
                id: data.id,
                text: data.message,
                timestamp: new Date(data.timestamp),
                isMine: data.sender_id === userId,
                senderName: data.sender_name
              })
              scrollToBottom()
            }
          } else if (data.type === 'error') {
            showToast(data.message)
          }
        } catch (error) {
          console.error('消息解析失败:', error)
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket错误:', error)
        showToast('聊天连接失败')
      }
      
      ws.onclose = () => {
        console.log('WebSocket连接关闭')
        // 3秒后重连
        setTimeout(() => {
          if (ws && ws.readyState === WebSocket.CLOSED) {
            initWebSocket()
          }
        }, 3000)
      }
    }
    
    const sendMessage = () => {
      if (!messageText.value.trim()) return
      
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          message: messageText.value
        }))
        
        messageText.value = ''
      } else {
        showToast('连接已断开，请稍后重试')
      }
    }
    
    const scrollToBottom = () => {
      nextTick(() => {
        if (chatContainer.value) {
          chatContainer.value.scrollTop = chatContainer.value.scrollHeight
        }
      })
    }
    
    const shouldShowTime = (index) => {
      if (index === 0) return true
      const currentMsg = messages.value[index]
      const prevMsg = messages.value[index - 1]
      const timeDiff = currentMsg.timestamp - prevMsg.timestamp
      return timeDiff > 5 * 60 * 1000 // 超过5分钟显示时间
    }
    
    const formatTime = (date) => {
      if (!date) return ''
      const d = new Date(date)
      const hour = String(d.getHours()).padStart(2, '0')
      const minute = String(d.getMinutes()).padStart(2, '0')
      return `${hour}:${minute}`
    }
    
    const closeWebSocket = () => {
      if (ws) {
        ws.close()
        ws = null
      }
    }
    
    onMounted(() => {
      // 先加载工单信息，然后初始化WebSocket
      loadWorkorderInfo()
      setTimeout(() => {
        initWebSocket()
      }, 300)
    })
    
    onUnmounted(() => {
      closeWebSocket()
    })
    
    return {
      messages,
      messageText,
      chatContainer,
      myAvatar,
      otherAvatar,
      chatTitle,
      onBack,
      sendMessage,
      shouldShowTime,
      formatTime
    }
  }
}
</script>

<style scoped>
.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f7f8fa;
}

.chat-content {
  flex: 1;
  overflow-y: auto;
  padding: 56px 0 60px;
  -webkit-overflow-scrolling: touch;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
}

.empty-text {
  margin-top: 16px;
  font-size: 14px;
  color: #969799;
}

.message-list {
  padding: 12px 16px;
}

.message-item {
  margin-bottom: 20px;
}

.time-divider {
  text-align: center;
  font-size: 12px;
  color: #969799;
  margin: 12px 0;
}

.message-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.message-item.mine .message-wrapper {
  flex-direction: row-reverse;
}

.avatar {
  flex-shrink: 0;
}

.message-bubble {
  max-width: 70%;
  position: relative;
}

.bubble-content {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.5;
  word-wrap: break-word;
  word-break: break-word;
}

.message-item.other .bubble-content {
  background: white;
  color: #323233;
  border-top-left-radius: 4px;
}

.message-item.mine .bubble-content {
  background: #1989fa;
  color: white;
  border-top-right-radius: 4px;
}

.chat-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-top: 1px solid #ebedf0;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
}

.footer-icon {
  color: #969799;
  cursor: pointer;
}

.footer-icon:active {
  opacity: 0.7;
}

.message-input {
  flex: 1;
  height: 36px;
  padding: 0 12px;
  border: 1px solid #ebedf0;
  border-radius: 18px;
  font-size: 14px;
  outline: none;
  background: #f7f8fa;
}

.message-input:focus {
  border-color: #1989fa;
  background: white;
}

.send-btn {
  border-radius: 18px;
  padding: 0 20px;
  height: 36px;
}

.send-btn:disabled {
  background: #ebedf0;
  border-color: #ebedf0;
  color: #c8c9cc;
}
</style>
