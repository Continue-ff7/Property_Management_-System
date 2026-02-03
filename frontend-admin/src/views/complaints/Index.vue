<template>
  <div class="app-container">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card" @click="queryParams.status = null; handleQuery()">
          <div class="stat-content">
            <div class="stat-icon" style="background: #1890ff;">
              <el-icon :size="32"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总投诉</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card" @click="queryParams.status = 'pending'; handleQuery()">
          <div class="stat-content">
            <div class="stat-icon" style="background: #faad14;">
              <el-icon :size="32"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.pending }}</div>
              <div class="stat-label">待处理</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card" @click="queryParams.status = 'processing'; handleQuery()">
          <div class="stat-content">
            <div class="stat-icon" style="background: #1890ff;">
              <el-icon :size="32"><Loading /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.processing }}</div>
              <div class="stat-label">处理中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card" @click="queryParams.status = 'completed'; handleQuery()">
          <div class="stat-content">
            <div class="stat-icon" style="background: #52c41a;">
              <el-icon :size="32"><Select /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.completed }}</div>
              <div class="stat-label">已完成</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 投诉列表 -->
    <el-card shadow="never" class="table-card">
      <!-- 筛选栏 -->
      <div class="table-header">
        <el-form :inline="true" :model="queryParams" class="filter-form">
          <el-form-item label="状态筛选">
            <el-select 
              v-model="queryParams.status" 
              placeholder="全部状态" 
              clearable 
              style="width: 200px;"
              @change="handleQuery"
            >
              <el-option label="待处理" value="pending"></el-option>
              <el-option label="处理中" value="processing"></el-option>
              <el-option label="已完成" value="completed"></el-option>
            </el-select>
          </el-form-item>
        </el-form>
      </div>

      <!-- 表格 -->
      <el-table
        v-loading="loading"
        :data="complaintList"
        style="width: 100%"
        @row-click="handleRowClick"
        :header-cell-style="{background: '#f5f7fa', color: '#606266'}"
      >
        <el-table-column prop="id" label="ID" width="80" align="center"></el-table-column>
        <el-table-column prop="type" label="类型" width="120" align="center">
          <template #default="scope">
            <el-tag :type="getTypeTagType(scope.row.type)" size="small">{{ getTypeName(scope.row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="投诉内容" min-width="200" show-overflow-tooltip></el-table-column>
        <el-table-column prop="owner_name" label="投诉人" width="100" align="center"></el-table-column>
        <el-table-column prop="contact_phone" label="联系电话" width="130" align="center"></el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="scope">
            <el-tag :type="getStatusTagType(scope.row.status)" size="small">{{ getStatusName(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="160" align="center">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="scope">
            <el-button type="primary" size="small" @click.stop="handleDetail(scope.row)">处理</el-button>
            <el-button type="danger" size="small" @click.stop="handleDelete(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        :current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        class="pagination"
      />
    </el-card>

    <!-- 处理投诉对话框 -->
    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="750px"
      @close="handleClose"
      :close-on-click-modal="false"
    >
      <el-form :model="form" label-width="90px" v-if="currentComplaint" class="complaint-form">
        <!-- 投诉信息 -->
        <div class="info-section">
          <div class="section-header">
            <span class="section-title">投诉信息</span>
            <el-tag :type="getStatusTagType(currentComplaint.status)" size="large">
              {{ getStatusName(currentComplaint.status) }}
            </el-tag>
          </div>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="投诉类型">
                <el-tag :type="getTypeTagType(currentComplaint.type)">
                  {{ getTypeName(currentComplaint.type) }}
                </el-tag>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="提交时间">
                <span>{{ formatDateTime(currentComplaint.created_at) }}</span>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="投诉人">
                <span>{{ currentComplaint.owner_name }}</span>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="联系电话">
                <span>{{ currentComplaint.contact_phone }}</span>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="投诉内容">
            <div class="content-text">{{ currentComplaint.content }}</div>
          </el-form-item>
          
          <!-- 相关图片 -->
          <el-form-item label="相关图片" v-if="currentComplaint.images && currentComplaint.images.length > 0">
            <div class="image-list">
              <el-image
                v-for="(img, index) in currentComplaint.images"
                :key="index"
                :src="img"
                class="preview-image"
                :preview-src-list="currentComplaint.images"
                :initial-index="index"
                fit="cover"
              >
                <template #error>
                  <div class="image-error">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
            </div>
          </el-form-item>
          
          <!-- 业主评价 -->
          <el-form-item label="业主评价" v-if="currentComplaint.rating">
            <el-rate 
              v-model="currentComplaint.rating" 
              disabled 
              show-score
              text-color="#ff9900"
            />
          </el-form-item>
          
          <!-- 历史回复 -->
          <el-form-item label="历史回复" v-if="currentComplaint.reply">
            <div class="reply-text">{{ currentComplaint.reply }}</div>
          </el-form-item>
        </div>

        <el-divider></el-divider>

        <!-- 处理信息 -->
        <div class="handle-section">
          <div class="section-header">
            <span class="section-title">处理信息</span>
          </div>
          
          <el-form-item label="处理状态" required>
            <el-select v-model="form.status" placeholder="请选择状态">
              <el-option label="待处理" value="pending"></el-option>
              <el-option label="处理中" value="processing"></el-option>
              <el-option label="已完成" value="completed"></el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item label="回复内容" required>
            <el-input
              type="textarea"
              v-model="form.reply"
              :rows="5"
              placeholder="请输入回复内容，业主将收到您的回复通知"
              maxlength="500"
              show-word-limit
            ></el-input>
          </el-form-item>
        </div>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false" size="large">取消</el-button>
          <el-button type="primary" @click="submitHandle" :loading="submitting" size="large">
            {{ submitting ? '保存中...' : '保存处理结果' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { Picture, Document, Warning, Loading, Select } from '@element-plus/icons-vue'

export default {
  name: 'ComplaintManagement',
  components: {
    Picture,
    Document,
    Warning,
    Loading,
    Select
  },
  data() {
    return {
      loading: false,
      submitting: false,
      complaintList: [],
      pagination: {
        page: 1,
        pageSize: 10,
        total: 0
      },
      queryParams: {
        status: null
      },
      stats: {
        total: 0,
        pending: 0,
        processing: 0,
        completed: 0
      },
      dialogVisible: false,
      dialogTitle: '处理投诉',
      currentComplaint: null,
      form: {
        status: '',
        reply: ''
      }
    }
  },
  computed: {
    newComplaintNotification() {
      return this.$store.state.newComplaintNotification
    }
  },
  watch: {
    // 监听新投诉通知
    newComplaintNotification(newVal) {
      if (newVal) {
        console.log('收到新投诉通知:', newVal)
        // 刷新列表和统计
        this.getList()
        this.getStats()
        // 显示通知
        this.$message({
          message: `收到新投诉：${newVal.owner_name} 提交了${this.getTypeName(newVal.type)}投诉`,
          type: 'info',
          duration: 3000
        })
      }
    }
  },
  created() {
    this.getList()
    this.getStats()
  },
  methods: {
    async getList() {
      this.loading = true
      try {
        const token = localStorage.getItem('token')
        const params = new URLSearchParams()
        params.append('skip', (this.pagination.page - 1) * this.pagination.pageSize)
        params.append('limit', this.pagination.pageSize)
        if (this.queryParams.status) {
          params.append('status', this.queryParams.status)
        }
        
        const response = await fetch(`http://localhost:8088/api/v1/manager/complaints?${params}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (!response.ok) {
          throw new Error('加载失败')
        }
        
        const data = await response.json()
        this.complaintList = data.items || []
        this.pagination.total = data.total || 0
      } catch (error) {
        console.error('加载投诉列表失败:', error)
        this.$message.error('加载失败')
      } finally {
        this.loading = false
      }
    },
    async getStats() {
      try {
        const token = localStorage.getItem('token')
        const response = await fetch('http://localhost:8088/api/v1/manager/complaints/stats/summary', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (!response.ok) {
          throw new Error('加载失败')
        }
        
        this.stats = await response.json()
      } catch (error) {
        console.error('加载统计数据失败:', error)
      }
    },
    handleQuery() {
      this.pagination.page = 1
      this.getList()
    },
    resetQuery() {
      this.queryParams.status = null
      this.pagination.page = 1
      this.getList()
    },
    handleSizeChange(size) {
      this.pagination.pageSize = size
      this.pagination.page = 1
      this.getList()
    },
    handlePageChange(page) {
      this.pagination.page = page
      this.getList()
    },
    handleRowClick(row) {
      this.handleDetail(row)
    },
    handleDetail(row) {
      this.currentComplaint = { ...row }
      this.form = {
        status: row.status,
        reply: row.reply || ''
      }
      this.dialogVisible = true
    },
    async submitHandle() {
      if (this.submitting) return
      
      try {
        this.submitting = true
        const token = localStorage.getItem('token')
        
        const response = await fetch(`http://localhost:8088/api/v1/manager/complaints/${this.currentComplaint.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(this.form)
        })
        
        if (!response.ok) {
          throw new Error('更新失败')
        }
        
        this.$message.success('更新成功')
        this.dialogVisible = false
        this.getList()
        this.getStats()
      } catch (error) {
        console.error('更新投诉失败:', error)
        this.$message.error('更新失败，请重试')
      } finally {
        this.submitting = false
      }
    },
    handleClose() {
      this.currentComplaint = null
      this.form = {
        status: '',
        reply: ''
      }
    },
    async handleDelete(row) {
      try {
        await this.$confirm('确定要删除这条投诉吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const token = localStorage.getItem('token')
        const response = await fetch(`http://localhost:8088/api/v1/manager/complaints/${row.id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (!response.ok) {
          throw new Error('删除失败')
        }
        
        this.$message.success('删除成功')
        this.getList()
        this.getStats()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除投诉失败:', error)
          this.$message.error('删除失败，请重试')
        }
      }
    },
    getTypeName(type) {
      const names = {
        'environment': '环境卫生',
        'facility': '设施维修',
        'noise': '噪音扰民',
        'parking': '停车管理',
        'security': '安全问题',
        'service': '服务态度',
        'other': '其他'
      }
      return names[type] || type
    },
    getStatusName(status) {
      const names = {
        'pending': '待处理',
        'processing': '处理中',
        'completed': '已完成'
      }
      return names[status] || status
    },
    getTypeTagType(type) {
      const types = {
        'environment': 'success',
        'facility': 'warning',
        'noise': 'danger',
        'parking': 'primary',
        'security': 'danger',
        'service': 'warning',
        'other': 'info'
      }
      return types[type] || 'info'
    },
    getStatusTagType(status) {
      const types = {
        'pending': 'warning',
        'processing': 'primary',
        'completed': 'success'
      }
      return types[status] || 'info'
    },
    formatDateTime(dateStr) {
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.app-container {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 8px;
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 10px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: white;
  margin-right: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.table-card {
  border-radius: 8px;
}

.table-header {
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 16px;
}

.filter-form {
  margin: 0;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

.el-table {
  cursor: pointer;
}

.el-table :deep(tbody tr:hover) {
  background-color: #f5f7fa;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 对话框样式 */
.complaint-form {
  max-height: 65vh;
  overflow-y: auto;
}

.info-section,
.handle-section {
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.content-text {
  line-height: 1.6;
  color: #606266;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-all;
}

.reply-text {
  line-height: 1.8;
  color: #606266;
  background: #fafafa;
  padding: 16px;
  border-radius: 4px;
  font-size: 14px;
}

.image-list {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.preview-image {
  width: 100px;
  height: 100px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #dcdfe6;
}

.preview-image:hover {
  transform: scale(1.05);
  border-color: #409eff;
}

.image-error {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #c0c4cc;
  font-size: 24px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
