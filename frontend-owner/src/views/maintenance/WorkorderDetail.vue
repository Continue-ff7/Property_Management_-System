<template>
  <div class="workorder-detail">
    <van-nav-bar
      title="工单详情"
      left-arrow
      @click-left="$router.back()"
      fixed
    />
    
    <div class="content" v-if="workorder">
      <!-- 工单信息卡片 -->
      <div class="info-card">
        <div class="order-header">
          <span class="order-number">#{{ workorder.order_number }}</span>
          <van-tag :type="getStatusType(workorder.status)">
            {{ getStatusText(workorder.status) }}
          </van-tag>
        </div>
        
        <van-cell-group>
          <van-cell title="报修地址" :value="workorder.property_info" />
          <van-cell title="问题描述" :value="workorder.description" />
          <van-cell title="紧急程度">
            <template #value>
              <van-tag :type="getUrgencyType(workorder.urgency_level)">
                {{ getUrgencyText(workorder.urgency_level) }}
              </van-tag>
            </template>
          </van-cell>
          <van-cell title="提交时间" :value="formatDate(workorder.created_at)" />
        </van-cell-group>
        
        <!-- 报修图片 -->
        <div class="images-section" v-if="workorder.images && workorder.images.length > 0">
          <div class="section-title">问题图片</div>
          <div class="image-grid">
            <van-image
              v-for="(img, index) in workorder.images"
              :key="index"
              width="100"
              height="100"
              :src="getImageUrl(img)"
              fit="cover"
              @click="previewImages(workorder.images.map(i => getImageUrl(i)), index)"
            />
          </div>
        </div>
      </div>
      
      <!-- 业主联系方式 -->
      <div class="contact-card">
        <div class="card-title">
          <van-icon name="user-o" />
          <span>业主信息</span>
        </div>
        
        <div class="contact-info">
          <div class="info-item">
            <span class="label">姓名：</span>
            <span class="value">{{ workorder.owner_name }}</span>
          </div>
          <div class="info-item">
            <span class="label">电话：</span>
            <span class="value">
              {{ workorder.owner_phone }}
              <van-button 
                type="primary" 
                size="mini" 
                @click="callOwner"
                style="margin-left: 8px;"
              >
                拨打
              </van-button>
            </span>
          </div>
        </div>
        
        <van-button 
          type="primary" 
          block 
          icon="chat-o"
          @click="openChat"
          style="margin-top: 12px;"
        >
          与业主实时聊天
        </van-button>
      </div>
      
      <!-- 操作按钮 -->
      <div class="action-card" v-if="workorder.status === 'assigned'">
        <van-button type="primary" block @click="startWork">
          开始维修
        </van-button>
      </div>
      
      <div class="action-card" v-else-if="workorder.status === 'in_progress'">
        <van-button type="success" block @click="goToComplete">
          完成维修
        </van-button>
      </div>
      
      <!-- 维修完成信息 -->
      <div class="complete-card" v-if="workorder.status === 'completed'">
        <div class="card-title">
          <van-icon name="success" />
          <span>维修完成</span>
        </div>
        
        <van-cell title="完成时间" :value="formatDate(workorder.completed_at)" />
        
        <!-- 维修完成图片 -->
        <div class="images-section" v-if="workorder.repair_images && workorder.repair_images.length > 0">
          <div class="section-title">完成照片</div>
          <div class="image-grid">
            <van-image
              v-for="(img, index) in workorder.repair_images"
              :key="index"
              width="100"
              height="100"
              :src="getImageUrl(img)"
              fit="cover"
              @click="previewImages(workorder.repair_images.map(i => getImageUrl(i)), index)"
            />
          </div>
        </div>
      </div>
    </div>
    
    <!-- 聊天弹窗 -->
    <van-popup 
      :show="showChat" 
      @update:show="showChat = $event"
      position="bottom" 
      round 
      :style="{ height: '80%' }"
    >
      <div class="chat-container">
        <div class="chat-header">
          <h3>与{{ workorder?.owner_name }}聊天</h3>
          <van-icon name="cross" @click="showChat = false" />
        </div>
        
        <div class="chat-messages" ref="messagesRef">
          <div 
            v-for="(msg, index) in messages" 
            :key="index"
            :class="['message-item', msg.isMine ? 'mine' : 'other']"
          >
            <div class="message-bubble">
              <div class="message-text">{{ msg.text }}</div>
              <div class="message-time">{{ formatTime(msg.time) }}</div>
            </div>
          </div>
          <div v-if="messages.length === 0" class="empty-tips">
            <van-empty description="暂无消息，开始聊天吧~" />
          </div>
        </div>
        
        <div class="chat-input">
          <van-field
            v-model="messageText"
            placeholder="输入消息..."
            @keyup.enter="sendMessage"
          />
          <van-button type="primary" @click="sendMessage" :disabled="!messageText.trim()">
            发送
          </van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast, showImagePreview, showDialog } from 'vant'
import { maintenanceWorkorderAPI } from '@/api'
import { getImageUrl, getWebSocketUrl } from '@/utils/request'

export default {
  name: 'MaintenanceWorkorderDetail',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const workorder = ref(null)
    const showChat = ref(false)
    const messages = ref([])
    const messageText = ref('')
    const messagesRef = ref(null)
    let ws = null
    
    const loadDetail = async () => {
      try {
        const id = parseInt(route.params.id)
        const data = await maintenanceWorkorderAPI.getWorkorderDetail(id)
        workorder.value = data
      } catch (error) {
        console.error('加载失败:', error)
        showToast('工单不存在')
        router.back()
      }
    }
    
    const startWork = async () => {
      try {
        await maintenanceWorkorderAPI.startWork(workorder.value.id)
        showSuccessToast('已开始维修')
        loadDetail()
      } catch (error) {
        console.error('操作失败:', error)
      }
    }
    
    const goToComplete = () => {
      router.push(`/maintenance/workorder/${workorder.value.id}/complete`)
    }
    
    const callOwner = () => {
      window.location.href = `tel:${workorder.value.owner_phone}`
    }
    
    const openChat = () => {
      router.push(`/maintenance/workorder/${workorder.value.id}/chat`)
    }
    
    const initWebSocket = () => {
      // WebSocket连接
      const token = localStorage.getItem('token')
      ws = new WebSocket(getWebSocketUrl(`/ws/chat/${workorder.value.id}?token=${token}`))
      
      ws.onopen = () => {
        console.log('WebSocket连接成功')
      }
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        messages.value.push({
          text: data.message,
          time: new Date(),
          isMine: data.sender_id === workorder.value.maintenance_worker_id
        })
        scrollToBottom()
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket错误:', error)
        showToast('聊天连接失败')
      }
      
      ws.onclose = () => {
        console.log('WebSocket连接关闭')
      }
    }
    
    const sendMessage = () => {
      if (!messageText.value.trim()) return
      
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          message: messageText.value
        }))
        
        messages.value.push({
          text: messageText.value,
          time: new Date(),
          isMine: true
        })
        
        messageText.value = ''
        scrollToBottom()
      } else {
        showToast('连接已断开，请重新打开')
      }
    }
    
    const scrollToBottom = () => {
      nextTick(() => {
        if (messagesRef.value) {
          messagesRef.value.scrollTop = messagesRef.value.scrollHeight
        }
      })
    }
    
    const previewImages = (images, index) => {
      showImagePreview({
        images,
        startPosition: index
      })
    }
    
    const getStatusType = (status) => {
      const map = {
        pending: 'default',
        assigned: 'primary',
        in_progress: 'warning',
        completed: 'success'
      }
      return map[status] || 'default'
    }
    
    const getStatusText = (status) => {
      const map = {
        pending: '待分配',
        assigned: '待处理',
        in_progress: '处理中',
        completed: '已完成'
      }
      return map[status] || status
    }
    
    const getUrgencyType = (level) => {
      const map = {
        low: 'success',
        medium: 'warning',
        high: 'danger'
      }
      return map[level] || 'default'
    }
    
    const getUrgencyText = (level) => {
      const map = {
        low: '一般',
        medium: '紧急',
        high: '非常紧急'
      }
      return map[level] || level
    }
    
    const formatDate = (date) => {
      if (!date) return '-'
      return new Date(date).toLocaleString('zh-CN')
    }
    
    const formatTime = (date) => {
      if (!date) return ''
      const d = new Date(date)
      const hour = String(d.getHours()).padStart(2, '0')
      const minute = String(d.getMinutes()).padStart(2, '0')
      return `${hour}:${minute}`
    }
    
    onMounted(() => {
      loadDetail()
    })
    
    onUnmounted(() => {
      if (ws) {
        ws.close()
      }
    })
    
    return {
      workorder,
      showChat,
      messages,
      messageText,
      messagesRef,
      startWork,
      goToComplete,
      callOwner,
      openChat,
      sendMessage,
      previewImages,
      getStatusType,
      getStatusText,
      getUrgencyType,
      getUrgencyText,
      formatDate,
      formatTime,
      getImageUrl
    }
  }
}
</script>

<style scoped>
.workorder-detail {
  background: #f7f8fa;
  min-height: 100vh;
  padding-bottom: 20px;
}

.content {
  padding-top: 46px;
}

.info-card,
.contact-card,
.action-card,
.complete-card {
  background: white;
  margin: 12px 16px;
  border-radius: 8px;
  padding: 16px;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f2f3f5;
}

.order-number {
  font-size: 14px;
  font-weight: bold;
  color: #323233;
}

.images-section {
  margin-top: 16px;
}

.section-title,
.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: bold;
  color: #323233;
  margin-bottom: 12px;
}

.image-grid {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.contact-info {
  margin-top: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  font-size: 14px;
}

.info-item .label {
  color: #969799;
  min-width: 60px;
}

.info-item .value {
  color: #323233;
  flex: 1;
  display: flex;
  align-items: center;
}

/* 聊天样式 */
.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f2f3f5;
}

.chat-header h3 {
  margin: 0;
  font-size: 16px;
}

.chat-header .van-icon {
  font-size: 20px;
  cursor: pointer;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.message-item {
  margin-bottom: 16px;
  display: flex;
}

.message-item.mine {
  justify-content: flex-end;
}

.message-item.other {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 8px;
}

.message-item.mine .message-bubble {
  background: #4A90E2;
  color: white;
}

.message-item.other .message-bubble {
  background: #f2f3f5;
  color: #323233;
}

.message-text {
  word-break: break-word;
  line-height: 1.5;
}

.message-time {
  font-size: 11px;
  margin-top: 4px;
  opacity: 0.7;
}

.empty-tips {
  padding: 60px 0;
}

.chat-input {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #f2f3f5;
  background: white;
}

.chat-input .van-field {
  flex: 1;
}
</style>
