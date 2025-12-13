<template>
  <div class="login-page">
    <div class="header">
      <h1>智慧物业</h1>
      <p>移动服务系统</p>
    </div>
    
    <!-- 角色选择 -->
    <div class="role-selector">
      <van-button 
        :type="loginRole === 'owner' ? 'primary' : 'default'"
        @click="loginRole = 'owner'"
        round
      >
        业主端
      </van-button>
      <van-button 
        :type="loginRole === 'maintenance' ? 'primary' : 'default'"
        @click="loginRole = 'maintenance'"
        round
      >
        维修人员
      </van-button>
    </div>
    
    <van-form @submit="onSubmit" class="login-form">
      <van-cell-group inset>
        <van-field
          v-model="formData.username"
          name="username"
          label="用户名"
          placeholder="请输入用户名"
          :rules="[{ required: true, message: '请输入用户名' }]"
        />
        <van-field
          v-model="formData.password"
          type="password"
          name="password"
          label="密码"
          placeholder="请输入密码"
          :rules="[{ required: true, message: '请输入密码' }]"
        />
      </van-cell-group>
      
      <div style="margin: 30px 16px;">
        <van-button round block type="primary" native-type="submit" :loading="loading">
          登录
        </van-button>
      </div>
    </van-form>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { showToast } from 'vant'
import { authAPI } from '@/api'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const store = useStore()
    const loading = ref(false)
    const loginRole = ref('owner') // 默认业主
    
    const formData = reactive({
      username: '',
      password: ''
    })
    
    const onSubmit = async () => {
      loading.value = true
      try {
        const res = await authAPI.login({
          username: formData.username,
          password: formData.password
        })
        
        // 检查角色是否匹配
        if (loginRole.value === 'owner' && res.user.role !== 'owner') {
          showToast('请使用业主账号登录')
          return
        }
        if (loginRole.value === 'maintenance' && res.user.role !== 'maintenance') {
          showToast('请使用维修人员账号登录')
          return
        }
        
        // 保存token和用户信息
        await store.dispatch('login', {
          token: res.access_token,
          userInfo: res.user || { username: formData.username, role: res.user.role }
        })
        
        showToast('登录成功')
        
        // 根据角色跳转
        if (loginRole.value === 'maintenance') {
          router.push('/maintenance/workorders')
        } else {
          router.push('/')
        }
      } catch (error) {
        console.error('登录失败:', error)
      } finally {
        loading.value = false
      }
    }
    
    return {
      formData,
      loading,
      loginRole,
      onSubmit
    }
  }
}
</script>

<style scoped>
.login-page {
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(135deg, #4A90E2 0%, #5CA4E8 100%);
  padding: 60px 0;
}

.header {
  text-align: center;
  color: white;
  margin-bottom: 60px;
}

.header h1 {
  font-size: 36px;
  margin-bottom: 10px;
}

.header p {
  font-size: 16px;
  opacity: 0.9;
}

.role-selector {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 30px;
  padding: 0 16px;
}

.role-selector .van-button {
  flex: 1;
  height: 44px;
  font-size: 15px;
}

.login-form {
  padding: 0 16px;
}
</style>
