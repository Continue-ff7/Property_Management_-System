<template>
  <div class="repairs-page">
    <van-nav-bar title="我的报修" fixed>
      <template #right>
        <van-button type="primary" size="small" @click="$router.push('/repair/create')">
          报修
        </van-button>
      </template>
    </van-nav-bar>
    
    <div class="content">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="onLoad"
        >
          <div v-for="repair in repairs" :key="repair.id" class="repair-card" @click="goToDetail(repair.id)">
            <div class="card-header">
              <span class="order-number">#{{ repair.order_number }}</span>
              <van-tag :type="getStatusType(repair.status)">
                {{ getStatusText(repair.status) }}
              </van-tag>
            </div>
            
            <div class="card-body">
              <div class="repair-info">
                <div class="info-row">
                  <span class="label">报修地址</span>
                  <span class="value">{{ repair.property_info }}</span>
                </div>
                <div class="info-row">
                  <span class="label">问题描述</span>
                  <span class="value">{{ repair.description }}</span>
                </div>
                <div class="info-row">
                  <span class="label">紧急程度</span>
                  <van-tag :type="getUrgencyType(repair.urgency_level)">
                    {{ getUrgencyText(repair.urgency_level) }}
                  </van-tag>
                </div>
                <div class="info-row" v-if="repair.maintenance_worker_name">
                  <span class="label">维修人员</span>
                  <span class="value">{{ repair.maintenance_worker_name }}</span>
                </div>
                <div class="info-row">
                  <span class="label">创建时间</span>
                  <span class="value">{{ formatDate(repair.created_at) }}</span>
                </div>
              </div>
              
              <div class="repair-images" v-if="repair.images && repair.images.length > 0">
                <van-image
                  v-for="(img, index) in repair.images"
                  :key="index"
                  width="60"
                  height="60"
                  :src="getImageUrl(img)"
                  fit="cover"
                  @click="previewImages(repair.images.map(i => getImageUrl(i)), index)"
                />
              </div>
            </div>
            
            <div class="card-footer" v-if="repair.status === 'completed' && !repair.rating">
              <van-button type="primary" size="small" @click="showEvaluate(repair)">
                去评价
              </van-button>
            </div>
          </div>
          
          <van-empty v-if="repairs.length === 0" description="暂无报修记录" />
        </van-list>
      </van-pull-refresh>
    </div>
    
    <!-- 评价弹窗 -->
    <van-popup v-model="showEvalDialog" position="bottom" round :style="{ height: '60%' }">
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
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast, showImagePreview } from 'vant'
import { repairAPI } from '@/api'
import { getImageUrl } from '@/utils/request'

export default {
  name: 'Repairs',
  setup() {
    const router = useRouter()
    const repairs = ref([])
    const loading = ref(false)
    const finished = ref(false)
    const refreshing = ref(false)
    const showEvalDialog = ref(false)
    const submitting = ref(false)
    const currentRepair = ref(null)
    const evalForm = ref({
      rating: 5,
      comment: ''
    })
    
    const loadRepairs = async () => {
      try {
        const data = await repairAPI.getMyRepairs()
        repairs.value = data
        finished.value = true
      } catch (error) {
        console.error('加载失败:', error)
      }
    }
    
    const onLoad = () => {
      loadRepairs()
      loading.value = false
    }
    
    const onRefresh = () => {
      finished.value = false
      loading.value = true
      loadRepairs().finally(() => {
        refreshing.value = false
      })
    }
    
    const showEvaluate = (repair) => {
      currentRepair.value = repair
      evalForm.value = {
        rating: 5,
        comment: ''
      }
      showEvalDialog.value = true
    }
    
    const submitEval = async () => {
      if (!evalForm.value.comment) {
        showToast('请输入评价内容')
        return
      }
      
      submitting.value = true
      try {
        await repairAPI.evaluateRepair(currentRepair.value.id, evalForm.value)
        showSuccessToast('评价成功')
        showEvalDialog.value = false
        loadRepairs()
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
        low: '一般',
        medium: '紧急',
        high: '非常紧急'
      }
      return map[level] || level
    }
    
    const formatDate = (date) => {
      return new Date(date).toLocaleString('zh-CN')
    }
    
    const goToDetail = (repairId) => {
      router.push(`/repair/${repairId}`)
    }
    
    return {
      repairs,
      loading,
      finished,
      refreshing,
      showEvalDialog,
      submitting,
      evalForm,
      onLoad,
      onRefresh,
      showEvaluate,
      submitEval,
      previewImages,
      getStatusType,
      getStatusText,
      getUrgencyType,
      getUrgencyText,
      formatDate,
      goToDetail,
      getImageUrl
    }
  }
}
</script>

<style scoped>
.repairs-page {
  background: #f7f8fa;
  min-height: 100vh;
}

.content {
  padding-top: 46px;
}

.repair-card {
  background: white;
  margin: 12px 16px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.repair-card:active {
  transform: scale(0.98);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f2f3f5;
}

.order-number {
  font-size: 14px;
  font-weight: bold;
  color: #323233;
}

.card-body {
  padding: 16px;
}

.repair-info {
  margin-bottom: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.info-row .label {
  color: #969799;
  width: 80px;
  flex-shrink: 0;
}

.info-row .value {
  color: #323233;
  flex: 1;
  text-align: right;
}

.repair-images {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.card-footer {
  padding: 12px 16px;
  border-top: 1px solid #f2f3f5;
  text-align: right;
}

.eval-content {
  padding: 20px;
}

.eval-content h3 {
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
</style>
