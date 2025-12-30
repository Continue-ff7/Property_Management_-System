<template>
  <div class="profile-page">
    <van-nav-bar 
      title="我的" 
      left-arrow
      @click-left="$router.back()"
      fixed 
    />
    
    <div class="content">
      <!-- 用户信息卡片 -->
      <div class="user-card" @click="showEditDialog">
        <div class="avatar-wrapper">
          <van-image
            round
            width="70"
            height="70"
            :src="getImageUrl(userInfo.avatar) || 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg'"
            fit="cover"
          />
          <div class="avatar-edit-icon">
            <van-icon name="edit" size="14" color="#fff" />
          </div>
        </div>
        <div class="user-info">
          <div class="name">{{ userInfo.name || '业主' }}</div>
          <div class="phone">{{ userInfo.phone || '未绑定手机' }}</div>
        </div>
        <van-icon name="arrow" color="rgba(255,255,255,0.7)" />
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
        <van-cell title="编辑个人信息" is-link @click="showEditDialog">
          <template #icon>
            <van-icon name="edit" size="20" style="margin-right: 12px;" />
          </template>
        </van-cell>
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
        <div class="avatar-upload">
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
            disabled
            placeholder="手机号不可修改"
          />
        </van-cell-group>
      </div>
    </van-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { showConfirmDialog, showSuccessToast, showLoadingToast, showFailToast } from 'vant'
import { ownerAPI, uploadAPI } from '@/api'
import { getImageUrl } from '@/utils/request'

export default {
  name: 'Profile',
  setup() {
    const router = useRouter()
    const store = useStore()
    const userInfo = computed(() => store.state.userInfo)
    const properties = ref([])
    const showEdit = ref(false)
    const avatarFile = ref([])
    
    // 编辑表单
    const editForm = reactive({
      name: '',
      email: '',
      phone: '',
      avatar: ''
    })
    
    const loadProperties = async () => {
      try {
        const data = await ownerAPI.getMyProperties()
        properties.value = data
      } catch (error) {
        console.error('加载房产失败:', error)
      }
    }
    
    const showEditDialog = () => {
      // 填充表单
      editForm.name = userInfo.value.name || ''
      editForm.email = userInfo.value.email || ''
      editForm.phone = userInfo.value.phone || ''
      editForm.avatar = userInfo.value.avatar || ''
      
      showEdit.value = true
    }
    
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
        showFailToast('头像上传失败')
        console.error(error)
      } finally {
        loading.close()
      }
    }
    
    const handleSaveProfile = async () => {
      if (!editForm.name.trim()) {
        showFailToast('请输入姓名')
        return
      }
      
      const loading = showLoadingToast({
        message: '保存中...',
        forbidClick: true,
        duration: 0
      })
      
      try {
        const result = await ownerAPI.updateProfile({
          name: editForm.name,
          email: editForm.email,
          avatar: editForm.avatar
        })
        
        // 更新store
        const updatedUserInfo = result.data || result
        store.commit('SET_USER_INFO', updatedUserInfo)
        
        loading.close()
        showSuccessToast('保存成功')
        showEdit.value = false
      } catch (error) {
        loading.close()
        console.error('保存错误:', error)
        console.error('错误详情:', error.response)
        showFailToast(error.message || '保存失败')
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
      // 不需要调用 loadProfile()，因为：
      // 1. 登录时已经将用户信息保存到 store
      // 2. 编辑后会更新 store
      // 3. 避免不必要的API请求导致401跳转
      
      loadProperties()
    })
    
    return {
      userInfo,
      properties,
      showEdit,
      avatarFile,
      editForm,
      getImageUrl,
      showEditDialog,
      handleAvatarUpload,
      handleSaveProfile,
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
  cursor: pointer;
  transition: transform 0.2s;
}

.user-card:active {
  transform: scale(0.98);
}

.avatar-wrapper {
  position: relative;
}

.avatar-edit-icon {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 24px;
  height: 24px;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid white;
}

.user-info {
  flex: 1;
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

/* 编辑弹窗样式 */
.edit-form {
  padding: 20px;
}

.avatar-upload {
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
