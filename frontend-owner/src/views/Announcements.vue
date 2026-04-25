<template>
  <div class="announcements-page">
    <van-nav-bar
      title="小区公告"
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
          <div 
            v-for="item in announcements" 
            :key="item.id" 
            class="ann-card"
            @click="viewDetail(item)"
          >
            <!-- 头部：标题和重要标签 -->
            <div class="card-header">
              <h3 class="title">{{ item.title }}</h3>
              <van-tag type="danger" v-if="item.is_important">重要</van-tag>
            </div>
            
            <!-- 发布单位 -->
            <div class="publisher">
              <van-icon name="user-o" />
              {{ item.publisher_name || '物业管理处' }}
            </div>
            
            <!-- 内容摘要 -->
            <div class="content-text">{{ getContentPreview(item.content) }}</div>
            
            <!-- 底部：时间和查看按钮 -->
            <div class="card-footer">
              <span class="time">{{ formatDate(item.created_at) }}</span>
              <span class="view-btn">查看详情</span>
            </div>
          </div>
          
          <van-empty v-if="announcements.length === 0" description="暂无公告" />
        </van-list>
      </van-pull-refresh>
    </div>
    
    <!-- 公告详情弹窗 -->
    <van-popup 
      :show="showDetail" 
      @update:show="showDetail = $event"
      position="bottom" 
      round 
      :style="{ height: '70%' }"
    >
      <div class="detail-content" v-if="currentAnn">
        <div class="detail-header">
          <h2>{{ currentAnn.title }}</h2>
          <van-tag type="danger" v-if="currentAnn.is_important">重要</van-tag>
        </div>
        
        <div class="detail-meta">
          <div class="meta-item">
            <van-icon name="user-o" />
            <span>{{ currentAnn.publisher_name || '物业管理处' }}</span>
          </div>
          <div class="meta-item">
            <van-icon name="clock-o" />
            <span>{{ formatDate(currentAnn.created_at) }}</span>
          </div>
        </div>
        
        <van-divider />
        
        <div class="detail-body">
          {{ currentAnn.content }}
        </div>
      </div>
    </van-popup>
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
    const showDetail = ref(false)
    const currentAnn = ref(null)
    
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
    
    const getContentPreview = (content) => {
      if (!content) return ''
      // 限制显示80个字符
      return content.length > 80 ? content.substring(0, 80) + '...' : content
    }
    
    const viewDetail = (ann) => {
      currentAnn.value = ann
      showDetail.value = true
    }
    
    const formatDate = (date) => {
      if (!date) return ''
      // 解析ISO格式（带Z表示UTC），转为北京时间(+8)
      const d = new Date(date)
      // 如果是UTC时间（带Z），new Date会自动转为本地时间
      // 但我们需要显式处理确保正确
      const beijingTime = new Date(d.getTime())
      const year = beijingTime.getFullYear()
      const month = String(beijingTime.getMonth() + 1).padStart(2, '0')
      const day = String(beijingTime.getDate()).padStart(2, '0')
      const hour = String(beijingTime.getHours()).padStart(2, '0')
      const minute = String(beijingTime.getMinutes()).padStart(2, '0')
      return `${year}-${month}-${day} ${hour}:${minute}`
    }
    
    return {
      announcements,
      loading,
      finished,
      refreshing,
      showDetail,
      currentAnn,
      onLoad,
      onRefresh,
      getContentPreview,
      viewDetail,
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
  padding-bottom: 16px;
}

.ann-card {
  background: white;
  margin: 12px 16px;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #f0f0f0;
}

.ann-card:active {
  transform: scale(0.98);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.ann-card:first-child {
  margin-top: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.title {
  flex: 1;
  font-size: 17px;
  font-weight: 600;
  color: #323233;
  line-height: 1.5;
  margin: 0;
  margin-right: 8px;
  letter-spacing: 0.3px;
}

.publisher {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #969799;
  margin-bottom: 10px;
  background: #f7f8fa;
  padding: 4px 10px;
  border-radius: 12px;
  display: inline-flex;
}

.publisher .van-icon {
  font-size: 13px;
}

.content-text {
  font-size: 14px;
  color: #646566;
  line-height: 1.7;
  margin-bottom: 12px;
  text-align: justify;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f2f3f5;
}

.time {
  font-size: 12px;
  color: #969799;
  display: flex;
  align-items: center;
  gap: 4px;
}

.time::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 4px;
  background: #c8c9cc;
  border-radius: 50%;
}

.view-btn {
  font-size: 13px;
  color: #1989fa;
  font-weight: 500;
  padding: 4px 12px;
  background: #e6f2ff;
  border-radius: 12px;
  transition: all 0.2s;
}

.ann-card:active .view-btn {
  background: #d1e8ff;
}

/* 详情弹窗样式 */
.detail-content {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.detail-header h2 {
  flex: 1;
  font-size: 18px;
  font-weight: bold;
  color: #323233;
  line-height: 1.5;
  margin: 0;
  margin-right: 8px;
}

.detail-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #646566;
}

.meta-item .van-icon {
  font-size: 14px;
  color: #969799;
}

.detail-body {
  font-size: 15px;
  color: #323233;
  line-height: 1.8;
  text-align: justify;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
