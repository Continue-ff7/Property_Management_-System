import request from '@/utils/request'

// 认证API
export const authAPI = {
  // 登录
  login(data) {
    return request({
      url: '/auth/login',
      method: 'post',
      data
    })
  },
  // 注册
  register(data) {
    return request({
      url: '/auth/register',
      method: 'post',
      data
    })
  }
}

// 业主API
export const ownerAPI = {
  // 获取个人信息
  getProfile() {
    return request({
      url: '/owner/profile',
      method: 'get'
    })
  },
  // 更新个人信息
  updateProfile(data) {
    return request({
      url: '/owner/profile',
      method: 'put',
      data
    })
  },
  // 获取我的房产
  getMyProperties() {
    return request({
      url: '/owner/properties',
      method: 'get'
    })
  }
}

// 账单API
export const billAPI = {
  // 获取我的账单
  getMyBills(params) {
    return request({
      url: '/owner/bills',
      method: 'get',
      params
    })
  },
  // 支付账单
  payBill(billId, data) {
    return request({
      url: `/owner/bills/${billId}/pay`,
      method: 'post',
      data
    })
  }
}

// 报修API
export const repairAPI = {
  // 获取我的报修
  getMyRepairs(params) {
    return request({
      url: '/owner/repairs',
      method: 'get',
      params
    })
  },
  // ✅ 新增：获取工单详情
  getRepairDetail(repairId) {
    return request({
      url: `/owner/repairs/${repairId}`,
      method: 'get'
    })
  },
  // 提交报修
  createRepair(data) {
    return request({
      url: '/owner/repairs',
      method: 'post',
      data
    })
  },
  // 评价报修
  evaluateRepair(repairId, data) {
    return request({
      url: `/owner/repairs/${repairId}/evaluate`,
      method: 'post',
      data
    })
  },
  // ✅ 新增：支付维修费用
  payRepairCost(repairId) {
    return request({
      url: `/owner/repairs/${repairId}/pay`,
      method: 'post'
    })
  }
}

// 公告API
export const announcementAPI = {
  // 获取公告列表
  getList(params) {
    return request({
      url: '/common/announcements',
      method: 'get',
      params
    })
  }
}

// 文件上传API
export const uploadAPI = {
  upload(file) {
    const formData = new FormData()
    formData.append('file', file)
    return request({
      url: '/common/upload',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

// 维修人员工单API
export const maintenanceWorkorderAPI = {
  // 获取我的工单
  getMyWorkorders(params) {
    return request({
      url: '/maintenance/orders',
      method: 'get',
      params
    })
  },
  // 获取工单详情
  getWorkorderDetail(id) {
    return request({
      url: `/maintenance/orders/${id}`,
      method: 'get'
    })
  },
  // 开始维修
  startWork(id) {
    return request({
      url: `/maintenance/orders/${id}/start`,
      method: 'post'
    })
  },
  // 完成维修
  completeWork(id, data) {
    return request({
      url: `/maintenance/orders/${id}/complete`,
      method: 'post',
      data
    })
  },
  // 上传维修图片
  uploadRepairImage(id, file) {
    const formData = new FormData()
    formData.append('file', file)
    return request({
      url: `/maintenance/orders/${id}/upload-image`,
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  // 获取统计数据
  getStatistics() {
    return request({
      url: '/maintenance/statistics',
      method: 'get'
    })
  }
}

// 维修人员API
export const maintenanceAPI = {
  // 获取个人信息
  getProfile() {
    return request({
      url: '/maintenance/profile',
      method: 'get'
    })
  },
  // 更新个人信息
  updateProfile(data) {
    return request({
      url: '/maintenance/profile',
      method: 'put',
      data
    })
  }
}

// AI助手API
export const aiAssistantAPI = {
  // 查询账单信息
  getBills() {
    return request({
      url: '/ai/bills',
      method: 'get'
    })
  },
  // 查询报修记录
  getRepairs() {
    return request({
      url: '/ai/repairs',
      method: 'get'
    })
  },
  // 查询房产信息
  getProperties() {
    return request({
      url: '/ai/properties',
      method: 'get'
    })
  },
  // 创建报修工单
  createRepair(data) {
    return request({
      url: '/ai/create-repair',
      method: 'post',
      data
    })
  }
}
