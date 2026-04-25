import { createStore } from 'vuex'
import { maintenanceWorkorderAPI } from '@/api'

// 获取token key，根据当前角色
const getTokenKey = (role) => {
  if (role === 'maintenance') return 'maintenance_token'
  return 'owner_token'
}

// 获取userInfo key，根据当前角色
const getUserInfoKey = (role) => {
  if (role === 'maintenance') return 'maintenance_userInfo'
  return 'owner_userInfo'
}

// 获取当前角色（本地开发版）
const getCurrentRole = () => {
  const path = window.location.pathname
  
  // 本地开发：pathname 包含 /maintenance
  if (path.startsWith('/maintenance')) {
    return 'maintenance'
  }
  
  // 默认业主
  return 'owner'
}

// 获取当前角色的用户信息
const getCurrentUserInfo = () => {
  const role = getCurrentRole()
  const data = localStorage.getItem(getUserInfoKey(role))
  return data ? JSON.parse(data) : {}
}

// 获取当前角色的token
const getCurrentToken = () => {
  const role = getCurrentRole()
  return localStorage.getItem(getTokenKey(role)) || ''
}

export default createStore({
  state: {
    token: getCurrentToken(),
    userInfo: getCurrentUserInfo(),
    // WebSocket通知状态
    repairStatusUpdate: null,      // 业主：工单状态更新通知
    newWorkorder: null,            // 维修人员：新工单通知
    workorderDeleted: null,        // 维修人员：工单被删除通知
    workorderEvaluated: null,      // ✅ 新增：维修人员：工单被评价通知
    workorderStatusUpdate: null,   // ✅ 新增：维修工单状态更新（用于维修人员端自动刷新）
    complaintUpdate: null,         // ✅ 新增：业主：投诉状态更新通知
    // ✅ 新增：维修人员统计数据
    maintenanceStats: null,
    // ✅ 新增：是否有新通知
    hasNewNotification: false
  },
  
  mutations: {
    SET_TOKEN(state, { token, role }) {
      state.token = token
      // 存 token
      const key = getTokenKey(role)
      localStorage.setItem(key, token)
    },
    
    SET_USER_INFO(state, userInfo) {
      state.userInfo = userInfo
      const key = getUserInfoKey(userInfo.role)
      localStorage.setItem(key, JSON.stringify(userInfo))
    },
    
    CLEAR_TOKEN(state) {
      state.token = ''
      state.userInfo = {}
      // 清除所有token和userInfo
      localStorage.removeItem('owner_token')
      localStorage.removeItem('maintenance_token')
      localStorage.removeItem('owner_userInfo')
      localStorage.removeItem('maintenance_userInfo')
    },
    
    // WebSocket通知相关mutations
    SET_REPAIR_STATUS_UPDATE(state, data) {
      state.repairStatusUpdate = data
    },
    
    SET_NEW_WORKORDER(state, data) {
      state.newWorkorder = data
    },
    
    SET_WORKORDER_DELETED(state, data) {
      state.workorderDeleted = data
    },
    
    // ✅ 新增：工单评价通知
    SET_WORKORDER_EVALUATED(state, data) {
      state.workorderEvaluated = data
    },
    
    // ✅ 新增：工单状态更新（支付通知）
    SET_WORKORDER_STATUS_UPDATE(state, data) {
      state.workorderStatusUpdate = data
    },
    
    // ✅ 新增：设置维修人员统计数据
    SET_MAINTENANCE_STATS(state, stats) {
      state.maintenanceStats = stats
    },
    
    // ✅ 新增：设置新通知状态
    SET_HAS_NEW_NOTIFICATION(state, hasNew) {
      state.hasNewNotification = hasNew
    },
    
    // ✅ 新增：投诉状态更新
    SET_COMPLAINT_UPDATE(state, data) {
      state.complaintUpdate = data
    }
  },
  
  actions: {
    login({ commit }, { token, userInfo }) {
      commit('SET_TOKEN', { token, role: userInfo.role })
      commit('SET_USER_INFO', userInfo)
    },
    
    logout({ commit }) {
      commit('CLEAR_TOKEN')
    },
    
    // WebSocket通知相关actions
    notifyRepairStatusUpdate({ commit }, data) {
      commit('SET_REPAIR_STATUS_UPDATE', data)
    },
    
    notifyNewWorkorder({ commit }, data) {
      commit('SET_NEW_WORKORDER', data)
    },
    
    notifyWorkorderDeleted({ commit }, data) {
      commit('SET_WORKORDER_DELETED', data)
    },
    
    // ✅ 新增：工单评价通知
    notifyWorkorderEvaluated({ commit }, data) {
      commit('SET_WORKORDER_EVALUATED', data)
    },
    
    // ✅ 新增：加载维修人员统计数据
    async loadMaintenanceStats({ commit, state }) {
      if (state.userInfo.role === 'maintenance') {
        try {
          const stats = await maintenanceWorkorderAPI.getStatistics()
          commit('SET_MAINTENANCE_STATS', stats)
        } catch (error) {
          console.error('加载统计数据失败:', error)
        }
      }
    },
    
    // ✅ 新增：投诉状态更新通知
    notifyComplaintUpdate({ commit }, data) {
      commit('SET_COMPLAINT_UPDATE', data)
    }
  }
})
