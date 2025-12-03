<template>
  <div class="page-container">
    <div class="card">
      <div class="toolbar">
        <el-input
          v-model="searchText"
          placeholder="搜索业主姓名或电话"
          style="width: 300px"
          clearable
          @clear="loadOwners"
        >
          <template #append>
            <el-button icon="Search" @click="loadOwners" />
          </template>
        </el-input>
        
        <el-button type="primary" icon="Plus" @click="showAddDialog">
          添加业主
        </el-button>
      </div>
      
      <el-table
        :data="owners"
        v-loading="loading"
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '正常' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button size="small" @click="viewProperties(row)">
                查看房产
              </el-button>
              <el-button size="small" type="primary" @click="showAssignDialog(row)">
                分配房产
              </el-button>
              <el-button size="small" @click="showEditDialog(row)">
                编辑
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="deleteOwner(row)"
                v-if="row.is_active"
              >
                删除
              </el-button>
            </div>
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
        style="margin-top: 20px; justify-content: flex-end"
      />
    </div>
    
    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" :disabled="isEdit" />
        </el-form-item>
        
        <el-form-item label="姓名" prop="name">
          <el-input v-model="formData.name" />
        </el-form-item>
        
        <el-form-item label="电话" prop="phone">
          <el-input v-model="formData.phone" />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="formData.password" type="password" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 房产列表对话框 -->
    <el-dialog
      v-model="propertiesDialogVisible"
      title="业主房产"
      width="600px"
    >
      <el-table :data="ownerProperties" v-loading="propertiesLoading">
        <el-table-column label="楼栋" prop="building_name" />
        <el-table-column label="单元" prop="unit" />
        <el-table-column label="楼层" prop="floor" />
        <el-table-column label="房间号" prop="room_number" />
        <el-table-column label="面积(㎡)" prop="area" />
      </el-table>
    </el-dialog>
    
    <!-- 分配房产对话框 -->
    <el-dialog
      v-model="assignDialogVisible"
      title="分配房产"
      width="700px"
    >
      <el-alert 
        title="提示" 
        type="info" 
        :closable="false"
        style="margin-bottom: 20px"
      >
        为{{ currentOwner?.name }}分配房产，请选择未分配的房产
      </el-alert>
      
      <el-table 
        :data="availableProperties" 
        v-loading="propertiesLoading"
        @selection-change="handlePropertySelection"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column label="楼栋" prop="building_name" />
        <el-table-column label="单元" prop="unit" />
        <el-table-column label="楼层" prop="floor" />
        <el-table-column label="房间号" prop="room_number" />
        <el-table-column label="面积(㎡)" prop="area" />
      </el-table>
      
      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAssignProperties" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ownerAPI, propertyAPI } from '@/api'

export default {
  name: 'Owners',
  setup() {
    const loading = ref(false)
    const searchText = ref('')
    const owners = ref([])
    const pagination = reactive({
      page: 1,
      pageSize: 20,
      total: 0
    })
    
    const dialogVisible = ref(false)
    const isEdit = ref(false)
    const submitting = ref(false)
    const formRef = ref(null)
    const formData = reactive({
      username: '',
      name: '',
      phone: '',
      email: '',
      password: ''
    })
    
    const propertiesDialogVisible = ref(false)
    const propertiesLoading = ref(false)
    const ownerProperties = ref([])
    
    const assignDialogVisible = ref(false)
    const availableProperties = ref([])
    const selectedProperties = ref([])
    const currentOwner = ref(null)
    
    const dialogTitle = computed(() => isEdit.value ? '编辑业主' : '添加业主')
    
    const rules = {
      username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
      name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
      phone: [
        { required: true, message: '请输入电话', trigger: 'blur' },
        { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
      ],
      password: [
        { 
          required: true, 
          message: '请输入密码', 
          trigger: 'blur',
          validator: (rule, value, callback) => {
            if (isEdit.value && !value) {
              callback() // 编辑时密码可为空
            } else if (!isEdit.value && !value) {
              callback(new Error('请输入密码'))
            } else {
              callback()
            }
          }
        }
      ]
    }
    
    // 加载业主列表
    const loadOwners = async () => {
      loading.value = true
      try {
        const params = {
          skip: (pagination.page - 1) * pagination.pageSize,
          limit: pagination.pageSize
        }
        if (searchText.value) {
          params.search = searchText.value
        }
        const data = await ownerAPI.getList(params)
        owners.value = data
      } catch (error) {
        console.error('加载失败:', error)
      } finally {
        loading.value = false
      }
    }
    
    // 分页处理
    const handleSizeChange = (size) => {
      pagination.pageSize = size
      loadOwners()
    }
    
    const handlePageChange = (page) => {
      pagination.page = page
      loadOwners()
    }
    
    // 显示添加对话框
    const showAddDialog = () => {
      isEdit.value = false
      Object.assign(formData, {
        username: '',
        name: '',
        phone: '',
        email: '',
        password: ''
      })
      dialogVisible.value = true
    }
    
    // 显示编辑对话框
    const showEditDialog = (row) => {
      isEdit.value = true
      Object.assign(formData, {
        id: row.id,
        username: row.username,
        name: row.name,
        phone: row.phone,
        email: row.email,
        password: ''
      })
      dialogVisible.value = true
    }
    
    // 提交表单
    const handleSubmit = async () => {
      if (!formRef.value) return
      
      await formRef.value.validate(async (valid) => {
        if (!valid) return
        
        submitting.value = true
        try {
          if (isEdit.value) {
            // 编辑时，只发送需要的字段
            const updateData = {
              name: formData.name,
              phone: formData.phone,
              email: formData.email
            }
            if (formData.password) {
              updateData.password = formData.password
            }
            await ownerAPI.update(formData.id, updateData)
            ElMessage.success('更新成功')
          } else {
            // 添加时，只发送需要的字段
            const createData = {
              username: formData.username,
              name: formData.name,
              phone: formData.phone,
              email: formData.email,
              password: formData.password
            }
            await ownerAPI.create(createData)
            ElMessage.success('添加成功')
          }
          dialogVisible.value = false
          loadOwners()
        } catch (error) {
          console.error('提交失败:', error)
          ElMessage.error(error.response?.data?.detail || '操作失败')
        } finally {
          submitting.value = false
        }
      })
    }
    
    // 删除业主
    const deleteOwner = async (row) => {
      try {
        const result = await ElMessageBox.confirm(
          `确定要删除业主「${row.name}」吗？如果该业主有关联房产，将自动解绑。`, 
          '提示', 
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        try {
          // 先尝试普通删除
          await ownerAPI.delete(row.id, false)
          ElMessage.success('删除成功')
          loadOwners()
        } catch (error) {
          // 如果有关联房产，提示是否强制删除
          if (error.response?.status === 400) {
            await ElMessageBox.confirm(
              error.response.data.detail + '，是否强制删除并解绑所有房产？', 
              '警告', 
              {
                confirmButtonText: '强制删除',
                cancelButtonText: '取消',
                type: 'error'
              }
            )
            await ownerAPI.delete(row.id, true)
            ElMessage.success('删除成功，相关房产已解绑')
            loadOwners()
          } else {
            throw error
          }
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除失败:', error)
          ElMessage.error(error.response?.data?.detail || '删除失败')
        }
      }
    }
    
    // 显示分配房产对话框
    const showAssignDialog = async (row) => {
      currentOwner.value = row
      assignDialogVisible.value = true
      propertiesLoading.value = true
      
      try {
        // 加载未分配的房产
        const data = await propertyAPI.getList({ unassigned: true })
        availableProperties.value = data
      } catch (error) {
        console.error('加载失败:', error)
        ElMessage.error('加载房产列表失败')
      } finally {
        propertiesLoading.value = false
      }
    }
    
    // 选择房产
    const handlePropertySelection = (selection) => {
      selectedProperties.value = selection
    }
    
    // 分配房产
    const handleAssignProperties = async () => {
      if (selectedProperties.value.length === 0) {
        ElMessage.warning('请选择要分配的房产')
        return
      }
      
      submitting.value = true
      try {
        // 批量分配房产
        for (const property of selectedProperties.value) {
          await propertyAPI.assignOwner(property.id, currentOwner.value.id)
        }
        ElMessage.success(`成功分配${selectedProperties.value.length}个房产`)
        assignDialogVisible.value = false
        selectedProperties.value = []
      } catch (error) {
        console.error('分配失败:', error)
        ElMessage.error(error.response?.data?.detail || '分配失败')
      } finally {
        submitting.value = false
      }
    }
    
    // 查看房产
    const viewProperties = async (row) => {
      propertiesDialogVisible.value = true
      propertiesLoading.value = true
      try {
        const data = await ownerAPI.getProperties(row.id)
        ownerProperties.value = data
      } catch (error) {
        console.error('加载失败:', error)
      } finally {
        propertiesLoading.value = false
      }
    }
    
    // 格式化日期
    const formatDate = (date) => {
      return new Date(date).toLocaleString('zh-CN')
    }
    
    // 初始化
    loadOwners()
    
    return {
      loading,
      searchText,
      owners,
      pagination,
      dialogVisible,
      dialogTitle,
      isEdit,
      submitting,
      formRef,
      formData,
      rules,
      propertiesDialogVisible,
      propertiesLoading,
      ownerProperties,
      assignDialogVisible,
      availableProperties,
      currentOwner,
      loadOwners,
      handleSizeChange,
      handlePageChange,
      showAddDialog,
      showEditDialog,
      handleSubmit,
      deleteOwner,
      viewProperties,
      showAssignDialog,
      handlePropertySelection,
      handleAssignProperties,
      formatDate
    }
  }
}
</script>
