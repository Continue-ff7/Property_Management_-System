<template>
  <div class="login-page">
    <!-- 背景图片 -->
    <div class="bg-image"></div>
    
    <!-- Tab切换 -->
    <div class="tab-container">
      <div 
        class="tab-item" 
        :class="{ active: loginRole === 'owner' }"
        @click="loginRole = 'owner'"
      >
        业主端
      </div>
      <div 
        class="tab-item" 
        :class="{ active: loginRole === 'maintenance' }"
        @click="loginRole = 'maintenance'"
      >
        维修人员端
      </div>
    </div>
    
    <!-- 登录/注册表单 -->
    <div class="form-container">
      <!-- 登录表单 -->
      <van-form v-if="!isRegister" @submit="onSubmit">
        <div class="input-wrapper">
          <input
            v-model="formData.username"
            type="text"
            placeholder="请输入用户名"
            class="custom-input"
          />
        </div>
        
        <div class="input-wrapper">
          <input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
            class="custom-input"
          />
        </div>
        
        <van-button 
          round 
          block 
          type="primary" 
          native-type="submit" 
          :loading="loading"
          class="login-button"
        >
          登录
        </van-button>
      </van-form>
      
      <!-- 注册表单 -->
      <van-form v-else @submit="onRegister">
        <div class="input-wrapper">
          <input
            v-model="registerData.username"
            type="text"
            placeholder="请输入用户名"
            class="custom-input"
          />
        </div>
        
        <div class="input-wrapper">
          <input
            v-model="registerData.password"
            type="password"
            placeholder="请输入密码"
            class="custom-input"
          />
        </div>
        
        <div class="input-wrapper">
          <input
            v-model="registerData.confirmPassword"
            type="password"
            placeholder="请确认密码"
            class="custom-input"
          />
        </div>
        
        <div class="input-wrapper">
          <input
            v-model="registerData.name"
            type="text"
            placeholder="请输入姓名"
            class="custom-input"
          />
        </div>
        
        <div class="input-wrapper">
          <input
            v-model="registerData.phone"
            type="tel"
            placeholder="请输入手机号"
            class="custom-input"
          />
        </div>
        
        <van-button 
          round 
          block 
          type="primary" 
          native-type="submit" 
          :loading="loading"
          class="login-button"
        >
          注册
        </van-button>
      </van-form>
      
      <!-- 切换登录/注册 -->
      <div class="switch-mode">
        <span @click="toggleMode">
          {{ isRegister ? '已有账号？去登录' : '没有账号？去注册' }}
        </span>
      </div>
      
      <!-- 协议勾选 -->
      <div class="agreement">
        <van-checkbox v-model="agreed" icon-size="16px">
          我已阅读并同意
          <span class="link">《用户协议》</span>
          和
          <span class="link">《隐私政策》</span>
        </van-checkbox>
      </div>
    </div>
    
    <!-- 底部文案 -->
    <div class="footer">
      <p>更智慧 更美好</p>
    </div>
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
    const agreed = ref(false) // 协议勾选状态
    const isRegister = ref(false) // 是否注册模式
    
    const formData = reactive({
      username: '',
      password: ''
    })
    
    const registerData = reactive({
      username: '',
      password: '',
      confirmPassword: '',
      name: '',
      phone: ''
    })
    
    // 切换登录/注册模式
    const toggleMode = () => {
      isRegister.value = !isRegister.value
      // 清空表单
      formData.username = ''
      formData.password = ''
      registerData.username = ''
      registerData.password = ''
      registerData.confirmPassword = ''
      registerData.name = ''
      registerData.phone = ''
    }
    
    // 登录
    const onSubmit = async () => {
      // 验证输入
      if (!formData.username) {
        showToast('请输入用户名')
        return
      }
      if (!formData.password) {
        showToast('请输入密码')
        return
      }
      if (!agreed.value) {
        showToast('请阅读并同意用户协议和隐私政策')
        return
      }
      
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
          router.push('/home/index')
        }
      } catch (error) {
        console.error('登录失败:', error)
      } finally {
        loading.value = false
      }
    }
    
    // 注册
    const onRegister = async () => {
      // 验证输入
      if (!registerData.username) {
        showToast('请输入用户名')
        return
      }
      if (!registerData.password) {
        showToast('请输入密码')
        return
      }
      if (registerData.password.length < 6) {
        showToast('密码长度不能少于6位')
        return
      }
      if (registerData.password !== registerData.confirmPassword) {
        showToast('两次密码输入不一致')
        return
      }
      if (!registerData.name) {
        showToast('请输入姓名')
        return
      }
      if (!registerData.phone) {
        showToast('请输入手机号')
        return
      }
      if (!/^1[3-9]\d{9}$/.test(registerData.phone)) {
        showToast('请输入正确的手机号')
        return
      }
      if (!agreed.value) {
        showToast('请阅读并同意用户协议和隐私政策')
        return
      }
      
      loading.value = true
      try {
        // 调用注册接口
        await authAPI.register({
          username: registerData.username,
          password: registerData.password,
          name: registerData.name,
          phone: registerData.phone,
          email: '',  // 添加email字段（空字符串会被转为None）
          role: loginRole.value // 根据当前Tab决定角色
        })
        
        showToast('注册成功，请登录')
        
        // 切换到登录模式并填充账号
        isRegister.value = false
        formData.username = registerData.username
        formData.password = ''
      } catch (error) {
        console.error('注册失败:', error)
      } finally {
        loading.value = false
      }
    }
    
    return {
      formData,
      registerData,
      loading,
      loginRole,
      agreed,
      isRegister,
      toggleMode,
      onSubmit,
      onRegister
    }
  }
}
</script>

<style scoped>
.login-page {
  width: 100%;
  min-height: 100vh;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 背景图片 - 深蓝色夜景风格 */
.bg-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, #0a1f44 0%, #1a3a5c 50%, #2a4a6c 100%);
  background-size: cover;
  background-position: center;
  z-index: 0;
}

/* 背景遮罩 */
.bg-image::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(10, 31, 68, 0.3);
}

/* Tab切换容器 */
.tab-container {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 120px;
  margin-bottom: 40px;
  padding: 0 60px;
}

.tab-item {
  flex: 1;
  text-align: center;
  font-size: 17px;
  color: rgba(255, 255, 255, 0.6);
  padding-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  font-weight: 400;
}

.tab-item.active {
  color: #ffffff;
  font-weight: 500;
}

/* 活跃Tab的下划线 */
.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 3px;
  background: #ffffff;
  border-radius: 2px;
}

/* 表单容器 */
.form-container {
  position: relative;
  z-index: 1;
  padding: 0 26px;
  flex: 1;
}

/* 输入框包装 */
.input-wrapper {
  margin-bottom: 16px;
}

/* 自定义输入框 */
.custom-input {
  width: 100%;
  height: 52px;
  background: rgba(255, 255, 255, 0.95);
  border: none;
  border-radius: 8px;
  padding: 0 20px;
  font-size: 15px;
  color: #333;
  outline: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.custom-input::placeholder {
  color: #bbb;
}

.custom-input:focus {
  background: rgba(255, 255, 255, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 登录/注册按钮 */
.login-button {
  width: 100%;
  height: 50px;
  margin-top: 24px;
  font-size: 16px;
  font-weight: 500;
  background: linear-gradient(135deg, #1e88e5 0%, #1976d2 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(30, 136, 229, 0.4);
  transition: all 0.3s;
}

.login-button:active {
  transform: scale(0.98);
}

/* 切换登录/注册按钮 */
.switch-mode {
  text-align: center;
  margin-top: 20px;
  padding: 10px 0;
}

.switch-mode span {
  color: rgba(255, 255, 255, 0.85);
  font-size: 14px;
  cursor: pointer;
  text-decoration: underline;
  transition: all 0.3s;
}

.switch-mode span:hover {
  color: #ffffff;
}

/* 协议勾选 */
.agreement {
  margin-top: 20px;
  display: flex;
  align-items: center;
}

.agreement :deep(.van-checkbox) {
  flex: 1;
}

.agreement :deep(.van-checkbox__label) {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.6;
}

.agreement :deep(.van-checkbox__icon) {
  border-color: rgba(255, 255, 255, 0.5);
}

.agreement :deep(.van-checkbox__icon--checked) {
  background-color: #1e88e5;
  border-color: #1e88e5;
}

.agreement .link {
  color: #64b5f6;
  text-decoration: none;
}

/* 底部文案 */
.footer {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 30px 0;
  margin-top: auto;
}

.footer p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
  letter-spacing: 2px;
  font-weight: 300;
}
</style>
