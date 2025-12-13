<template>
  <div class="profile-page">
    <van-nav-bar
      title="个人中心"
      fixed
    />
    
    <div class="content">
      <!-- 个人信息卡片 -->
      <div class="user-card">
        <van-image
          round
          width="60"
          height="60"
          src="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
        />
        <div class="user-info">
          <div class="name">{{ userInfo.name || userInfo.username }}</div>
          <div class="role">维修人员</div>
        </div>
      </div>
      
      <!-- 统计信息 -->
      <div class="stats-grid">
        <div class="stat-item">
          <div class="value">{{ stats.total }}</div>
          <div class="label">总工单</div>
        </div>
        <div class="stat-item">
          <div class="value">{{ stats.completed }}</div>
          <div class="label">已完成</div>
        </div>
        <div class="stat-item">
          <div class="value">{{ stats.in_progress }}</div>
          <div class="label">进行中</div>
        </div>
      </div>
      
      <!-- 功能列表 -->
      <van-cell-group inset style="margin-top: 16px;">
        <van-cell title="我的工单" is-link @click="goTo('/maintenance/workorders')" />
        <van-cell title="个人信息" is-link />
        <van-cell title="系统设置" is-link />
      </van-cell-group>
      
      <div style="margin: 24px 16px;">
        <van-button block @click="handleLogout">
          退出登录
        </van-button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { showConfirmDialog, showSuccessToast } from 'vant'
import { maintenanceWorkorderAPI } from '@/api'

export default {
  name: 'MaintenanceProfile',
  setup() {
    const router = useRouter()
    const store = useStore()
    const userInfo = computed(() => store.state.userInfo)
    const stats = reactive({
      total: 0,
      completed: 0,
      in_progress: 0
    })
    
    const loadStats = async () => {
      try {
        const data = await maintenanceWorkorderAPI.getMyWorkorders()
        stats.total = data.length
        stats.completed = data.filter(w => w.status === 'completed').length
        stats.in_progress = data.filter(w => w.status === 'in_progress').length
      } catch (error) {
        console.error('加载统计失败:', error)
      }
    }
    
    const goTo = (path) => {
      router.push(path)
    }
    
    const handleLogout = async () => {
      try {
        await showConfirmDialog({
          title: '提示',
          message: '确定要退出登录吗？'
        })
        
        store.dispatch('logout')
        showSuccessToast('已退出登录')
        router.push('/login')
      } catch (error) {
        // 取消操作
      }
    }
    
    onMounted(() => {
      loadStats()
    })
    
    return {
      userInfo,
      stats,
      goTo,
      handleLogout
    }
  }
}
</script>

<style scoped>
.profile-page {
  background: #f7f8fa;
  min-height: 100vh;
}

.content {
  padding-top: 46px;
  padding-bottom: 20px;
}

.user-card {
  background: linear-gradient(135deg, #4A90E2 0%, #5CA4E8 100%);
  margin: 12px 16px;
  padding: 24px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
}

.user-info {
  color: white;
}

.user-info .name {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 4px;
}

.user-info .role {
  font-size: 13px;
  opacity: 0.9;
}

.stats-grid {
  background: white;
  margin: 16px 16px;
  padding: 20px;
  border-radius: 12px;
  display: flex;
  justify-content: space-around;
}

.stat-item {
  text-align: center;
}

.stat-item .value {
  font-size: 24px;
  font-weight: bold;
  color: #4A90E2;
  margin-bottom: 4px;
}

.stat-item .label {
  font-size: 13px;
  color: #969799;
}
</style>
