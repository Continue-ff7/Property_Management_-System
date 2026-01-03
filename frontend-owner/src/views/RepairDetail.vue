<template>
  <div class="repair-detail">
    <van-nav-bar
      title="维修详情"
      left-arrow
      @click-left="$router.back()"
      fixed
    />
    
    <div class="content">
      <!-- 维修信息卡片 -->
      <div class="info-card">
        <div class="order-header">
          <span class="order-number">工单号：{{ repair.order_number }}</span>
          <van-tag :type="getStatusType(repair.status)">
            {{ getStatusText(repair.status) }}
          </van-tag>
        </div>
        
        <van-cell-group>
          <van-cell title="报修地址" :value="repair.property_info" />
          <van-cell title="问题描述" :value="repair.description" />
          <van-cell title="紧急程度">
            <template #value>
              <van-tag :type="getUrgencyType(repair.urgency_level)">
                {{ getUrgencyText(repair.urgency_level) }}
              </van-tag>
            </template>
          </van-cell>
          <van-cell title="提交时间" :value="formatDate(repair.created_at)" />
        </van-cell-group>
        
        <!-- 报修图片 -->
        <div class="images-section" v-if="repair.images && repair.images.length > 0">
          <div class="section-title">问题图片</div>
          <div class="image-grid">
            <van-image
              v-for="(img, index) in repair.images"
              :key="index"
              width="100"
              height="100"
              :src="getImageUrl(img)"
              fit="cover"
              @click="previewImages(repair.images.map(i => getImageUrl(i)), index)"
            />
          </div>
        </div>
      </div>
      
      <!-- 维修进度 -->
      <div class="progress-card">
        <div class="card-title">
          <van-icon name="notes-o" />
          <span>维修进度</span>
        </div>
        
        <van-steps direction="vertical" :active="getProgressStep(repair.status, repair.rating)">
          <van-step>
            <h3>已提交</h3>
            <p>{{ formatDate(repair.created_at) }}</p>
            <p class="desc">您的报修申请已提交，请耐心等待</p>
          </van-step>
          <van-step>
            <h3>{{ repair.status === 'pending' ? '待分配' : '已分配' }}</h3>
            <p v-if="repair.assigned_at">{{ formatDate(repair.assigned_at) }}</p>
            <p class="desc" v-if="repair.maintenance_worker_name">
              维修人员：{{ repair.maintenance_worker_name }}
            </p>
          </van-step>
          <van-step>
            <h3>{{ repair.status === 'in_progress' ? '维修中' : (repair.status === 'completed' ? '已完成' : '待维修') }}</h3>
            <p v-if="repair.completed_at">{{ formatDate(repair.completed_at) }}</p>
            
            <!-- 维修完成图片 -->
            <div v-if="repair.repair_images && repair.repair_images.length > 0" class="repair-images">
              <p class="desc">维修完成照片：</p>
              <div class="image-grid">
                <van-image
                  v-for="(img, index) in repair.repair_images"
                  :key="index"
                  width="80"
                  height="80"
                  :src="getImageUrl(img)"
                  fit="cover"
                  @click="previewImages(repair.repair_images.map(i => getImageUrl(i)), index)"
                />
              </div>
            </div>
            <p class="desc" v-if="repair.status === 'completed' && !repair.rating">维修已完成，请评价服务质量</p>
          </van-step>
          <van-step>
            <h3>{{ repair.rating ? '已评价' : '待评价' }}</h3>
            <div v-if="repair.rating" class="rating-display">
              <van-rate :model-value="repair.rating" :size="16" readonly />
              <p class="desc" v-if="repair.comment">{{ repair.comment }}</p>
            </div>
            <p class="desc" v-else-if="repair.status !== 'completed'">维修完成后可进行评价</p>
          </van-step>
        </van-steps>
      </div>
      
      <!-- 维修人员信息 -->
      <div class="worker-card" v-if="repair.maintenance_worker_name">
        <div class="card-title">
          <van-icon name="user-o" />
          <span>维修人员</span>
        </div>
        
        <div class="worker-info">
          <van-image
            round
            width="50"
            height="50"
            :src="repair.maintenance_worker_avatar ? getImageUrl(repair.maintenance_worker_avatar) : 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg'"
          />
          <div class="worker-detail">
            <div class="name">{{ repair.maintenance_worker_name }}</div>
            <div class="phone">{{ repair.owner_phone || '暂无电话' }}</div>
          </div>
          <van-button type="primary" size="small" icon="chat-o" @click="goToChat">
            对话
          </van-button>
        </div>
      </div>
      
      <!-- 评价区域 -->
      <div class="eval-card" v-if="repair.status === 'completed' && !repair.rating">
        <van-button type="primary" block @click="showEvalDialog = true">
          评价维修服务
        </van-button>
      </div>
      
      <!-- 已评价 -->
      <div class="eval-card" v-if="repair.rating">
        <div class="card-title">
          <van-icon name="star-o" />
          <span>我的评价</span>
        </div>
        <van-rate v-model="repair.rating" :size="20" readonly />
        <p class="eval-comment">{{ repair.comment }}</p>
      </div>
    </div>
    
    <!-- 评价弹窗 -->
    <van-popup 
      :show="showEvalDialog" 
      @update:show="showEvalDialog = $event"
      position="bottom" 
      round 
      :style="{ height: '60%' }"
    >
      <div class="eval-content">
        <h3>评价维修服务</h3>
        
        <div class="rate-section">
          <span>服务评分</span>
          <van-rate v-model="evalForm.rating" :size="30" />
        </div>
        
        <van-field
          v-model="evalForm.comment"
          rows="4"
          autosize
          type="textarea"
          maxlength="200"
          placeholder="请输入评价内容"
          show-word-limit
        />
        
        <div style="padding: 16px;">
          <van-button type="primary" block @click="submitEval" :loading="submitting">
            提交评价
          </van-button>
        </div>
      </div>
    </van-popup>
    
    <!-- 对话弹窗（预留） -->
    <van-popup 
      :show="showChatDialog" 
      @update:show="showChatDialog = $event"
      position="bottom" 
      round 
      :style="{ height: '70%' }"
    >
      <div class="chat-content">
        <h3>与维修人员对话</h3>
        <van-empty description="对话功能开发中..." />
      </div>
    </van-popup>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { showToast, showSuccessToast, showImagePreview } from 'vant'
import { repairAPI } from '@/api'
import { getImageUrl } from '@/utils/request'

export default {
  name: 'RepairDetail',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()
    const repair = ref({})
    const showEvalDialog = ref(false)
    const showChatDialog = ref(false)
    const submitting = ref(false)
    const evalForm = ref({
      rating: 5,
      comment: ''
    })
    
    const loadRepairDetail = async () => {
      try {
        const repairs = await repairAPI.getMyRepairs()
        const repairId = parseInt(route.params.id)
        const found = repairs.find(r => r.id === repairId)
        if (found) {
          repair.value = found
        } else {
          showToast('工单不存在')
          router.back()
        }
      } catch (error) {
        console.error('加载失败:', error)
      }
    }
    
    const getProgressStep = (status, rating) => {
      // 如果已评价，显示第4步完成
      if (rating) {
        return 4
      }
      
      // 根据工单状态返回进度
      const map = {
        'pending': 0,      // 已提交
        'assigned': 1,     // 已分配
        'in_progress': 2,  // 维修中
        'completed': 3     // 已完成（待评价）
      }
      return map[status] || 0
    }
    
    const submitEval = async () => {
      if (!evalForm.value.comment) {
        showToast('请输入评价内容')
        return
      }
      
      submitting.value = true
      try {
        await repairAPI.evaluateRepair(repair.value.id, evalForm.value)
        showSuccessToast('评价成功')
        showEvalDialog.value = false
        loadRepairDetail()
      } catch (error) {
        console.error('评价失败:', error)
      } finally {
        submitting.value = false
      }
    }
    
    const previewImages = (images, index) => {
      showImagePreview({
        images,
        startPosition: index
      })
    }
    
    const goToChat = () => {
      router.push(`/repair/${repair.value.id}/chat`)
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
        pending: '待处理',
        assigned: '已分配',
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
        low: '低',
        medium: '中',
        high: '高',
        urgent: '紧急'
      }
      return map[level] || level
    }
    
    const formatDate = (date) => {
      if (!date) return '-'
      return new Date(date).toLocaleString('zh-CN')
    }
    
    onMounted(() => {
      loadRepairDetail()
    })
    
    // 监听Vuex中的工单状态更新通知
    watch(
      () => store.state.repairStatusUpdate,
      (newVal) => {
        if (newVal) {
          // 判断是否是当前工单的更新
          const currentRepairId = parseInt(route.params.id)
          if (newVal.id === currentRepairId) {
            console.log('当前工单状态更新，刷新详情')
            loadRepairDetail()  // 刷新详情数据
          }
        }
      }
    )
    
    return {
      repair,
      showEvalDialog,
      showChatDialog,
      submitting,
      evalForm,
      getProgressStep,
      submitEval,
      previewImages,
      goToChat,
      getStatusType,
      getStatusText,
      getUrgencyType,
      getUrgencyText,
      formatDate,
      getImageUrl
    }
  }
}
</script>

<style scoped>
.repair-detail {
  background: #f7f8fa;
  min-height: 100vh;
  padding-bottom: 20px;
}

.content {
  padding-top: 46px;
}

.info-card,
.progress-card,
.worker-card,
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

.repair-images {
  margin-top: 8px;
}

.repair-images .desc {
  font-size: 13px;
  color: #646566;
  margin-bottom: 8px;
}

.worker-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.worker-detail {
  flex: 1;
}

.worker-detail .name {
  font-size: 16px;
  font-weight: bold;
  color: #323233;
  margin-bottom: 4px;
}

.worker-detail .phone {
  font-size: 13px;
  color: #969799;
}

.eval-comment {
  margin-top: 12px;
  font-size: 14px;
  color: #646566;
  line-height: 1.6;
}

.eval-content,
.chat-content {
  padding: 20px;
}

.eval-content h3,
.chat-content h3 {
  text-align: center;
  margin-bottom: 20px;
}

.rate-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  margin-bottom: 16px;
}

:deep(.van-steps) {
  padding: 8px 0;
}

:deep(.van-step__circle-container) {
  background-color: white;
}

:deep(.van-step__title) {
  font-size: 14px;
  font-weight: bold;
}

.desc {
  font-size: 12px;
  color: #969799;
  margin-top: 4px;
}

.rating-display {
  margin-top: 8px;
}

.rating-display .desc {
  margin-top: 8px;
  color: #646566;
  line-height: 1.5;
}
</style>
