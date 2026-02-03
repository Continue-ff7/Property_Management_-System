import { createStore } from 'vuex'
import { maintenanceWorkorderAPI } from '@/api'

export default createStore({
  state: {
    token: localStorage.getItem('token') || '',
    userInfo: JSON.parse(localStorage.getItem('userInfo') || '{}'),
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
    SET_TOKEN(state, token) {
      state.token = token
      localStorage.setItem('token', token)
    },
    
    SET_USER_INFO(state, userInfo) {
      state.userInfo = userInfo
      localStorage.setItem('userInfo', JSON.stringify(userInfo))
    },
    
    CLEAR_TOKEN(state) {
      state.token = ''
      state.userInfo = {}
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
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
      commit('SET_TOKEN', token)
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
