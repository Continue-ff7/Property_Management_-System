<template>
  <div class="page-container">
    <div class="card">
      <div class="toolbar">
        <div>
          <el-select v-model="filterStatus" placeholder="工单状态" clearable style="width: 150px; margin-right: 10px" @change="loadRepairs">
            <el-option label="全部" value="" />
            <el-option label="待处理" value="pending" />
            <el-option label="已分配" value="assigned" />
            <el-option label="维修中" value="in_progress" />
            <el-option label="已完成" value="completed" />
          </el-select>
          
          <el-select v-model="filterUrgency" placeholder="紧急程度" clearable style="width: 150px" @change="loadRepairs">
            <el-option label="全部" value="" />
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </div>
      </div>
      
      <el-table :data="repairs" v-loading="loading">
        <el-table-column prop="order_number" label="工单号" width="180" />
        <el-table-column prop="owner_name" label="业主" width="100" />
        <el-table-column prop="property_info" label="房产" width="150" />
        <el-table-column prop="description" label="问题描述" show-overflow-tooltip />
        <el-table-column label="紧急程度" width="100">
          <template #default="{ row }">
            <el-tag :type="getUrgencyType(row.urgency_level)">
              {{ getUrgencyText(row.urgency_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="maintenance_worker_name" label="维修人员" width="100" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">详情</el-button>
            <el-button
              size="small"
              type="primary"
              @click="showAssignDialog(row)"
              v-if="row.status === 'pending'"
            >
              分配
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        :current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </div>
    
    <!-- 分配对话框 -->
    <el-dialog v-model="assignDialogVisible" title="分配维修人员" width="400px">
      <el-form>
        <el-form-item label="维修人员">
          <el-select v-model="assignWorkerId" placeholder="请选择" style="width: 100%">
            <el-option
              v-for="worker in workers"
              :key="worker.id"
              :label="worker.name"
              :value="worker.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAssign" :loading="assigning">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="工单详情" width="600px">
      <el-descriptions :column="2" border v-if="currentRepair">
        <el-descriptions-item label="工单号">{{ currentRepair.order_number }}</el-descriptions-item>
        <el-descriptions-item label="业主">{{ currentRepair.owner_name }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ currentRepair.owner_phone }}</el-descriptions-item>
        <el-descriptions-item label="房产">{{ currentRepair.property_info }}</el-descriptions-item>
        <el-descriptions-item label="紧急程度">
          <el-tag :type="getUrgencyType(currentRepair.urgency_level)">
            {{ getUrgencyText(currentRepair.urgency_level) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentRepair.status)">
            {{ getStatusText(currentRepair.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="问题描述" :span="2">
          {{ currentRepair.description }}
        </el-descriptions-item>
        <el-descriptions-item label="报修图片" :span="2">
          <el-image
            v-for="(img, index) in currentRepair.images"
            :key="index"
            :src="getImageUrl(img)"
            style="width: 100px; height: 100px; margin-right: 10px"
            fit="cover"
            :preview-src-list="currentRepair.images.map(getImageUrl)"
          />
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { repairAPI, maintenanceAPI } from '@/api'

export default {
  name: 'Repairs',
  setup() {
    const loading = ref(false)
    const filterStatus = ref('')
    const filterUrgency = ref('')
    const repairs = ref([])
    const workers = ref([])
    const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
    
    const assignDialogVisible = ref(false)
    const detailDialogVisible = ref(false)
    const currentRepair = ref(null)
    const assignWorkerId = ref(null)
    const assigning = ref(false)
    
    const loadRepairs = async () => {
      loading.value = true
      try {
        const params = {
          skip: (pagination.page - 1) * pagination.pageSize,
          limit: pagination.pageSize
        }
        if (filterStatus.value) params.status = filterStatus.value
        if (filterUrgency.value) params.urgency_level = filterUrgency.value
        
        const data = await repairAPI.getList(params)
        repairs.value = data
      } catch (error) {
        console.error('加载失败:', error)
      } finally {
        loading.value = false
      }
    }
    
    const loadWorkers = async () => {
      try {
        const data = await maintenanceAPI.getList()
        workers.value = data
      } catch (error) {
        console.error('加载维修人员失败:', error)
      }
    }
    
    const handlePageChange = (page) => {
      pagination.page = page
      loadRepairs()
    }
    
    const showAssignDialog = (row) => {
      currentRepair.value = row
      assignWorkerId.value = null
      assignDialogVisible.value = true
    }
    
    const handleAssign = async () => {
      if (!assignWorkerId.value) {
        ElMessage.warning('请选择维修人员')
        return
      }
      
      assigning.value = true
      try {
        await repairAPI.assign(currentRepair.value.id, { maintenance_worker_id: assignWorkerId.value })
        ElMessage.success('分配成功')
        assignDialogVisible.value = false
        loadRepairs()
      } catch (error) {
        console.error('分配失败:', error)
      } finally {
        assigning.value = false
      }
    }
    
    const viewDetail = (row) => {
      currentRepair.value = row
      detailDialogVisible.value = true
    }
    
    const getImageUrl = (url) => {
      return url.startsWith('http') ? url : `http://localhost:8000${url}`
    }
    
    const getUrgencyType = (level) => {
      const map = { low: 'info', medium: 'warning', high: 'danger', urgent: 'danger' }
      return map[level] || 'info'
    }
    
    const getUrgencyText = (level) => {
      const map = { low: '低', medium: '中', high: '高', urgent: '紧急' }
      return map[level] || level
    }
    
    const getStatusType = (status) => {
      const map = { pending: 'warning', assigned: 'primary', in_progress: 'primary', completed: 'success' }
      return map[status] || 'info'
    }
    
    const getStatusText = (status) => {
      const map = { pending: '待处理', assigned: '已分配', in_progress: '维修中', completed: '已完成' }
      return map[status] || status
    }
    
    onMounted(() => {
      loadRepairs()
      loadWorkers()
    })
    
    return {
      loading, filterStatus, filterUrgency, repairs, pagination, workers,
      assignDialogVisible, detailDialogVisible, currentRepair, assignWorkerId, assigning,
      loadRepairs, handlePageChange, showAssignDialog, handleAssign, viewDetail,
      getImageUrl, getUrgencyType, getUrgencyText, getStatusType, getStatusText
    }
  }
}
</script>
