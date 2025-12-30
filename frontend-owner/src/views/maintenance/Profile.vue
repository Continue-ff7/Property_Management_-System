<template>
  <div class="profile-page">
    <van-nav-bar
      title="个人中心"
      left-arrow
      @click-left="$router.back()"
      fixed
    />
    
    <div class="content">
      <!-- 个人信息卡片 -->
      <div class="user-card" @click="handleCardClick">
        <van-image
          round
          width="60"
          height="60"
          :src="avatarUrl"
        />
        <div class="user-info">
          <div class="name">{{ userInfo.name || userInfo.username }}</div>
          <div class="role">维修人员</div>
        </div>
        <van-icon name="edit" color="white" size="18" style="margin-left: auto;" />
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
        <van-cell title="个人信息" is-link @click="handleEditClick" />
        <van-cell title="系统设置" is-link />
      </van-cell-group>
      
      <div style="margin: 24px 16px;">
        <van-button block @click="handleLogout">
          退出登录
        </van-button>
      </div>
    </div>
    
    <!-- 编辑个人信息弹窗 -->
    <van-dialog
      :show="showEdit"
      title="编辑个人信息"
      show-cancel-button
      @confirm="handleSaveProfile"
      @cancel="showEdit = false"
      @close="showEdit = false"
    >
      <div class="edit-form">
        <!-- 头像上传 -->
        <div class="avatar-upload-section">
          <van-uploader
            v-model="avatarFile"
            :max-count="1"
            :after-read="handleAvatarUpload"
            :deletable="true"
          >
            <van-image
              round
              width="80"
              height="80"
              :src="getImageUrl(editForm.avatar) || 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg'"
              fit="cover"
            />
          </van-uploader>
          <div class="upload-hint">点击头像更换</div>
        </div>
        
        <!-- 表单字段 -->
        <van-cell-group inset>
          <van-field
            v-model="editForm.name"
            label="姓名"
            placeholder="请输入姓名"
            :rules="[{ required: true, message: '请输入姓名' }]"
          />
          <van-field
            v-model="editForm.email"
            label="邮箱"
            placeholder="请输入邮箱"
            type="email"
          />
          <van-field
            v-model="editForm.phone"
            label="手机号"
            placeholder="请输入手机号"
          />
        </van-cell-group>
      </div>
    </van-dialog>
  </div>
</template>

<script>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { showConfirmDialog, showSuccessToast, showToast, showLoadingToast } from 'vant'
import { maintenanceWorkorderAPI, maintenanceAPI, uploadAPI } from '@/api'
import { getImageUrl } from '@/utils/request'

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
    
    const showEdit = ref(false)
    const avatarFile = ref([])
    const editForm = reactive({
      name: '',
      phone: '',
      email: '',
      avatar: ''
    })
    
    // 计算头像URL
    const avatarUrl = computed(() => {
      if (userInfo.value?.avatar) {
        return getImageUrl(userInfo.value.avatar)
      }
      return 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg'
    })
    
    // 点击卡片，打开编辑弹窗
    const handleCardClick = () => {
      // 填充表单
      editForm.name = userInfo.value?.name || ''
      editForm.phone = userInfo.value?.phone || ''
      editForm.email = userInfo.value?.email || ''
      editForm.avatar = userInfo.value?.avatar || ''
      
      showEdit.value = true
    }
    
    // 点击编辑按钮
    const handleEditClick = () => {
      handleCardClick()
    }
    
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
    
    // 上传头像
    const handleAvatarUpload = async (file) => {
      const loading = showLoadingToast({
        message: '上传中...',
        forbidClick: true,
        duration: 0
      })
      
      try {
        const result = await uploadAPI.upload(file.file)
        editForm.avatar = result.url
        showSuccessToast('头像上传成功')
      } catch (error) {
        showToast('头像上传失败')
        console.error(error)
      } finally {
        loading.close()
      }
    }
    
    // 保存个人信息
    const handleSaveProfile = async () => {
      if (!editForm.name.trim()) {
        showToast('请输入姓名')
        return
      }
      
      const loading = showLoadingToast({
        message: '保存中...',
        forbidClick: true,
        duration: 0
      })
      
      try {
        const updateData = {}
        if (editForm.name) updateData.name = editForm.name
        if (editForm.phone) updateData.phone = editForm.phone
        if (editForm.email) updateData.email = editForm.email
        if (editForm.avatar) updateData.avatar = editForm.avatar
        
        const res = await maintenanceAPI.updateProfile(updateData)
        
        // 更新Vuex中的用户信息
        store.commit('SET_USER_INFO', {
          ...userInfo.value,
          name: res.name,
          phone: res.phone,
          email: res.email,
          avatar: res.avatar
        })
        
        showSuccessToast('保存成功')
        showEdit.value = false
      } catch (error) {
        showToast('保存失败')
        console.error('保存失败:', error)
      } finally {
        loading.close()
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
      avatarUrl,
      showEdit,
      avatarFile,
      editForm,
      handleCardClick,
      handleEditClick,
      goTo,
      handleLogout,
      handleAvatarUpload,
      handleSaveProfile,
      getImageUrl
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

/* 编辑弹窗样式 */
.edit-form {
  padding: 20px;
}

.avatar-upload-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;
}

.upload-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #999;
}

.edit-form :deep(.van-cell-group) {
  margin-top: 16px;
}
</style>
