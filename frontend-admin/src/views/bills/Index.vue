<template>
  <div class="page-container">
    <div class="card">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- 账单管理 -->
        <el-tab-pane label="账单管理" name="bills">
          <div class="toolbar">
            <el-select v-model="filterStatus" placeholder="账单状态" clearable style="width: 150px" @change="loadBills">
              <el-option label="全部" value="" />
              <el-option label="未支付" value="unpaid" />
              <el-option label="已支付" value="paid" />
              <el-option label="已逾期" value="overdue" />
            </el-select>
            
            <el-select v-model="filterFeeType" placeholder="费用类型" clearable style="width: 150px" @change="loadBills">
              <el-option label="全部" value="" />
              <el-option label="物业费" value="property" />
              <el-option label="停车费" value="parking" />
              <el-option label="水费" value="water" />
              <el-option label="电费" value="electricity" />
            </el-select>
            
            <div style="flex: 1"></div>
            
            <el-button type="primary" icon="Plus" @click="showCreateDialog">创建账单</el-button>
            <el-button type="success" icon="Document" @click="showBatchDialog">批量生成</el-button>
          </div>
          
          <el-table 
            v-if="activeTab === 'bills'" 
            :data="bills" 
            v-loading="loading"
            :key="'bills-table'"
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="owner_name" label="业主" width="120" />
            <el-table-column prop="property_info" label="房产" width="200" />
            <el-table-column label="费用类型" width="120">
              <template #default="{ row }">
                <el-tag>{{ getFeeTypeText(row.fee_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="金额" width="100">
              <template #default="{ row }">¥{{ Number(row.amount || 0).toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="billing_period" label="账期" width="120" />
            <el-table-column prop="due_date" label="截止日期" width="120" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="viewDetail(row)">详情</el-button>
                <el-button 
                  size="small" 
                  type="danger"
                  @click="deleteBill(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <el-pagination
            v-if="activeTab === 'bills'"
            :current-page="pagination.page"
            :page-size="pagination.pageSize"
            :total="pagination.total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handlePageChange"
            style="margin-top: 20px; justify-content: center"
          />
        </el-tab-pane>
        
        <!-- 收费标准 -->
        <el-tab-pane label="收费标准" name="standards">
          <el-button type="primary" icon="Plus" @click="showStandardDialog" style="margin-bottom: 20px">
            添加标准
          </el-button>
          
          <el-table 
            v-if="activeTab === 'standards'" 
            :data="standards" 
            v-loading="standardsLoading"
            :key="'standards-table'"
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column label="费用类型" width="150">
              <template #default="{ row }">
                <el-tag>{{ getFeeTypeText(row.fee_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="unit_price" label="单价（元/㎡/月）" width="180">
              <template #default="{ row }">¥{{ Number(row.unit_price || 0).toFixed(2) }}</template>
            </el-table-column>
            <el-table-column prop="description" label="说明" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="editStandard(row)">编辑</el-button>
                <el-button 
                  size="small" 
                  :type="row.is_active ? 'warning' : 'success'"
                  @click="toggleStandard(row)"
                >
                  {{ row.is_active ? '禁用' : '启用' }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <!-- 创建账单对话框 -->
    <el-dialog v-model="createDialogVisible" :title="isEdit ? '编辑账单' : '创建账单'" width="600px">
      <el-form :model="billForm" label-width="100px">
        <el-form-item label="业主">
          <el-select 
            v-model="billForm.owner_id" 
            placeholder="请选择业主" 
            filterable
            style="width: 100%"
            @change="handleOwnerChange"
          >
            <el-option
              v-for="owner in owners"
              :key="owner.id"
              :label="`${owner.name} (${owner.phone})`"
              :value="owner.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="房产">
          <el-select 
            v-model="billForm.property_id" 
            placeholder="请先选择业主" 
            :disabled="!billForm.owner_id"
            style="width: 100%"
          >
            <el-option
              v-for="property in ownerProperties"
              :key="property.id"
              :label="`${property.building_name} ${property.unit}单元 ${property.room_number} (¥${property.area}㎡)`"
              :value="property.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="费用类型">
          <el-select v-model="billForm.fee_type" style="width: 100%" @change="handleFeeTypeChange">
            <el-option label="物业费" value="property" />
            <el-option label="停车费" value="parking" />
            <el-option label="水费" value="water" />
            <el-option label="电费" value="electricity" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="金额">
          <el-input-number v-model="billForm.amount" :min="0" :precision="2" style="width: 100%" />
          <span v-if="suggestedAmount" style="color: #909399; font-size: 12px; margin-left: 10px">
            建议：¥{{ suggestedAmount.toFixed(2) }}
          </span>
        </el-form-item>
        
        <el-form-item label="账期">
          <el-input v-model="billForm.billing_period" placeholder="如: 2024年1月" />
        </el-form-item>
        
        <el-form-item label="截止日期">
          <el-date-picker v-model="billForm.due_date" type="date" style="width: 100%" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateBill" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 批量生成对话框 -->
    <el-dialog v-model="batchDialogVisible" title="批量生成账单" width="600px">
      <el-alert 
        title="说明" 
        type="info" 
        :closable="false"
        style="margin-bottom: 20px"
      >
        将根据收费标准，为所有已分配房产的业主自动生成账单。金额 = 房产面积 × 单价
      </el-alert>
      
      <el-form :model="batchForm" label-width="100px">
        <el-form-item label="费用类型">
          <el-select v-model="batchForm.fee_type" style="width: 100%">
            <el-option label="物业费" value="property" />
            <el-option label="停车费" value="parking" />
            <el-option label="水费" value="water" />
            <el-option label="电费" value="electricity" />
          </el-select>
        </el-form-item>
        <el-form-item label="账期">
          <el-input v-model="batchForm.billing_period" placeholder="如: 2024年1月" />
        </el-form-item>
        <el-form-item label="截止日期">
          <el-date-picker v-model="batchForm.due_date" type="date" style="width: 100%" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchCreate" :loading="submitting">确定生成</el-button>
      </template>
    </el-dialog>
    
    <!-- 收费标准对话框 -->
    <el-dialog v-model="standardDialogVisible" :title="isEditStandard ? '编辑标准' : '添加标准'" width="500px">
      <el-form :model="standardForm" label-width="120px">
        <el-form-item label="费用类型">
          <el-select v-model="standardForm.fee_type" style="width: 100%" :disabled="isEditStandard">
            <el-option label="物业费" value="property" />
            <el-option label="停车费" value="parking" />
            <el-option label="水费" value="water" />
            <el-option label="电费" value="electricity" />
          </el-select>
        </el-form-item>
        <el-form-item label="单价（元/㎡/月）">
          <el-input-number v-model="standardForm.unit_price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="standardForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="standardDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleStandardSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 账单详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="账单详情" width="600px">
      <el-descriptions :column="2" border v-if="currentBill">
        <el-descriptions-item label="账单ID">{{ currentBill.id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentBill.status)">
            {{ getStatusText(currentBill.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="业主">{{ currentBill.owner_name }}</el-descriptions-item>
        <el-descriptions-item label="房产">{{ currentBill.property_info }}</el-descriptions-item>
        <el-descriptions-item label="费用类型">
          <el-tag>{{ getFeeTypeText(currentBill.fee_type) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="金额">
          <span style="color: #f56c6c; font-weight: bold; font-size: 16px">
            ¥{{ Number(currentBill.amount || 0).toFixed(2) }}
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="账期">{{ currentBill.billing_period }}</el-descriptions-item>
        <el-descriptions-item label="截止日期">{{ currentBill.due_date }}</el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">{{ formatDate(currentBill.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="支付时间" :span="2" v-if="currentBill.paid_at">
          {{ formatDate(currentBill.paid_at) }}
        </el-descriptions-item>
      </el-descriptions>
      
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { billAPI, ownerAPI, propertyAPI } from '@/api'

export default {
  name: 'Bills',
  setup() {
    const activeTab = ref('bills')
    const loading = ref(false)
    const standardsLoading = ref(false)
    const submitting = ref(false)
    
    const filterStatus = ref('')
    const filterFeeType = ref('')
    const bills = ref([])
    const standards = ref([])
    const owners = ref([])
    const ownerProperties = ref([])
    
    const pagination = reactive({
      page: 1,
      pageSize: 20,
      total: 0
    })
    
    const batchDialogVisible = ref(false)
    const createDialogVisible = ref(false)
    const standardDialogVisible = ref(false)
    const detailDialogVisible = ref(false)
    
    const isEdit = ref(false)
    const isEditStandard = ref(false)
    const currentBill = ref(null)
    const suggestedAmount = ref(0)
    
    const billForm = reactive({
      owner_id: null,
      property_id: null,
      fee_type: 'property',
      amount: 0,
      billing_period: '',
      due_date: null
    })
    
    const batchForm = reactive({
      fee_type: 'property',
      billing_period: '',
      due_date: null
    })
    
    const standardForm = reactive({
      fee_type: 'property',
      unit_price: 0,
      description: ''
    })
    
    // 加载账单列表
    const loadBills = async () => {
      loading.value = true
      try {
        const params = {
          skip: (pagination.page - 1) * pagination.pageSize,
          limit: pagination.pageSize
        }
        if (filterStatus.value) params.status = filterStatus.value
        if (filterFeeType.value) params.fee_type = filterFeeType.value
        
        const data = await billAPI.getList(params)
        bills.value = data
        // 如果后端返回 total，则更新
        if (data.total !== undefined) {
          pagination.total = data.total
        }
      } catch (error) {
        console.error('加载失败:', error)
        ElMessage.error('加载账单失败')
      } finally {
        loading.value = false
      }
    }
    
    // 加载收费标准
    const loadStandards = async () => {
      standardsLoading.value = true
      try {
        const data = await billAPI.getStandards()
        standards.value = data
      } catch (error) {
        console.error('加载失败:', error)
        ElMessage.error('加载收费标准失败')
      } finally {
        standardsLoading.value = false
      }
    }
    
    // 加载业主列表
    const loadOwners = async () => {
      try {
        const data = await ownerAPI.getList({ limit: 1000 })
        owners.value = data
      } catch (error) {
        console.error('加载业主失败:', error)
      }
    }
    
    // 业主变化时加载其房产
    const handleOwnerChange = async (ownerId) => {
      billForm.property_id = null
      ownerProperties.value = []
      suggestedAmount.value = 0
      
      if (!ownerId) return
      
      try {
        const data = await ownerAPI.getProperties(ownerId)
        ownerProperties.value = data
      } catch (error) {
        console.error('加载房产失败:', error)
        ElMessage.error('加载业主房产失败')
      }
    }
    
    // 费用类型变化时计算建议金额
    const handleFeeTypeChange = () => {
      if (!billForm.property_id || !billForm.fee_type) return
      
      const property = ownerProperties.value.find(p => p.id === billForm.property_id)
      const standard = standards.value.find(s => s.fee_type === billForm.fee_type && s.is_active)
      
      if (property && standard) {
        suggestedAmount.value = property.area * standard.unit_price
        billForm.amount = suggestedAmount.value
      }
    }
    
    // 显示创建对话框
    const showCreateDialog = async () => {
      isEdit.value = false
      Object.assign(billForm, {
        owner_id: null,
        property_id: null,
        fee_type: 'property',
        amount: 0,
        billing_period: '',
        due_date: null
      })
      ownerProperties.value = []
      suggestedAmount.value = 0
      
      await loadOwners()
      await loadStandards()
      createDialogVisible.value = true
    }
    
    // 创建账单
    const handleCreateBill = async () => {
      if (!billForm.owner_id || !billForm.property_id || !billForm.billing_period || !billForm.due_date) {
        ElMessage.warning('请填写完整信息')
        return
      }
      
      submitting.value = true
      try {
        await billAPI.create({
          owner_id: billForm.owner_id,
          property_id: billForm.property_id,
          fee_type: billForm.fee_type,
          amount: billForm.amount,
          billing_period: billForm.billing_period,
          due_date: billForm.due_date.toISOString().split('T')[0]
        })
        ElMessage.success('创建成功')
        createDialogVisible.value = false
        loadBills()
      } catch (error) {
        console.error('创建失败:', error)
        ElMessage.error(error.response?.data?.detail || '创建失败')
      } finally {
        submitting.value = false
      }
    }
    
    // 显示批量生成对话框
    const showBatchDialog = () => {
      Object.assign(batchForm, {
        fee_type: 'property',
        billing_period: '',
        due_date: null
      })
      batchDialogVisible.value = true
    }
    
    // 批量生成账单
    const handleBatchCreate = async () => {
      if (!batchForm.billing_period || !batchForm.due_date) {
        ElMessage.warning('请填写完整信息')
        return
      }
      
      submitting.value = true
      try {
        const result = await billAPI.batchCreate({
          fee_type: batchForm.fee_type,
          billing_period: batchForm.billing_period,
          due_date: batchForm.due_date.toISOString().split('T')[0]
        })
        ElMessage.success(result.message || `成功生成 ${result.created} 条账单`)
        batchDialogVisible.value = false
        loadBills()
      } catch (error) {
        console.error('生成失败:', error)
        ElMessage.error(error.response?.data?.detail || '生成失败')
      } finally {
        submitting.value = false
      }
    }
    
    // 显示收费标准对话框
    const showStandardDialog = () => {
      isEditStandard.value = false
      Object.assign(standardForm, {
        fee_type: 'property',
        unit_price: 0,
        description: ''
      })
      standardDialogVisible.value = true
    }
    
    // 编辑收费标准
    const editStandard = (row) => {
      isEditStandard.value = true
      Object.assign(standardForm, {
        id: row.id,
        fee_type: row.fee_type,
        unit_price: row.unit_price,
        description: row.description
      })
      standardDialogVisible.value = true
    }
    
    // 提交收费标准
    const handleStandardSubmit = async () => {
      if (!standardForm.unit_price) {
        ElMessage.warning('请输入单价')
        return
      }
      
      submitting.value = true
      try {
        if (isEditStandard.value) {
          await billAPI.updateStandard(standardForm.id, {
            unit_price: standardForm.unit_price,
            description: standardForm.description
          })
          ElMessage.success('更新成功')
        } else {
          await billAPI.createStandard(standardForm)
          ElMessage.success('创建成功')
        }
        standardDialogVisible.value = false
        loadStandards()
      } catch (error) {
        console.error('操作失败:', error)
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        submitting.value = false
      }
    }
    
    // 切换标准状态
    const toggleStandard = async (row) => {
      try {
        await billAPI.updateStandard(row.id, {
          is_active: !row.is_active
        })
        ElMessage.success(`已${!row.is_active ? '启用' : '禁用'}`)
        loadStandards()
      } catch (error) {
        console.error('操作失败:', error)
        ElMessage.error('操作失败')
      }
    }
    
    // 删除账单
    const deleteBill = async (row) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除此账单吗？`,
          '提示',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await billAPI.delete(row.id)
        ElMessage.success('删除成功')
        loadBills()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除失败:', error)
          ElMessage.error('删除失败')
        }
      }
    }
    
    // 查看详情
    const viewDetail = (row) => {
      currentBill.value = row
      detailDialogVisible.value = true
    }
    
    // Tab切换
    const handleTabChange = (tabName) => {
      if (tabName === 'standards' && standards.value.length === 0) {
        loadStandards()
      }
    }
    
    // 分页处理
    const handleSizeChange = (size) => {
      pagination.pageSize = size
      loadBills()
    }
    
    const handlePageChange = (page) => {
      pagination.page = page
      loadBills()
    }
    
    const getFeeTypeText = (type) => {
      const map = { property: '物业费', parking: '停车费', water: '水费', electricity: '电费' }
      return map[type] || type
    }
    
    const getStatusType = (status) => {
      const map = { unpaid: 'warning', paid: 'success', overdue: 'danger' }
      return map[status] || 'info'
    }
    
    const getStatusText = (status) => {
      const map = { unpaid: '未支付', paid: '已支付', overdue: '已逾期' }
      return map[status] || status
    }
    
    const formatDate = (date) => {
      if (!date) return '-'
      return new Date(date).toLocaleString('zh-CN')
    }
    
    onMounted(() => {
      loadBills()
    })
    
    return {
      activeTab, loading, standardsLoading, submitting,
      filterStatus, filterFeeType, bills, standards, owners, ownerProperties,
      pagination, batchDialogVisible, createDialogVisible, standardDialogVisible, detailDialogVisible,
      isEdit, isEditStandard, currentBill, suggestedAmount,
      billForm, batchForm, standardForm,
      loadBills, loadStandards, loadOwners, handleOwnerChange, handleFeeTypeChange,
      showCreateDialog, handleCreateBill, showBatchDialog, handleBatchCreate,
      showStandardDialog, editStandard, handleStandardSubmit, toggleStandard,
      deleteBill, viewDetail, handleTabChange,
      handleSizeChange, handlePageChange,
      getFeeTypeText, getStatusType, getStatusText, formatDate
    }
  }
}
</script>
