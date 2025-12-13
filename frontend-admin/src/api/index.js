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
  // 获取业主列表
  getList(params) {
    return request({
      url: '/manager/owners',
      method: 'get',
      params
    })
  },
  // 创建业主
  create(data) {
    return request({
      url: '/manager/owners',
      method: 'post',
      data
    })
  },
  // 更新业主
  update(id, data) {
    return request({
      url: `/manager/owners/${id}`,
      method: 'put',
      data
    })
  },
  // 删除业主
  delete(id, force = false) {
    return request({
      url: `/manager/owners/${id}`,
      method: 'delete',
      params: { force }
    })
  },
  // 获取业主房产
  getProperties(id) {
    return request({
      url: `/manager/owners/${id}/properties`,
      method: 'get'
    })
  }
}

// 房产API
export const propertyAPI = {
  // 获取楼栋列表
  getBuildings() {
    return request({
      url: '/manager/buildings',
      method: 'get'
    })
  },
  // 创建楼栋
  createBuilding(data) {
    return request({
      url: '/manager/buildings',
      method: 'post',
      data
    })
  },
  // 获取房产列表
  getList(params) {
    return request({
      url: '/manager/properties',
      method: 'get',
      params
    })
  },
  // 创建房产
  create(data) {
    return request({
      url: '/manager/properties',
      method: 'post',
      data
    })
  },
  // 分配业主
  assignOwner(propertyId, ownerId) {
    return request({
      url: `/manager/properties/${propertyId}/assign-owner`,
      method: 'put',
      params: { owner_id: ownerId }
    })
  },
  // 解绑业主
  unbindOwner(propertyId) {
    return request({
      url: `/manager/properties/${propertyId}/owner`,
      method: 'delete'
    })
  }
}

// 账单API
export const billAPI = {
  // 获取收费标准
  getStandards() {
    return request({
      url: '/manager/fee-standards',
      method: 'get'
    })
  },
  // 创建收费标准
  createStandard(data) {
    return request({
      url: '/manager/fee-standards',
      method: 'post',
      data
    })
  },
  // 更新收费标准
  updateStandard(id, data) {
    return request({
      url: `/manager/fee-standards/${id}`,
      method: 'put',
      data
    })
  },
  // 获取账单列表
  getList(params) {
    return request({
      url: '/manager/bills',
      method: 'get',
      params
    })
  },
  // 创建账单
  create(data) {
    return request({
      url: '/manager/bills',
      method: 'post',
      data
    })
  },
  // 批量生成账单
  batchCreate(data) {
    return request({
      url: '/manager/bills/batch',
      method: 'post',
      data
    })
  },
  // 删除账单
  delete(id) {
    return request({
      url: `/manager/bills/${id}`,
      method: 'delete'
    })
  }
}

// 报修API
export const repairAPI = {
  // 获取工单列表
  getList(params) {
    return request({
      url: '/manager/repairs',
      method: 'get',
      params
    })
  },
  // 分配工单
  assign(id, data) {
    return request({
      url: `/manager/repairs/${id}/assign`,
      method: 'post',
      params: data
    })
  },
  // 更新工单
  update(id, data) {
    return request({
      url: `/manager/repairs/${id}`,
      method: 'put',
      data
    })
  },
  // 删除工单
  deleteRepair(id) {
    return request({
      url: `/manager/repairs/${id}`,
      method: 'delete'
    })
  }
}

// 维修人员API
export const maintenanceAPI = {
  // 获取维修人员列表
  getList() {
    return request({
      url: '/manager/maintenance-workers',
      method: 'get'
    })
  },
  // 创建维修人员
  create(data) {
    return request({
      url: '/manager/maintenance-workers',
      method: 'post',
      data
    })
  },
  // 更新维修人员
  update(id, data) {
    return request({
      url: `/manager/maintenance-workers/${id}`,
      method: 'put',
      data
    })
  },
  // 删除维修人员
  delete(id, force = false) {
    return request({
      url: `/manager/maintenance-workers/${id}`,
      method: 'delete',
      params: { force }
    })
  }
}

// 公告API
export const announcementAPI = {
  // 获取公告列表
  getList(params) {
    return request({
      url: '/manager/announcements',
      method: 'get',
      params
    })
  },
  // 创建公告
  create(data) {
    return request({
      url: '/manager/announcements',
      method: 'post',
      data
    })
  },
  // 更新公告
  update(id, data) {
    return request({
      url: `/manager/announcements/${id}`,
      method: 'put',
      data
    })
  },
  // 删除公告
  delete(id) {
    return request({
      url: `/manager/announcements/${id}`,
      method: 'delete'
    })
  }
}

// 统计API
export const statisticsAPI = {
  // 收入统计
  getRevenue(params) {
    return request({
      url: '/manager/statistics/revenue',
      method: 'get',
      params
    })
  },
  // 维修统计
  getRepairs(params) {
    return request({
      url: '/manager/statistics/repairs',
      method: 'get',
      params
    })
  },
  // 业主统计
  getOwners() {
    return request({
      url: '/manager/statistics/owners',
      method: 'get'
    })
  },
  // 预警信息
  getAlerts() {
    return request({
      url: '/manager/alerts',
      method: 'get'
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
