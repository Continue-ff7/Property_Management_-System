<template>
  <div class="workorders-page">
    <!-- 顶部用户信息 -->
    <div class="header">
      <div class="user-info">
        <van-image
          round
          width="40"
          height="40"
          src="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
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
              <van-tag 
                :color="getStatusColor(order.status)"
                text-color="#fff"
                plain
                size="medium"
              >
                {{ getStatusText(order.status) }}
              </van-tag>
            </div>
            
            <div class="card-body">
              <div class="location">
                {{ order.property_info }} · 面积 {{ order.area || '100' }} ㎡
              </div>
              <div class="tags">
                <van-tag size="medium">紧急程度：{{ getUrgencyText(order.urgency_level) }}</van-tag>
              </div>
              <div class="time">{{ formatDate(order.created_at) }}</div>
            </div>
            
            <div class="card-footer">
              <span class="status-text">
                <van-icon name="clock-o" />
                {{ getStatusDescription(order.status) }}
              </span>
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
      <van-tabbar-item to="/maintenance/tasks" icon="todo-list-o">
        任务
      </van-tabbar-item>
      <van-tabbar-item to="/maintenance/messages" icon="chat-o">
        消息
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
    
    const getStatusText = (status) => {
      const map = {
        pending: '待分配',
        assigned: '金色',
        in_progress: '绿色',
        completed: '蓝色'
      }
      return map[status] || status
    }
    
    const getStatusDescription = (status) => {
      const map = {
        pending: '待分配',
        assigned: '待处理',
        in_progress: '处理中',
        completed: '已完成'
      }
      return map[status] || status
    }
    
    const handleAction = (order) => {
      goToDetail(order.id)
    }
    
    const goToDetail = (id) => {
      router.push(`/maintenance/workorder/${id}`)
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
      workorders,
      loading,
      finished,
      refreshing,
      activeTab,
      activeTabbar,
      showFilter,
      stats,
      onLoad,
      onRefresh,
      handleAction,
      goToDetail,
      getStatusColor,
      getStatusText,
      getStatusDescription,
      getUrgencyText,
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

.card-body {
  padding: 12px 16px;
}

.location {
  font-size: 14px;
  color: #323233;
  margin-bottom: 8px;
  font-weight: 500;
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

.status-text {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #646566;
}

.status-text .van-icon {
  font-size: 14px;
}
</style>
