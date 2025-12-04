<template>
  <div class="profile-page">
    <van-nav-bar title="我的" fixed />
    
    <div class="content">
      <!-- 用户信息卡片 -->
      <div class="user-card">
        <van-image
          round
          width="70"
          height="70"
          src="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
        />
        <div class="user-info">
          <div class="name">{{ userInfo.name || '业主' }}</div>
          <div class="phone">{{ userInfo.phone || '未绑定手机' }}</div>
        </div>
      </div>
      
      <!-- 房产信息 -->
      <van-cell-group inset title="我的房产">
        <van-cell
          v-for="property in properties"
          :key="property.id"
          :title="`${property.building_name} ${property.unit}单元 ${property.room_number}`"
          :label="`面积：${property.area}㎡`"
        >
          <template #icon>
            <van-icon name="home-o" size="20" color="#1989fa" style="margin-right: 12px;" />
          </template>
        </van-cell>
        <van-empty v-if="properties.length === 0" description="暂无房产" />
      </van-cell-group>
      
      <!-- 功能菜单 -->
      <van-cell-group inset title="功能设置">
        <van-cell title="账单记录" is-link @click="$router.push('/bills')">
          <template #icon>
            <van-icon name="balance-list-o" size="20" style="margin-right: 12px;" />
          </template>
        </van-cell>
        <van-cell title="报修记录" is-link @click="$router.push('/repairs')">
          <template #icon>
            <van-icon name="service-o" size="20" style="margin-right: 12px;" />
          </template>
        </van-cell>
        <van-cell title="公告通知" is-link @click="$router.push('/announcements')">
          <template #icon>
            <van-icon name="volume-o" size="20" style="margin-right: 12px;" />
          </template>
        </van-cell>
      </van-cell-group>
      
      <van-cell-group inset title="账户管理">
        <van-cell title="修改密码" is-link>
          <template #icon>
            <van-icon name="lock" size="20" style="margin-right: 12px;" />
          </template>
        </van-cell>
        <van-cell title="关于我们" is-link>
          <template #icon>
            <van-icon name="info-o" size="20" style="margin-right: 12px;" />
          </template>
        </van-cell>
      </van-cell-group>
      
      <div style="margin: 24px 16px;">
        <van-button type="danger" block @click="handleLogout">退出登录</van-button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { showConfirmDialog, showSuccessToast } from 'vant'
import { ownerAPI } from '@/api'

export default {
  name: 'Profile',
  setup() {
    const router = useRouter()
    const store = useStore()
    const userInfo = computed(() => store.state.userInfo)
    const properties = ref([])
    
    const loadProperties = async () => {
      try {
        const data = await ownerAPI.getMyProperties()
        properties.value = data
      } catch (error) {
        console.error('加载房产失败:', error)
      }
    }
    
    const handleLogout = async () => {
      try {
        await showConfirmDialog({
          title: '提示',
          message: '确定要退出登录吗？'
        })
        
        store.dispatch('logout')
        showSuccessToast('已退出登录')
        router.replace('/login')
      } catch (error) {
        // 用户取消
      }
    }
    
    onMounted(() => {
      loadProperties()
    })
    
    return {
      userInfo,
      properties,
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
  margin: 16px;
  padding: 24px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 16px;
  color: white;
}

.user-info .name {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 8px;
}

.user-info .phone {
  font-size: 14px;
  opacity: 0.9;
}
</style>
