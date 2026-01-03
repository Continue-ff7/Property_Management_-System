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
        <!-- ✅ 新增：维修费用 -->
        <el-table-column label="维修费用" width="120">
          <template #default="{ row }">
            <span v-if="row.repair_cost !== null && row.repair_cost !== undefined">
              ￥{{ row.repair_cost }}
              <el-tag v-if="row.repair_cost > 0 && row.cost_paid" type="success" size="small" style="margin-left: 5px">已付</el-tag>
              <el-tag v-else-if="row.repair_cost > 0 && !row.cost_paid" type="danger" size="small" style="margin-left: 5px">未付</el-tag>
            </span>
            <span v-else style="color: #909399">-</span>
          </template>
        </el-table-column>
        <el-table-column label="紧急程度" width="100">
          <template #default="{ row }">
            <el-tag :type="getUrgencyType(row.urgency_level)">
              {{ getUrgencyText(row.urgency_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row)">
              {{ getStatusText(row) }}
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
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(row)"
            >
              删除
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
    <el-dialog v-model="detailDialogVisible" title="工单详情" width="700px">
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
          <el-tag :type="getStatusType(currentRepair)">
            {{ getStatusText(currentRepair) }}
          </el-tag>
        </el-descriptions-item>
        
        <!-- ✅ 修改：支持新状态，显示维修费用 -->
        <el-descriptions-item label="维修费用" v-if="currentRepair.status === 'pending_payment' || currentRepair.status === 'pending_evaluation' || currentRepair.status === 'finished' || currentRepair.status === 'completed'">
          <span v-if="currentRepair.repair_cost !== null && currentRepair.repair_cost !== undefined">
            ￥{{ currentRepair.repair_cost }}
            <el-tag v-if="currentRepair.status === 'finished' || (currentRepair.repair_cost > 0 && currentRepair.cost_paid)" type="success" size="small" style="margin-left: 8px">已支付</el-tag>
            <el-tag v-else-if="currentRepair.status === 'pending_payment' || (currentRepair.repair_cost > 0 && !currentRepair.cost_paid)" type="danger" size="small" style="margin-left: 8px">待支付</el-tag>
            <el-tag v-else type="info" size="small" style="margin-left: 8px">免费维修</el-tag>
          </span>
          <span v-else style="color: #909399">未设置</span>
        </el-descriptions-item>
        
        <!-- ✅ 新增：维修人员信息 -->
        <el-descriptions-item label="维修人员" v-if="currentRepair.maintenance_worker_name">
          {{ currentRepair.maintenance_worker_name }}
        </el-descriptions-item>
        <el-descriptions-item label="工单状态" v-else>
          <el-tag type="info">未分配</el-tag>
        </el-descriptions-item>
        
        <el-descriptions-item label="问题描述" :span="2">
          {{ currentRepair.description }}
        </el-descriptions-item>
        
        <el-descriptions-item label="报修图片" :span="2" v-if="currentRepair.images && currentRepair.images.length > 0">
          <el-image
            v-for="(img, index) in currentRepair.images"
            :key="index"
            :src="getImageUrl(img)"
            style="width: 100px; height: 100px; margin-right: 10px"
            fit="cover"
            :preview-src-list="currentRepair.images.map(getImageUrl)"
          />
        </el-descriptions-item>
        
        <!-- ✅ 新增：维修完成照片 -->
        <el-descriptions-item label="维修完成照片" :span="2" v-if="currentRepair.repair_images && currentRepair.repair_images.length > 0">
          <el-image
            v-for="(img, index) in currentRepair.repair_images"
            :key="'repair-' + index"
            :src="getImageUrl(img)"
            style="width: 100px; height: 100px; margin-right: 10px"
            fit="cover"
            :preview-src-list="currentRepair.repair_images.map(getImageUrl)"
          />
        </el-descriptions-item>
        
        <!-- ✅ 新增：时间线 -->
        <el-descriptions-item label="提交时间" :span="2">
          {{ formatDate(currentRepair.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="分配时间" :span="2" v-if="currentRepair.assigned_at">
          {{ formatDate(currentRepair.assigned_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="开始维修时间" :span="2" v-if="currentRepair.started_at">
          {{ formatDate(currentRepair.started_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="完成时间" :span="2" v-if="currentRepair.completed_at">
          {{ formatDate(currentRepair.completed_at) }}
        </el-descriptions-item>
        
        <!-- ✅ 新增：评价信息 -->
        <el-descriptions-item label="业主评价" :span="2" v-if="currentRepair.rating">
          <div>
            <el-rate v-model="currentRepair.rating" disabled />
            <p style="margin-top: 8px; color: #606266" v-if="currentRepair.comment">
              {{ currentRepair.comment }}
            </p>
          </div>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { repairAPI, maintenanceAPI } from '@/api'
import { useStore } from 'vuex'

export default {
  name: 'Repairs',
  setup() {
    const store = useStore()
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
    
    const handleDelete = async (row) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除工单 ${row.order_number} 吗？删除后业主将收到拒绝通知。`,
          '警告',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
        
        await repairAPI.deleteRepair(row.id)
        ElMessage.success('工单已删除')
        loadRepairs()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除失败:', error)
        }
      }
    }
    
    const getImageUrl = (url) => {
      if (!url) return ''
      if (url.startsWith('http://') || url.startsWith('https://')) {
        return url
      }
      return `http://localhost:8088${url}`
    }
    
    const getUrgencyType = (level) => {
      const map = { low: 'info', medium: 'warning', high: 'danger', urgent: 'danger' }
      return map[level] || 'info'
    }
    
    const getUrgencyText = (level) => {
      const map = { low: '低', medium: '中', high: '高', urgent: '紧急' }
      return map[level] || level
    }
    
    // ✅ 简化：直接根据状态返回类型
    const getStatusType = (repair) => {
      const statusMap = {
        'pending': 'warning',
        'assigned': 'primary',
        'in_progress': 'primary',
        'pending_payment': 'danger',
        'pending_evaluation': 'primary',
        'finished': 'success',
        'cancelled': 'info',
        'completed': 'success'  // 兼容旧数据
      }
      return statusMap[repair.status || repair] || 'info'
    }
    
    // ✅ 简化：直接根据状态返回文本
    const getStatusText = (repair) => {
      const statusMap = {
        'pending': '待处理',
        'assigned': '已分配',
        'in_progress': '维修中',
        'pending_payment': '待支付',
        'pending_evaluation': '待评价',
        'finished': '已完结',
        'cancelled': '已取消',
        'completed': '已完成'  // 兼容旧数据
      }
      return statusMap[repair.status || repair] || repair.status || repair
    }
    
    // ✅ 新增：格式化日期时间
    const formatDate = (dateStr) => {
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hour = String(date.getHours()).padStart(2, '0')
      const minute = String(date.getMinutes()).padStart(2, '0')
      const second = String(date.getSeconds()).padStart(2, '0')
      return `${year}-${month}-${day} ${hour}:${minute}:${second}`
    }
    
    onMounted(() => {
      loadRepairs()
      loadWorkers()
    })
    
    // 监听Vuex中的新报修通知
    watch(
      () => store.state.newRepairNotification,
      (newVal) => {
        if (newVal) {
          // 收到新报修通知，刷新列表
          loadRepairs()
        }
      }
    )
    
    // 监听Vuex中的工单状态更新通知（维修人员开始/完成维修）
    watch(
      () => store.state.repairStatusUpdate,
      (newVal) => {
        if (newVal) {
          // 收到工单状态更新，刷新列表
          console.log('管理员端收到工单状态更新，刷新列表')
          loadRepairs()
        }
      }
    )
    
    return {
      loading, filterStatus, filterUrgency, repairs, pagination, workers,
      assignDialogVisible, detailDialogVisible, currentRepair, assignWorkerId, assigning,
      loadRepairs, handlePageChange, showAssignDialog, handleAssign, handleDelete, viewDetail,
      getImageUrl, getUrgencyType, getUrgencyText, getStatusType, getStatusText, formatDate
    }
  }
}
</script>
