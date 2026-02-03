<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="logo">
        <span v-if="!sidebarCollapsed">智慧物业</span>
        <span v-else>智</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="sidebarCollapsed"
        :unique-opened="true"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>数据看板</template>
        </el-menu-item>
        
        <el-menu-item index="/owners">
          <el-icon><User /></el-icon>
          <template #title>业主管理</template>
        </el-menu-item>
        
        <el-menu-item index="/properties">
          <el-icon><OfficeBuilding /></el-icon>
          <template #title>房产管理</template>
        </el-menu-item>
        
        <el-menu-item index="/bills">
          <el-icon><Tickets /></el-icon>
          <template #title>账单管理</template>
        </el-menu-item>
        
        <el-menu-item index="/repairs">
          <el-icon><Tools /></el-icon>
          <template #title>报修管理</template>
        </el-menu-item>
        
        <el-menu-item index="/maintenance">
          <el-icon><UserFilled /></el-icon>
          <template #title>维修人员</template>
        </el-menu-item>
        
        <el-menu-item index="/announcements">
          <el-icon><Bell /></el-icon>
          <template #title>公告管理</template>
        </el-menu-item>
        
        <el-menu-item index="/complaints">
          <el-icon><ChatDotSquare /></el-icon>
          <template #title>投诉管理</template>
        </el-menu-item>
      </el-menu>
    </aside>
    
    <!-- 主内容区 -->
    <div class="main-container">
      <!-- 顶部导航 -->
      <header class="header">
        <div class="header-left">
          <el-icon class="toggle-icon" @click="toggleSidebar">
            <Fold v-if="!sidebarCollapsed" />
            <Expand v-else />
          </el-icon>
        </div>
        
        <div class="header-right">
          <span class="username">{{ userName }}</span>
          <el-dropdown @command="handleCommand">
            <el-avatar :size="32" style="cursor: pointer">
              {{ userName.charAt(0) }}
            </el-avatar>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      
      <!-- 内容区域 -->
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  DataAnalysis, User, OfficeBuilding, Tickets, Tools, UserFilled, Bell, ChatDotSquare,
  Fold, Expand, SwitchButton
} from '@element-plus/icons-vue'

export default {
  name: 'Layout',
  components: {
    DataAnalysis, User, OfficeBuilding, Tickets, Tools, UserFilled, Bell, ChatDotSquare,
    Fold, Expand, SwitchButton
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const store = useStore()
    
    const activeMenu = computed(() => route.path)
    const sidebarCollapsed = computed(() => store.state.sidebarCollapsed)
    const userName = computed(() => store.getters.userName)
    
    const toggleSidebar = () => {
      store.commit('TOGGLE_SIDEBAR')
    }
    
    const handleCommand = async (command) => {
      if (command === 'logout') {
        try {
          await ElMessageBox.confirm('确定要退出登录吗?', '提示', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          })
          
          store.dispatch('logout')
          ElMessage.success('退出成功')
          router.push('/login')
        } catch (error) {
          // 取消操作
        }
      }
    }
    
    return {
      activeMenu,
      sidebarCollapsed,
      userName,
      toggleSidebar,
      handleCommand
    }
  }
}
</script>

<style lang="scss" scoped>
.layout-container {
  display: flex;
  width: 100%;
  height: 100%;
}

.sidebar {
  width: 200px;
  background: #001529;
  transition: width 0.3s;
  overflow: hidden;
  
  &.collapsed {
    width: 64px;
  }
  
  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    font-weight: bold;
    color: #fff;
    background: rgba(255, 255, 255, 0.05);
  }
  
  :deep(.el-menu) {
    border-right: none;
    background: #001529;
    
    .el-menu-item {
      color: rgba(255, 255, 255, 0.7);
      
      &:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        color: #fff;
      }
      
      &.is-active {
        background: #1890ff !important;
        color: #fff;
      }
    }
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  
  .header-left {
    .toggle-icon {
      font-size: 20px;
      cursor: pointer;
      
      &:hover {
        color: #1890ff;
      }
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .username {
      font-size: 14px;
      color: #333;
    }
  }
}

.content {
  flex: 1;
  overflow-y: auto;
  background: #f0f2f5;
}
</style>
