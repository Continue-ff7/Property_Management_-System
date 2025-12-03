<template>
  <div class="page-container">
    <div class="card">
      <el-button type="primary" icon="Plus" @click="showDialog" style="margin-bottom: 20px">
        添加维修人员
      </el-button>
      
      <el-table :data="workers" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteWorker(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="80px">
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
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { maintenanceAPI } from '@/api'

export default {
  name: 'Maintenance',
  setup() {
    const loading = ref(false)
    const workers = ref([])
    const dialogVisible = ref(false)
    const isEdit = ref(false)
    const formRef = ref(null)
    
    const formData = reactive({
      username: '',
      name: '',
      phone: '',
      email: '',
      password: '',
      role: 'maintenance'
    })
    
    const rules = {
      username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
      name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
      phone: [{ required: true, message: '请输入电话', trigger: 'blur' }],
      password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
    }
    
    const dialogTitle = computed(() => isEdit.value ? '编辑维修人员' : '添加维修人员')
    
    const loadWorkers = async () => {
      loading.value = true
      try {
        const data = await maintenanceAPI.getList()
        workers.value = data
      } catch (error) {
        console.error('加载失败:', error)
      } finally {
        loading.value = false
      }
    }
    
    const showDialog = () => {
      isEdit.value = false
      Object.assign(formData, {
        username: '',
        name: '',
        phone: '',
        email: '',
        password: '',
        role: 'maintenance'
      })
      dialogVisible.value = true
    }
    
    const showEditDialog = (row) => {
      isEdit.value = true
      Object.assign(formData, {
        id: row.id,
        username: row.username,
        name: row.name,
        phone: row.phone,
        email: row.email,
        password: '',
        role: 'maintenance'
      })
      dialogVisible.value = true
    }
    
    const handleSubmit = async () => {
      if (!formRef.value) return
      
      await formRef.value.validate(async (valid) => {
        if (!valid) return
        
        try {
          if (isEdit.value) {
            await maintenanceAPI.update(formData.id, formData)
            ElMessage.success('更新成功')
          } else {
            await maintenanceAPI.create(formData)
            ElMessage.success('添加成功')
          }
          dialogVisible.value = false
          loadWorkers()
        } catch (error) {
          console.error('提交失败:', error)
        }
      })
    }
    
    // 删除维修人员
    const deleteWorker = async (row) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除维修人员「${row.name}」吗？如果该维修人员有关联工单，将自动解绑。`, 
          '提示', 
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        try {
          // 先尝试普通删除
          await maintenanceAPI.delete(row.id, false)
          ElMessage.success('删除成功')
          loadWorkers()
        } catch (error) {
          // 如果有关联工单，提示是否强制删除
          if (error.response?.status === 400) {
            await ElMessageBox.confirm(
              error.response.data.detail + '，是否强制删除并解绑所有工单？', 
              '警告', 
              {
                confirmButtonText: '强制删除',
                cancelButtonText: '取消',
                type: 'error'
              }
            )
            await maintenanceAPI.delete(row.id, true)
            ElMessage.success('删除成功，相关工单已解绑')
            loadWorkers()
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
    
    onMounted(() => {
      loadWorkers()
    })
    
    return {
      loading, workers, dialogVisible, dialogTitle, isEdit, formRef, formData, rules,
      loadWorkers, showDialog, showEditDialog, handleSubmit, deleteWorker
    }
  }
}
</script>
