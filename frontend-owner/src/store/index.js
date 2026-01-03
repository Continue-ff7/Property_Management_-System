import { createStore } from 'vuex'

export default createStore({
  state: {
    token: localStorage.getItem('token') || '',
    userInfo: JSON.parse(localStorage.getItem('userInfo') || '{}'),
    // WebSocket通知状态
    repairStatusUpdate: null,      // 业主：工单状态更新通知
    newWorkorder: null,            // 维修人员：新工单通知
    workorderDeleted: null,        // 维修人员：工单被删除通知
    workorderEvaluated: null       // ✅ 新增：维修人员：工单被评价通知
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
    }
  }
})
