<template>
  <div class="complaints-page">
    <van-nav-bar 
      title="物业投诉" 
      left-arrow
      @click-left="$router.back()"
      fixed 
    />
    
    <div class="content">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <div class="complaints-list">
          <!-- 空状态 -->
          <van-empty v-if="complaints.length === 0" description="暂无投诉记录" />
          
          <!-- 投诉卡片 -->
          <div 
            v-for="complaint in complaints" 
            :key="complaint.id" 
            class="complaint-card"
            @click="goToDetail(complaint.id)"
          >
            <div class="complaint-header">
              <van-tag :type="getTypeColor(complaint.type)">{{ getTypeName(complaint.type) }}</van-tag>
              <van-tag :type="getStatusColor(complaint.status)">{{ getStatusName(complaint.status) }}</van-tag>
            </div>
            
            <div class="complaint-content">
              {{ complaint.content }}
            </div>
            
            <div class="complaint-footer">
              <span class="time">{{ formatTime(complaint.created_at) }}</span>
              <van-icon name="arrow" />
            </div>
          </div>
        </div>
      </van-pull-refresh>
    </div>
    
    <!-- 固定底部按钮 -->
    <div class="footer-btn">
      <van-button
        type="primary"
        size="large"
        icon="plus"
        @click="goToCreate"
        block
      >
        提交投诉
      </van-button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { showToast } from 'vant'

export default {
  name: 'Complaints',
  setup() {
    const router = useRouter()
    const store = useStore()
    const complaints = ref([])
    const refreshing = ref(false)
    
    // 投诉类型映射
    const typeNames = {
      'environment': '环境卫生',
      'facility': '设施维修',
      'noise': '噪音扰民',
      'parking': '停车管理',
      'security': '安全问题',
      'service': '服务态度',
      'other': '其他'
    }
    
    // 状态映射
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
    
    const formatTime = (dateStr) => {
      const date = new Date(dateStr)
      const now = new Date()
      const diff = now - date
      const minutes = Math.floor(diff / 60000)
      const hours = Math.floor(diff / 3600000)
      const days = Math.floor(diff / 86400000)
      
      if (minutes < 60) return `${minutes}分钟前`
      if (hours < 24) return `${hours}小时前`
      if (days < 7) return `${days}天前`
      
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${month}-${day}`
    }
    
    const loadComplaints = async () => {
      try {
        const token = localStorage.getItem('token')
        const response = await fetch('http://localhost:8088/api/v1/complaints', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (!response.ok) {
          throw new Error('加载失败')
        }
        
        complaints.value = await response.json()
      } catch (error) {
        console.error('加载投诉列表失败:', error)
        showToast('加载失败')
      }
    }
    
    const onRefresh = async () => {
      await loadComplaints()
      refreshing.value = false
    }
    
    const goToCreate = () => {
      router.push('/complaint/create')
    }
    
    const goToDetail = (id) => {
      router.push(`/complaint/${id}`)
    }
    
    // ✅ 监听投诉更新通知
    const complaintUpdate = computed(() => store.state.complaintUpdate)
    
    watch(complaintUpdate, (newVal) => {
      if (newVal) {
        console.log('收到投诉更新通知，刷新列表')
        loadComplaints()
      }
    })
    
    onMounted(() => {
      loadComplaints()
    })
    
    return {
      complaints,
      refreshing,
      getTypeName,
      getStatusName,
      getTypeColor,
      getStatusColor,
      formatTime,
      onRefresh,
      goToCreate,
      goToDetail
    }
  }
}
</script>

<style scoped>
.complaints-page {
  min-height: 100vh;
  background-color: #f7f8fa;
  padding-bottom: 70px;
}

.content {
  padding: 56px 16px 20px;
}

.complaints-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.complaint-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.3s;
}

.complaint-card:active {
  transform: scale(0.98);
}

.complaint-header {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.complaint-content {
  font-size: 14px;
  color: #323233;
  line-height: 1.6;
  margin-bottom: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.complaint-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.time {
  font-size: 12px;
  color: #969799;
}

.footer-btn {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 10px 16px;
  background: white;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  z-index: 999;
}
</style>
