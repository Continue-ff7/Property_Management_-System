<template>
  <div class="notifications-page">
    <!-- 顶部导航 -->
    <van-nav-bar
      title="通知中心"
      left-arrow
      @click-left="$router.back()"
      fixed
      placeholder
    >
      <template #right>
        <van-button size="small" type="primary" @click="markAllRead">
          全部已读
        </van-button>
      </template>
    </van-nav-bar>
    
    <!-- 通知列表 -->
    <div class="content">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <div v-if="notifications.length > 0">
          <div 
            v-for="(notification, index) in notifications" 
            :key="index" 
            class="notification-item"
            :class="{ 'unread': !notification.read }"
            @click="handleClick(notification)"
          >
            <div class="notification-icon" :class="`type-${notification.type}`">
              <van-icon :name="getIcon(notification.type)" size="20" />
            </div>
            
            <div class="notification-content">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-message">{{ notification.message }}</div>
              <div class="notification-time">{{ formatTime(notification.time) }}</div>
            </div>
            
            <div v-if="!notification.read" class="unread-dot"></div>
          </div>
        </div>
        
        <van-empty v-else description="暂无通知" image="search" />
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
import { showToast } from 'vant'

export default {
  name: 'MaintenanceNotifications',
  setup() {
    const router = useRouter()
    const store = useStore()
    const refreshing = ref(false)
    const activeTabbar = ref(2)  // 通知tab
    const notifications = ref([])
    
    const todayCount = computed(() => store.state.maintenanceStats?.pending_orders || 0)
    const hasNewNotification = computed(() => store.state.hasNewNotification || false)
    
    // 加载通知列表（从 localStorage 或 Vuex 获取）
    const loadNotifications = () => {
      const stored = localStorage.getItem('maintenance_notifications')
      if (stored) {
        notifications.value = JSON.parse(stored)
      } else {
        // 示例通知
        notifications.value = [
          {
            type: 'new_workorder',
            title: '新工单分配',
            message: '您有新的维修工单需要处理',
            time: new Date().toISOString(),
            read: false,
            workorderId: null
          }
        ]
      }
    }
    
    const onRefresh = () => {
      loadNotifications()
      refreshing.value = false
    }
    
    const handleClick = (notification) => {
      // 标记为已读
      notification.read = true
      saveNotifications()
      
      // 根据类型跳转
      if (notification.type === 'new_workorder' && notification.workorderId) {
        router.push(`/maintenance/workorder/${notification.workorderId}`)
      } else if (notification.type === 'evaluation' && notification.workorderId) {
        router.push(`/maintenance/workorder/${notification.workorderId}`)
      }
    }
    
    const markAllRead = () => {
      notifications.value.forEach(n => n.read = true)
      saveNotifications()
      store.commit('SET_HAS_NEW_NOTIFICATION', false)
      showToast('全部标记为已读')
    }
    
    const saveNotifications = () => {
      localStorage.setItem('maintenance_notifications', JSON.stringify(notifications.value))
      // 更新 Vuex 状态
      const hasUnread = notifications.value.some(n => !n.read)
      store.commit('SET_HAS_NEW_NOTIFICATION', hasUnread)
    }
    
    const getIcon = (type) => {
      const iconMap = {
        'new_workorder': 'orders-o',
        'status_update': 'clock-o',
        'evaluation': 'star-o',
        'system': 'info-o'
      }
      return iconMap[type] || 'bell'
    }
    
    const formatTime = (timeString) => {
      const date = new Date(timeString)
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
        if (days === 1) return '昨天'
        if (days < 7) return `${days}天前`
        return date.toLocaleDateString()
      }
    }
    
    onMounted(() => {
      loadNotifications()
    })
    
    return {
      refreshing,
      activeTabbar,
      notifications,
      todayCount,
      hasNewNotification,
      onRefresh,
      handleClick,
      markAllRead,
      getIcon,
      formatTime
    }
  }
}
</script>

<style scoped>
.notifications-page {
  background: #f7f8fa;
  min-height: 100vh;
  padding-bottom: 50px;
}

.content {
  padding: 16px;
}

.notification-item {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  position: relative;
  transition: all 0.3s;
}

.notification-item.unread {
  background: #f0f9ff;
}

.notification-item:active {
  transform: scale(0.98);
}

.notification-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.type-new_workorder {
  background: #e8f4ff;
  color: #1989fa;
}

.type-status_update {
  background: #fff3e0;
  color: #ff9800;
}

.type-evaluation {
  background: #fff9e6;
  color: #ffa940;
}

.type-system {
  background: #f0f0f0;
  color: #646566;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-size: 15px;
  font-weight: bold;
  color: #323233;
  margin-bottom: 4px;
}

.notification-message {
  font-size: 14px;
  color: #646566;
  line-height: 1.5;
  margin-bottom: 4px;
}

.notification-time {
  font-size: 12px;
  color: #969799;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ee0a24;
  position: absolute;
  top: 16px;
  right: 16px;
}
</style>
