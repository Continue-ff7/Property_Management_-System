<template>
  <div class="login-container">
    <!-- 背景图片 -->
    <div class="bg-decoration">
      <img src="@/layout/img/img.png" alt="" class="bg-image" />
    </div>
    
    <!-- 登录表单卡片 -->
    <div class="login-card">
      <div class="card-header">
        <div class="logo-icon">
          <svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="40" height="40">
            <path d="M512 85.333333l384 256v512H640V597.333333H384v256H128V341.333333l384-256z" fill="#52c41a"/>
          </svg>
        </div>
        <h1 class="title">智慧物业管理系统</h1>
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
            placeholder="请输入账号"
            size="large"
            prefix-icon="User"
            clearable
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
            type="success"
            size="large"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            立即登录
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
  height: 100vh;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 50%, #95de64 100%);
}

// 背景装饰图片（左侧居中）
.bg-decoration {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 55%;
  height: 65%;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .bg-image {
    width: 100%;
    height: 100%;
    object-fit: contain;
    object-position: center;
    filter: drop-shadow(0 10px 30px rgba(0, 0, 0, 0.15));
  }
}

// 登录表单卡片（右上角悬浮）
.login-card {
  position: absolute;
  top: 10%;
  right: 8%;
  width: 420px;
  background: #ffffff;
  border-radius: 20px;
  padding: 40px 45px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(10px);
}

.card-header {
  text-align: center;
  margin-bottom: 35px;
  
  .logo-icon {
    margin: 0 auto 16px;
    width: 56px;
    height: 56px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
  
  .title {
    font-size: 28px;
    font-weight: 600;
    color: #262626;
    margin: 0;
    letter-spacing: 3px;
  }
}

.login-form {
  :deep(.el-form-item) {
    margin-bottom: 20px;
  }
  
  :deep(.el-input__wrapper) {
    padding: 13px 15px;
    border-radius: 10px;
    box-shadow: 0 0 0 1px #e0e0e0 inset;
    transition: all 0.3s;
    
    &:hover {
      box-shadow: 0 0 0 1px #52c41a inset;
    }
  }
  
  :deep(.el-input__wrapper.is-focus) {
    box-shadow: 0 0 0 1px #52c41a inset, 0 0 0 3px rgba(82, 196, 26, 0.1);
  }
  
  :deep(.el-input__prefix) {
    font-size: 16px;
    color: #8c8c8c;
  }
  
  :deep(.el-input__inner) {
    font-size: 14px;
  }
}

.login-button {
  width: 100%;
  height: 46px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 10px;
  background: linear-gradient(135deg, #52c41a 0%, #73d13d 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(82, 196, 26, 0.35);
  transition: all 0.3s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(82, 196, 26, 0.45);
  }
  
  &:active {
    transform: translateY(0);
  }
}

.login-tips {
  margin-top: 20px;
  text-align: center;
  
  p {
    font-size: 12px;
    color: #bfbfbf;
    margin: 0;
  }
}

// 响应式适配
@media (max-width: 1200px) {
  .login-card {
    right: 5%;
    width: 380px;
  }
}

@media (max-width: 768px) {
  .bg-decoration {
    display: none;
  }
  
  .login-card {
    top: 50%;
    right: 50%;
    transform: translate(50%, -50%);
    width: 90%;
    max-width: 400px;
  }
}
</style>
