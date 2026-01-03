import { createStore } from 'vuex'

export default createStore({
  state: {
    token: localStorage.getItem('token') || '',
    userInfo: JSON.parse(localStorage.getItem('userInfo') || '{}'),
    sidebarCollapsed: false,
    newRepairNotification: null,  // 新报修通知
    repairStatusUpdate: null  // 工单状态更新通知（维修人员开始/完成维修）
  },
  
  getters: {
    isLoggedIn: state => !!state.token,
    userName: state => state.userInfo.name || state.userInfo.username || '系统管理员',
    userRole: state => state.userInfo.role || ''
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
    
    CLEAR_AUTH(state) {
      state.token = ''
      state.userInfo = {}
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
    },
    
    TOGGLE_SIDEBAR(state) {
      state.sidebarCollapsed = !state.sidebarCollapsed
    },
    
    SET_NEW_REPAIR_NOTIFICATION(state, data) {
      state.newRepairNotification = data
    },
    
    SET_REPAIR_STATUS_UPDATE(state, data) {
      state.repairStatusUpdate = data
    }
  },
  
  actions: {
    login({ commit }, { token, user }) {
      commit('SET_TOKEN', token)
      commit('SET_USER_INFO', user)
    },
    
    logout({ commit }) {
      commit('CLEAR_AUTH')
    },
    
    notifyNewRepair({ commit }, repairData) {
      commit('SET_NEW_REPAIR_NOTIFICATION', repairData)
    },
    
    notifyRepairStatusUpdate({ commit }, repairData) {
      commit('SET_REPAIR_STATUS_UPDATE', repairData)
    }
  }
})
