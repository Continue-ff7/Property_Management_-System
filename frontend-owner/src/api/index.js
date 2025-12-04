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
