<template>
  <div class="announcements-page">
    <van-nav-bar
      title="公告通知"
      left-arrow
      @click-left="$router.back()"
      fixed
    />
    
    <div class="content">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="onLoad"
        >
          <div v-for="item in announcements" :key="item.id" class="ann-card">
            <h3 class="title">{{ item.title }}</h3>
            <div class="content-text">{{ item.content }}</div>
            <div class="footer">
              <span class="publisher">{{ item.publisher_name }}</span>
              <span class="time">{{ formatDate(item.created_at) }}</span>
            </div>
          </div>
          
          <van-empty v-if="announcements.length === 0" description="暂无公告" />
        </van-list>
      </van-pull-refresh>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { announcementAPI } from '@/api'

export default {
  name: 'Announcements',
  setup() {
    const announcements = ref([])
    const loading = ref(false)
    const finished = ref(false)
    const refreshing = ref(false)
    
    const loadAnnouncements = async () => {
      try {
        const data = await announcementAPI.getList()
        announcements.value = data
        finished.value = true
      } catch (error) {
        console.error('加载失败:', error)
      }
    }
    
    const onLoad = () => {
      loadAnnouncements()
      loading.value = false
    }
    
    const onRefresh = () => {
      finished.value = false
      loading.value = true
      loadAnnouncements().finally(() => {
        refreshing.value = false
      })
    }
    
    const formatDate = (date) => {
      return new Date(date).toLocaleString('zh-CN')
    }
    
    return {
      announcements,
      loading,
      finished,
      refreshing,
      onLoad,
      onRefresh,
      formatDate
    }
  }
}
</script>

<style scoped>
.announcements-page {
  background: #f7f8fa;
  min-height: 100vh;
}

.content {
  padding-top: 46px;
}

.ann-card {
  background: white;
  margin: 12px 16px;
  padding: 16px;
  border-radius: 8px;
}

.title {
  font-size: 16px;
  font-weight: bold;
  color: #323233;
  margin-bottom: 12px;
}

.content-text {
  font-size: 14px;
  color: #646566;
  line-height: 1.6;
  margin-bottom: 12px;
}

.footer {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #969799;
}
</style>
