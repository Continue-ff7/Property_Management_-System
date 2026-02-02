<template>
  <div class="workorders-page">
    <!-- 顶部用户信息 -->
    <div class="header">
      <div class="user-info">
        <van-image
          round
          width="40"
          height="40"
          :src="avatarUrl"
        />
        <div class="info">
          <div class="name">{{ userInfo.name || userInfo.username }}</div>
          <div class="role">维修工</div>
        </div>
      </div>
      <van-icon name="search" size="20" />
    </div>
    
    <div class="content">
      <!-- 标题和筛选 -->
      <div class="title-bar">
        <h2>我的工单</h2>
        <van-button size="small" icon="filter-o" @click="showFilter = true">
          筛选
        </van-button>
      </div>
      
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="onLoad"
        >
          <div 
            v-for="order in workorders" 
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
                {{ getUrgencyBadgeText(order.urgency_level) }}
              </div>
            </div>
            
            <div class="card-body">
              <div class="location">
                {{ order.property_info }}
              </div>
              <div class="description">
                {{ order.description }}
              </div>
              <div class="time">{{ formatDate(order.created_at) }}</div>
            </div>
            
            <div class="card-footer">
              <div class="status-info">
                <span 
                  class="status-dot"
                  :class="`status-${order.status}`"
                ></span>
                <span class="status-text">{{ getStatusDescription(order) }}</span>
              </div>
              <van-button 
                type="primary" 
                size="small"
                @click.stop="handleAction(order)"
              >
                查看详情
              </van-button>
            </div>
          </div>
          
          <van-empty v-if="workorders.length === 0" description="暂无工单" />
        </van-list>
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
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { maintenanceWorkorderAPI } from '@/api'
import { getImageUrl } from '@/utils/request'

export default {
  name: 'MaintenanceWorkorders',
  setup() {
    const router = useRouter()
    const store = useStore()
    const userInfo = computed(() => store.state.userInfo)
    const workorders = ref([])
    const loading = ref(false)
    const finished = ref(false)
    const refreshing = ref(false)
    const activeTab = ref('all')
    const activeTabbar = ref(0)
    const showFilter = ref(false)
    const stats = reactive({
      pending: 0,
      in_progress: 0,
      completed: 0
    })
    
    // ✅ 新增：今日待办数量（从 Vuex 获取）
    const todayCount = computed(() => store.state.maintenanceStats?.pending_orders || 0)
    
    // ✅ 新增：是否有新通知
    const hasNewNotification = computed(() => store.state.hasNewNotification || false)
    
    // 计算头像URL
    const avatarUrl = computed(() => {
      if (userInfo.value?.avatar) {
        return getImageUrl(userInfo.value.avatar)
      }
      return 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg'
    })
    
    const loadWorkorders = async () => {
      try {
        const params = {}
        if (activeTab.value !== 'all') {
          params.status = activeTab.value
        }
        
        const data = await maintenanceWorkorderAPI.getMyWorkorders(params)
        workorders.value = data
        
        // 更新统计
        stats.pending = data.filter(w => w.status === 'assigned').length
        stats.in_progress = data.filter(w => w.status === 'in_progress').length
        stats.completed = data.filter(w => w.status === 'completed').length
        
        finished.value = true
      } catch (error) {
        console.error('加载失败:', error)
      }
    }
    
    const onLoad = () => {
      loadWorkorders()
      loading.value = false
    }
    
    const onRefresh = () => {
      finished.value = false
      loading.value = true
      loadWorkorders().finally(() => {
        refreshing.value = false
      })
    }
    
    const getStatusColor = (status) => {
      const map = {
        pending: '#FFD700',
        assigned: '#FFD700',  // 金色
        in_progress: '#07C160',  // 绿色
        completed: '#1989FA'  // 蓝色
      }
      return map[status] || '#dcdee0'
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
    
    const getStatusDescription = (order) => {
      return getStatusText(order)  // 复用相同逻辑
    }
    
    const handleAction = (order) => {
      goToDetail(order.id)
    }
    
    const goToDetail = (id) => {
      router.push(`/maintenance/workorder/${id}`)
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
    
    const getUrgencyBadgeText = (level) => {
      const map = {
        low: '低',
        medium: '中',
        high: '高',
        urgent: '紧急'
      }
      return map[level] || '低'
    }
    
    const formatDate = (date) => {
      if (!date) return ''
      const d = new Date(date)
      const month = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      const hour = String(d.getHours()).padStart(2, '0')
      const minute = String(d.getMinutes()).padStart(2, '0')
      return `${month}-${day} ${hour}:${minute}`
    }
    
    onMounted(() => {
      loadWorkorders()
    })
    
    // 监听Vuex中的新工单通知
    watch(
      () => store.state.newWorkorder,
      (newVal) => {
        if (newVal) {
          // 收到新工单，刷新列表
          loadWorkorders()
        }
      }
    )
    
    // 监听Vuex中的工单被删除通知
    watch(
      () => store.state.workorderDeleted,
      (newVal) => {
        if (newVal) {
          // 收到工单被删除，刷新列表
          loadWorkorders()
        }
      }
    )
    
    return {
      userInfo,
      avatarUrl,
      workorders,
      loading,
      finished,
      refreshing,
      activeTab,
      activeTabbar,
      showFilter,
      stats,
      todayCount,  // ✅ 新增
      hasNewNotification,  // ✅ 新增
      onLoad,
      onRefresh,
      handleAction,
      goToDetail,
      getStatusColor,
      getStatusText,
      getStatusDescription,
      getUrgencyText,
      getUrgencyBadgeText,
      formatDate
    }
  }
}
</script>

<style scoped>
.workorders-page {
  background: #f7f8fa;
  min-height: 100vh;
  padding-bottom: 50px;
}

.header {
  background: white;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f2f3f5;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info .name {
  font-size: 16px;
  font-weight: bold;
  color: #323233;
}

.info .role {
  font-size: 12px;
  color: #969799;
  margin-top: 2px;
}

.content {
  padding: 12px 0;
}

.title-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px 12px;
}

.title-bar h2 {
  margin: 0;
  font-size: 20px;
  color: #323233;
}

.workorder-card {
  background: white;
  margin: 8px 16px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  transition: all 0.3s;
}

.workorder-card:active {
  transform: scale(0.98);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #f2f3f5;
}

.order-number {
  font-size: 15px;
  font-weight: 600;
  color: #323233;
}

/* 紧急程度徽章 - 圆角标签样式 */
.urgency-badge {
  padding: 4px 12px;
  border-radius: 12px 0 0 12px;
  font-size: 12px;
  font-weight: 500;
  color: white;
  position: relative;
  min-width: 50px;
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

.card-body {
  padding: 12px 16px;
}

.location {
  font-size: 14px;
  color: #323233;
  margin-bottom: 8px;
  font-weight: 500;
}

.description {
  font-size: 13px;
  color: #646566;
  margin-bottom: 8px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.tags {
  margin-bottom: 8px;
}

.time {
  font-size: 12px;
  color: #969799;
}

.card-footer {
  padding: 10px 16px;
  border-top: 1px solid #f2f3f5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafafa;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.status-assigned {
  background: #FF9500;
}

.status-dot.status-in_progress {
  background: #4A90E2;
}

.status-dot.status-completed {
  background: #52C41A;
}

.status-dot.status-cancelled {
  background: #999999;
}

.status-dot.status-pending {
  background: #FF9500;
}

.status-text {
  font-size: 13px;
  color: #646566;
}

.status-text .van-icon {
  font-size: 14px;
}
</style>
