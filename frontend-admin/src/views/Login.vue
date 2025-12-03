<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>智慧物业管理系统</h1>
        <p>Property Management System</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="rules"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            style="width: 100%"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-tips">
        <p>默认账户：admin / admin123</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { authAPI } from '@/api'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const store = useStore()
    const loginFormRef = ref(null)
    const loading = ref(false)
    
    const loginForm = reactive({
      username: 'admin',
      password: 'admin123'
    })
    
    const rules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能小于6位', trigger: 'blur' }
      ]
    }
    
    const handleLogin = async () => {
      if (!loginFormRef.value) return
      
      await loginFormRef.value.validate(async (valid) => {
        if (!valid) return
        
        loading.value = true
        try {
          const res = await authAPI.login(loginForm)
          
          // 检查角色
          if (res.user.role !== 'manager') {
            ElMessage.error('只有管理员才能登录此系统')
            return
          }
          
          // 保存登录信息
          store.dispatch('login', {
            token: res.access_token,
            user: res.user
          })
          
          ElMessage.success('登录成功')
          router.push('/')
        } catch (error) {
          console.error('登录失败:', error)
        } finally {
          loading.value = false
        }
      })
    }
    
    return {
      loginFormRef,
      loginForm,
      rules,
      loading,
      handleLogin
    }
  }
}
</script>

<style lang="scss" scoped>
.login-container {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-box {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
  
  h1 {
    font-size: 28px;
    color: #333;
    margin-bottom: 8px;
  }
  
  p {
    font-size: 14px;
    color: #999;
  }
}

.login-form {
  :deep(.el-form-item) {
    margin-bottom: 24px;
  }
}

.login-tips {
  margin-top: 20px;
  text-align: center;
  font-size: 12px;
  color: #999;
}
</style>
