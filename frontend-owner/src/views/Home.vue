<template>
  <div class="home-page">
    <!-- 头部信息 -->
    <div class="header">
      <div class="user-info">
        <van-image
          round
          width="60"
          height="60"
          :src="getImageUrl(userInfo.avatar) || 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg'"
        />
        <div class="info">
          <div class="name">{{ userInfo.name || userInfo.username || '业主' }}</div>
          <div class="property">{{ propertyInfo }}</div>
        </div>
      </div>
      
      <van-icon name="bell" size="24" />
    </div>
    
    <!-- 功能菜单 -->
    <div class="menu-grid">
      <div class="menu-item" @click="goTo('/bills')">
        <van-icon name="balance-list-o" size="28" color="#4fc08d" />
        <span>我的账单</span>
      </div>
      <div class="menu-item" @click="goTo('/repairs')">
        <van-icon name="service-o" size="28" color="#f56c6c" />
        <span>维修工单</span>
      </div>
      <div class="menu-item" @click="goTo('/announcements')">
        <van-icon name="volume-o" size="28" color="#409eff" />
        <span>公告通知</span>
      </div>
      <div class="menu-item" @click="goTo('/complaints')">
        <van-icon name="chat-o" size="28" color="#ff6b6b" />
        <span>物业投诉</span>
      </div>
      <div class="menu-item" @click="goTo('/repair/create')">
        <van-icon name="add-o" size="28" color="#909399" />
        <span>报修申请</span>
      </div>
      <div class="menu-item" @click="goTo('/invoices')">
        <van-icon name="description" size="28" color="#67c23a" />
        <span>发票下载</span>
      </div>
      <div class="menu-item" @click="goTo('/ai-assistant')">
        <van-icon name="chat-o" size="28" color="#1989fa" />
        <span>AI助手</span>
      </div>
      <div class="menu-item" @click="goTo('/profile')">
        <van-icon name="setting-o" size="28" color="#a0a0a0" />
        <span>用户设置</span>
      </div>
    </div>
    
    <!-- 待办提醒 -->
    <div class="section">
      <div class="section-title">
        <span>待办提醒</span>
      </div>
      
      <van-cell-group inset>
        <van-cell
          v-for="(item, index) in todos"
          :key="index"
          :title="item.title"
          :value="item.value"
          is-link
          @click="handleTodoClick(item)"
        >
          <template #icon>
            <van-icon :name="item.icon" :color="item.color" size="20" style="margin-right: 10px;" />
          </template>
        </van-cell>
      </van-cell-group>
    </div>
    
    <!-- 小区公告 -->
    <div class="section">
      <div class="section-title">
        <span>小区公告</span>
        <van-button size="small" type="primary" @click="goTo('/announcements')">
          查看更多
        </van-button>
      </div>
      
      <van-cell-group inset>
        <van-cell
          v-for="item in announcements"
          :key="item.id"
          :title="item.title"
          :label="item.created_at"
          is-link
        />
        <van-empty v-if="announcements.length === 0" description="暂无公告" />
      </van-cell-group>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ownerAPI, billAPI, repairAPI, announcementAPI } from '@/api'
import { getImageUrl } from '@/utils/request'

export default {
  name: 'Home',
  setup() {
    const router = useRouter()
    const store = useStore()
    const userInfo = computed(() => store.state.userInfo)
    const properties = ref([])
    const announcements = ref([])
    const todos = ref([])
    
    const propertyInfo = computed(() => {
      if (properties.value.length > 0) {
        const p = properties.value[0]
        return `${p.building_name} ${p.unit}单元 ${p.room_number}`
      }
      return '暂无房产'
    })
    
    const loadData = async () => {
      try {
        // 加载房产信息
        const props = await ownerAPI.getMyProperties()
        properties.value = props
        
        // 加载待办事项
        const [unpaidBills, pendingRepairs] = await Promise.all([
          billAPI.getMyBills({ status: 'unpaid', limit: 1 }),
          repairAPI.getMyRepairs({ status: 'pending', limit: 1 })
        ])
        
        todos.value = []
        if (unpaidBills.length > 0) {
          todos.value.push({
            title: '未缴费账单',
            value: `主房产费 ¥${unpaidBills[0].amount}`,
            icon: 'balance-list',
            color: '#f56c6c',
            type: 'bill'
          })
        }
        
        if (pendingRepairs.length > 0) {
          todos.value.push({
            title: '待处理报修',
            value: `请耐心等待物业处理`,
            icon: 'service',
            color: '#409eff',
            type: 'repair'
          })
        }
        
        // 加载公告
        const anns = await announcementAPI.getList({ limit: 3 })
        announcements.value = anns
      } catch (error) {
        console.error('加载失败:', error)
      }
    }
    
    const goTo = (path) => {
      router.push(path)
    }
    
    const handleTodoClick = (item) => {
      if (item.type === 'bill') {
        router.push('/bills')
      } else if (item.type === 'repair') {
        router.push('/repairs')
      }
    }
    
    onMounted(() => {
      loadData()
    })
    
    // 监听Vuex中的工单状态更新通知
    watch(
      () => store.state.repairStatusUpdate,
      (newVal) => {
        if (newVal) {
          // 收到工单状态更新，刷新待办事项
          loadData()
        }
      }
    )
    
    return {
      userInfo,
      propertyInfo,
      todos,
      announcements,
      getImageUrl,
      goTo,
      handleTodoClick
    }
  }
}
</script>

<style scoped>
.home-page {
  background-color: #f7f8fa;
  min-height: 100vh;
  padding-bottom: 20px;
}

.header {
  background: linear-gradient(135deg, #4A90E2 0%, #5CA4E8 100%);
  padding: 20px 16px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info .name {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 4px;
}

.info .property {
  font-size: 13px;
  opacity: 0.9;
}

.menu-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 20px 16px;
  background: white;
  margin: -20px 16px 16px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.menu-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 0;
  cursor: pointer;
}

.menu-item span {
  font-size: 12px;
  color: #646566;
}

.section {
  padding: 0 16px;
  margin-top: 16px;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  font-size: 16px;
  font-weight: bold;
  color: #323233;
}
</style>
