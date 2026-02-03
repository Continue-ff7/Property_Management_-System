<template>
  <div class="complaint-detail">
    <van-nav-bar 
      title="投诉详情" 
      left-arrow
      @click-left="$router.back()"
      fixed
    />
    
    <div class="content" v-if="complaint">
      <!-- 投诉信息卡片 -->
      <div class="info-card">
        <div class="order-header">
          <span class="order-number">投诉编号：#{{ complaint.id }}</span>
          <van-tag :type="getStatusColor(complaint.status)">
            {{ getStatusName(complaint.status) }}
          </van-tag>
        </div>
        
        <van-cell-group>
          <van-cell title="投诉类型" :value="getTypeName(complaint.type)" />
          <van-cell title="投诉内容" :value="complaint.content" />
          <van-cell title="联系电话" :value="complaint.contact_phone" />
          <van-cell title="提交时间" :value="formatDateTime(complaint.created_at)" />
        </van-cell-group>
        
        <!-- 投诉图片 -->
        <div class="images-section" v-if="complaint.images && complaint.images.length > 0">
          <div class="section-title">相关图片</div>
          <div class="image-grid">
            <van-image
              v-for="(img, index) in complaint.images"
              :key="index"
              width="100"
              height="100"
              :src="img"
              fit="cover"
              @click="previewImages(index)"
            />
          </div>
        </div>
      </div>
      
      <!-- 物业回复 -->
      <div class="reply-card" v-if="complaint.reply">
        <div class="card-title">
          <van-icon name="comment-o" />
          <span>物业回复</span>
        </div>
        <div class="reply-content">{{ complaint.reply }}</div>
        <div class="reply-time">回复时间：{{ formatDateTime(complaint.updated_at) }}</div>
      </div>
      
      <!-- 评价区域 -->
      <div class="eval-card" v-if="complaint.status === 'completed' && !complaint.rating">
        <van-button 
          type="primary" 
          block
          @click="showRating = true"
        >
          评价处理结果
        </van-button>
      </div>
      
      <!-- 已评价 -->
      <div class="eval-card" v-if="complaint.rating">
        <div class="card-title">
          <van-icon name="star-o" />
          <span>我的评价</span>
        </div>
        <van-rate v-model="complaint.rating" :size="20" readonly />
      </div>
    </div>
    
    <!-- 评价弹窗 -->
    <van-popup :show="showRating" @update:show="showRating = $event" position="bottom" round>
      <div class="rating-popup">
        <div class="popup-title">评价处理</div>
        <div class="rating-desc">请对本次投诉处理进行评价</div>
        <van-rate v-model="rating" :size="32" color="#ffd21e" void-color="#eee" />
        <van-button 
          type="primary" 
          block 
          round
          size="large"
          @click="submitRating" 
          :loading="submitting"
          class="submit-btn"
        >
          提交评价
        </van-button>
      </div>
    </van-popup>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast, showImagePreview } from 'vant'

export default {
  name: 'ComplaintDetail',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const complaint = ref(null)
    const showRating = ref(false)
    const rating = ref(5)
    const submitting = ref(false)
    
    const typeNames = {
      'environment': '环境卫生',
      'facility': '设施维修',
      'noise': '噪音扰民',
      'parking': '停车管理',
      'security': '安全问题',
      'service': '服务态度',
      'other': '其他'
    }
    
    const statusNames = {
      'pending': '待处理',
      'processing': '处理中',
      'completed': '已完成'
    }
    
    const getTypeName = (type) => typeNames[type] || type
    const getStatusName = (status) => statusNames[status] || status
    
    const getTypeColor = (type) => {
      const colors = {
        'environment': 'success',
        'facility': 'warning',
        'noise': 'danger',
        'parking': 'primary',
        'security': 'danger',
        'service': 'warning',
        'other': 'default'
      }
      return colors[type] || 'default'
    }
    
    const getStatusColor = (status) => {
      const colors = {
        'pending': 'warning',
        'processing': 'primary',
        'completed': 'success'
      }
      return colors[status] || 'default'
    }
    
    const formatDateTime = (dateStr) => {
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN')
    }
    
    const loadDetail = async () => {
      try {
        const token = localStorage.getItem('token')
        const response = await fetch(`http://localhost:8088/api/v1/complaints/${route.params.id}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (!response.ok) {
          throw new Error('加载失败')
        }
        
        complaint.value = await response.json()
      } catch (error) {
        console.error('加载投诉详情失败:', error)
        showToast('加载失败')
      }
    }
    
    const submitRating = async () => {
      if (submitting.value) return
      
      try {
        submitting.value = true
        const token = localStorage.getItem('token')
        
        const response = await fetch(`http://localhost:8088/api/v1/complaints/${route.params.id}/rate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ rating: rating.value })
        })
        
        if (!response.ok) {
          throw new Error('评价失败')
        }
        
        showSuccessToast('评价成功')
        showRating.value = false
        await loadDetail()
      } catch (error) {
        console.error('评价失败:', error)
        showToast('评价失败，请重试')
      } finally {
        submitting.value = false
      }
    }
    
    const previewImages = (startIndex) => {
      showImagePreview({
        images: complaint.value.images,
        startPosition: startIndex,
        closeable: true
      })
    }
    
    onMounted(() => {
      loadDetail()
    })
    
    return {
      complaint,
      showRating,
      rating,
      submitting,
      getTypeName,
      getStatusName,
      getTypeColor,
      getStatusColor,
      formatDateTime,
      submitRating,
      previewImages
    }
  }
}
</script>

<style scoped>
.complaint-detail {
  background: #f7f8fa;
  min-height: 100vh;
  padding-bottom: 20px;
}

.content {
  padding-top: 46px;
}

.info-card,
.reply-card,
.eval-card {
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

.reply-content {
  font-size: 14px;
  color: #646566;
  line-height: 1.6;
  margin-bottom: 12px;
}

.reply-time {
  font-size: 12px;
  color: #969799;
}

.rating-popup {
  padding: 20px;
}

.popup-title {
  text-align: center;
  margin-bottom: 20px;
  font-size: 18px;
  font-weight: bold;
}

.rating-desc {
  text-align: center;
  font-size: 14px;
  color: #969799;
  margin-bottom: 16px;
}

.rating-popup .van-rate {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.submit-btn {
  margin-top: 16px;
}
</style>
