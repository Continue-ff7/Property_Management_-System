<template>
  <div class="today-page">
    <!-- 顶部导航 -->
    <van-nav-bar
      title="今日任务"
      left-arrow
      @click-left="$router.back()"
      fixed
      placeholder
    />
    
    <!-- 统计卡片 -->
    <div class="stats-card">
      <div class="stat-item">
        <div class="stat-value">{{ stats.pending_orders || 0 }}</div>
        <div class="stat-label">待处理</div>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.in_progress_orders || 0 }}</div>
        <div class="stat-label">处理中</div>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.completed_orders || 0 }}</div>
        <div class="stat-label">今日完成</div>
      </div>
    </div>
    
    <!-- 今日待办列表 -->
    <div class="content">
      <div class="section-title">
        <van-icon name="calendar-o" />
        <span>今日待办 ({{ pendingWorkorders.length }})</span>
      </div>
      
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <div v-if="pendingWorkorders.length > 0">
          <div 
            v-for="order in pendingWorkorders" 
            :key="order.id" 
            class="workorder-card"
            @click="goToDetail(order.id)"
          >
            <div class="card-header">
              <span class="order-number">{{ order.order_number }}</span>
              <div 
                class="urgency-badge"
                :class="`urgency-${order.urgency_level}`"
              >
                {{ getUrgencyText(order.urgency_level) }}
              </div>
            </div>
            
            <div class="card-body">
              <div class="location">
                <van-icon name="location-o" />
                {{ order.property_info }}
              </div>
              <div class="description">{{ order.description }}</div>
              <div class="time">{{ formatDate(order.created_at) }}</div>
            </div>
            
            <div class="card-footer">
              <van-button 
                type="primary" 
                size="small"
                @click.stop="handleStart(order)"
              >
                开始处理
              </van-button>
            </div>
          </div>
        </div>
        
        <van-empty v-else description="今日暂无待办任务" image="search" />
      </van-pull-refresh>
    </div>
    
    <!-- 底部Tab导航 -->
    <van-tabbar v-model="activeTabbar" route>
      <van-tabbar-item to="/maintenance/workorders" icon="orders-o">
        工单
      </van-tabbar-item>
      <van-tabbar-item to="/maintenance/today" icon="calendar-o" :badge="todayCount > 0 ? todayCount : ''">
        今日
      </van-tabbar-item>
      <van-tabbar-item to="/maintenance/notifications" icon="bell" :dot="hasNewNotification">
        通知
      </van-tabbar-item>
      <van-tabbar-item to="/maintenance/profile" icon="user-o">
        我的
      </van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { maintenanceWorkorderAPI } from '@/api'
import { showDialog } from 'vant'

export default {
  name: 'MaintenanceToday',
  setup() {
    const router = useRouter()
    const store = useStore()
    const refreshing = ref(false)
    const activeTabbar = ref(1)  // 今日tab
    
    // 从 Vuex 获取统计数据
    const stats = computed(() => store.state.maintenanceStats || {})
    const pendingWorkorders = ref([])
    
    // 今日待办数量
    const todayCount = computed(() => store.state.maintenanceStats?.pending_orders || 0)
    const hasNewNotification = computed(() => store.state.hasNewNotification || false)
    
    // 加载待处理工单
    const loadPendingWorkorders = async () => {
      try {
        const data = await maintenanceWorkorderAPI.getMyWorkorders({ status: 'assigned' })
        // 按紧急程度排序：urgent > high > medium > low
        const urgencyOrder = { 'urgent': 0, 'high': 1, 'medium': 2, 'low': 3 }
        pendingWorkorders.value = data.sort((a, b) => {
          return urgencyOrder[a.urgency_level] - urgencyOrder[b.urgency_level]
        })
      } catch (error) {
        console.error('加载失败:', error)
      }
    }
    
    const onRefresh = async () => {
      await loadPendingWorkorders()
      // 刷新统计数据
      await store.dispatch('loadMaintenanceStats')
      refreshing.value = false
    }
    
    const handleStart = (order) => {
      showDialog({
        title: '开始处理',
        message: `确认开始处理工单 ${order.order_number}？`,
        showCancelButton: true
      }).then(async () => {
        try {
          await maintenanceWorkorderAPI.startWorkorder(order.id)
          await loadPendingWorkorders()
          await store.dispatch('loadMaintenanceStats')
        } catch (error) {
          console.error('开始处理失败:', error)
        }
      })
    }
    
    const goToDetail = (id) => {
      router.push(`/maintenance/workorder/${id}`)
    }
    
    const getUrgencyText = (level) => {
      const map = {
        'low': '低',
        'medium': '中',
        'high': '高',
        'urgent': '紧急'
      }
      return map[level] || level
    }
    
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      const now = new Date()
      const diff = now - date
      const hours = Math.floor(diff / 3600000)
      
      if (hours < 1) {
        const minutes = Math.floor(diff / 60000)
        return `${minutes}分钟前`
      } else if (hours < 24) {
        return `${hours}小时前`
      } else {
        const days = Math.floor(hours / 24)
        return `${days}天前`
      }
    }
    
    onMounted(() => {
      loadPendingWorkorders()
      // 加载统计数据
      store.dispatch('loadMaintenanceStats')
    })
    
    return {
      refreshing,
      activeTabbar,
      stats,
      pendingWorkorders,
      todayCount,
      hasNewNotification,
      onRefresh,
      handleStart,
      goToDetail,
      getUrgencyText,
      formatDate
    }
  }
}
</script>

<style scoped>
.today-page {
  background: #f7f8fa;
  min-height: 100vh;
  padding-bottom: 50px;
}

.stats-card {
  background: linear-gradient(135deg, #1989fa 0%, #1677ff 100%);
  margin: 16px;
  padding: 20px;
  border-radius: 12px;
  display: flex;
  justify-content: space-around;
  align-items: center;
  box-shadow: 0 4px 12px rgba(25, 137, 250, 0.4);
}

.stat-item {
  text-align: center;
  color: white;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.3);
}

.content {
  padding: 0 16px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: bold;
  color: #323233;
  margin: 16px 0 12px;
}

.workorder-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s;
}

.workorder-card:active {
  transform: scale(0.98);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.order-number {
  font-size: 14px;
  font-weight: bold;
  color: #323233;
}

.urgency-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.urgency-low {
  background: #e8f5e9;
  color: #4caf50;
}

.urgency-medium {
  background: #fff3e0;
  color: #ff9800;
}

.urgency-high {
  background: #ffebee;
  color: #f44336;
}

.urgency-urgent {
  background: #f44336;
  color: white;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.card-body {
  margin-bottom: 12px;
}

.location {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #646566;
  margin-bottom: 8px;
}

.description {
  font-size: 14px;
  color: #323233;
  margin-bottom: 8px;
  line-height: 1.5;
}

.time {
  font-size: 12px;
  color: #969799;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
}
</style>
