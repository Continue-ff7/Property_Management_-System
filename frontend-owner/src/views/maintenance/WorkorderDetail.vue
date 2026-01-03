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
          <div 
            class="status-badge"
            :class="`status-${workorder.status}`"
          >
            <span class="status-dot"></span>
            {{ getStatusText(workorder) }}
          </div>
        </div>
        
        <van-cell-group>
          <van-cell title="报修地址" :value="workorder.property_info" />
          <van-cell title="问题描述" :value="workorder.description" />
          <van-cell title="紧急程度">
            <template #value>
              <div 
                class="urgency-badge"
                :class="`urgency-${workorder.urgency_level}`"
              >
                {{ getUrgencyText(workorder.urgency_level) }}
              </div>
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
          <!-- 业主头像和基本信息 -->
          <div class="owner-header" style="display: flex; align-items: center; margin-bottom: 12px;">
            <van-image
              round
              width="50"
              height="50"
              :src="workorder.owner_avatar ? getImageUrl(workorder.owner_avatar) : 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg'"
              style="margin-right: 12px;"
            />
            <div>
              <div style="font-size: 16px; font-weight: 500; margin-bottom: 4px;">{{ workorder.owner_name }}</div>
              <div style="font-size: 14px; color: #969799;">{{ workorder.owner_phone }}</div>
            </div>
          </div>
          
          <div style="display: flex; gap: 8px;">
            <van-button 
              type="primary" 
              size="small"
              icon="phone-o"
              @click="callOwner"
              style="flex: 1;"
            >
              拨打电话
            </van-button>
            <van-button 
              type="primary" 
              size="small"
              icon="chat-o"
              @click="openChat"
              style="flex: 1;"
            >
              实时聊天
            </van-button>
          </div>
        </div>
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
      <div class="complete-card" v-if="workorder.status === 'completed' || workorder.status === 'pending_payment' || workorder.status === 'pending_evaluation' || workorder.status === 'finished'">
        <div class="card-title">
          <van-icon name="success" />
          <span>维修完成</span>
        </div>
        
        <van-cell title="完成时间" :value="formatDate(workorder.completed_at)" />
        
        <!-- 维修费用 -->
        <van-cell v-if="workorder.repair_cost && workorder.repair_cost > 0" title="维修费用">
          <template #value>
            <span style="color: #ff6b6b; font-weight: bold;">￥{{ workorder.repair_cost }}</span>
            <van-tag v-if="workorder.cost_paid" type="success" style="margin-left: 8px;">已支付</van-tag>
            <van-tag v-else type="warning" style="margin-left: 8px;">未支付</van-tag>
          </template>
        </van-cell>
        
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
      
      <!-- ✅ 业主评价信息 -->
      <div class="evaluation-card" v-if="workorder.rating && (workorder.status === 'finished' || workorder.status === 'pending_evaluation')">
        <div class="card-title">
          <van-icon name="star" color="#ee0a24" />
          <span>业主评价</span>
        </div>
        
        <!-- 评分 -->
        <div class="rating-section">
          <van-rate
            v-model="workorder.rating"
            :readonly="true"
            :size="24"
            void-color="#eee"
          />
          <span class="rating-score">{{ workorder.rating }}.0 分</span>
        </div>
        
        <!-- 评论内容 -->
        <div class="comment-section" v-if="workorder.comment">
          <div class="comment-label">评论内容：</div>
          <div class="comment-text">{{ workorder.comment }}</div>
        </div>
        <div class="comment-section" v-else>
          <div class="comment-text" style="color: #969799;">业主未填写评论</div>
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
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { showToast, showSuccessToast, showImagePreview, showDialog } from 'vant'
import { maintenanceWorkorderAPI } from '@/api'
import { getImageUrl, getWebSocketUrl } from '@/utils/request'

export default {
  name: 'MaintenanceWorkorderDetail',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()
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
    
    // ✅ 简化：直接根据状态返回类型
    const getStatusType = (order) => {
      const statusMap = {
        'pending': 'default',
        'assigned': 'primary',
        'in_progress': 'warning',
        'pending_payment': 'danger',
        'pending_evaluation': 'primary',
        'finished': 'success',
        'cancelled': 'default',
        'completed': 'success'  // 兼容旧数据
      }
      return statusMap[order.status || order] || 'default'
    }
        
    // ✅ 简化：直接根据状态返回文本
    const getStatusText = (order) => {
      const statusMap = {
        'pending': '待分配',
        'assigned': '待处理',
        'in_progress': '处理中',
        'pending_payment': '待支付',
        'pending_evaluation': '待评价',
        'finished': '已完结',
        'cancelled': '已取消',
        'completed': '已完成'  // 兼容旧数据
      }
      return statusMap[order.status || order] || order.status || order
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
        low: '低',
        medium: '中',
        high: '高',
        urgent: '紧急'
      }
      return map[level] || '低'
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
    
    // 监听Vuex中的新工单通知（刷新详情）
    watch(
      () => store.state.newWorkorder,
      (newVal) => {
        if (newVal) {
          const currentWorkorderId = parseInt(route.params.id)
          if (newVal.id === currentWorkorderId) {
            console.log('当前工单状态更新，刷新详情')
            loadDetail()
          }
        }
      }
    )
    
    // 监听Vuex中的工单被删除通知
    watch(
      () => store.state.workorderDeleted,
      (newVal) => {
        if (newVal) {
          const currentWorkorderId = parseInt(route.params.id)
          if (newVal.id === currentWorkorderId) {
            console.log('当前工单已被删除，返回列表')
            showToast('工单已被管理员撤销')
            setTimeout(() => {
              router.push('/maintenance/workorders')
            }, 1500)
          }
        }
      }
    )
    
    // ✅ 监听评价通知，自动刷新详情
    watch(
      () => store.state.workorderEvaluated,
      (newVal) => {
        if (newVal) {
          const currentWorkorderId = parseInt(route.params.id)
          if (newVal.id === currentWorkorderId) {
            console.log('当前工单已被评价，刷新详情')
            loadDetail()
          }
        }
      }
    )
    
    // ✅ 监听支付通知，自动刷新详情
    watch(
      () => store.state.workorderStatusUpdate,
      (newVal) => {
        if (newVal) {
          const currentWorkorderId = parseInt(route.params.id)
          if (newVal.order_id === currentWorkorderId) {
            console.log('当前工单费用已支付，刷新详情')
            loadDetail()
          }
        }
      }
    )
    
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
.complete-card,
.evaluation-card {
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

/* 状态徽章 */
.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  color: white;
}

.status-badge .status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: white;
}

.status-badge.status-assigned {
  background: linear-gradient(135deg, #FF9500 0%, #FF6B00 100%);
}

.status-badge.status-in_progress {
  background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
}

.status-badge.status-completed {
  background: linear-gradient(135deg, #52C41A 0%, #389E0D 100%);
}

.status-badge.status-cancelled {
  background: linear-gradient(135deg, #999999 0%, #666666 100%);
}

.status-badge.status-pending {
  background: linear-gradient(135deg, #FF9500 0%, #FF6B00 100%);
}

/* 紧急程度徽章 */
.urgency-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  color: white;
  text-align: center;
}

/* 低 - 蓝色 */
.urgency-badge.urgency-low {
  background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
}

/* 中 - 黄色/橙色 */
.urgency-badge.urgency-medium {
  background: linear-gradient(135deg, #FAAD14 0%, #D48806 100%);
}

/* 高 - 橙红色 */
.urgency-badge.urgency-high {
  background: linear-gradient(135deg, #FF6B00 0%, #E85500 100%);
}

/* 紧急 - 红色 */
.urgency-badge.urgency-urgent {
  background: linear-gradient(135deg, #F5222D 0%, #CF1322 100%);
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

/* ✅ 评价卡片样式 */
.evaluation-card {
  background: white;
  border: 1px solid #f2f3f5;
}

.evaluation-card .card-title {
  color: #ee0a24;
}

.rating-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid #f2f3f5;
}

.rating-score {
  font-size: 18px;
  font-weight: bold;
  color: #ee0a24;
}

.comment-section {
  padding: 16px 0;
}

.comment-label {
  font-size: 14px;
  color: #646566;
  margin-bottom: 8px;
  font-weight: 500;
}

.comment-text {
  font-size: 14px;
  line-height: 1.6;
  color: #323233;
  padding: 12px;
  background: #f7f8fa;
  border-radius: 6px;
  border-left: 3px solid #ee0a24;
}
</style>
