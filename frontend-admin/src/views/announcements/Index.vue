<template>
  <div class="page-container">
    <div class="card">
      <el-button type="primary" icon="Plus" @click="showDialog" style="margin-bottom: 20px">
        发布公告
      </el-button>
      
      <el-table :data="announcements" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="publisher_name" label="发布人" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_published ? 'success' : 'info'">
              {{ row.is_published ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发布时间" width="180">
          <template #default="{ row }">
            {{ row.published_at ? formatDate(row.published_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">查看</el-button>
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteAnnouncement(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px">
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="80px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="formData.title" />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="formData.content" type="textarea" :rows="10" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">发布</el-button>
      </template>
    </el-dialog>
    
    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="公告详情" width="700px">
      <div v-if="currentAnnouncement">
        <h3>{{ currentAnnouncement.title }}</h3>
        <p style="color: #999; font-size: 14px; margin: 10px 0">
          发布人: {{ currentAnnouncement.publisher_name }} | 
          发布时间: {{ formatDate(currentAnnouncement.published_at) }}
        </p>
        <div style="white-space: pre-wrap; line-height: 1.8">
          {{ currentAnnouncement.content }}
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { announcementAPI } from '@/api'

export default {
  name: 'Announcements',
  setup() {
    const loading = ref(false)
    const announcements = ref([])
    const dialogVisible = ref(false)
    const detailDialogVisible = ref(false)
    const isEdit = ref(false)
    const formRef = ref(null)
    const currentAnnouncement = ref(null)
    
    const formData = reactive({
      title: '',
      content: ''
    })
    
    const rules = {
      title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
      content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
    }
    
    const dialogTitle = computed(() => isEdit.value ? '编辑公告' : '发布公告')
    
    const loadAnnouncements = async () => {
      loading.value = true
      try {
        const data = await announcementAPI.getList()
        announcements.value = data
      } catch (error) {
        console.error('加载失败:', error)
      } finally {
        loading.value = false
      }
    }
    
    const showDialog = () => {
      isEdit.value = false
      Object.assign(formData, { title: '', content: '' })
      dialogVisible.value = true
    }
    
    const showEditDialog = (row) => {
      isEdit.value = true
      Object.assign(formData, {
        id: row.id,
        title: row.title,
        content: row.content
      })
      dialogVisible.value = true
    }
    
    const handleSubmit = async () => {
      if (!formRef.value) return
      
      await formRef.value.validate(async (valid) => {
        if (!valid) return
        
        try {
          if (isEdit.value) {
            await announcementAPI.update(formData.id, formData)
            ElMessage.success('更新成功')
          } else {
            await announcementAPI.create(formData)
            ElMessage.success('发布成功')
          }
          dialogVisible.value = false
          loadAnnouncements()
        } catch (error) {
          console.error('提交失败:', error)
        }
      })
    }
    
    const viewDetail = (row) => {
      currentAnnouncement.value = row
      detailDialogVisible.value = true
    }
    
    const deleteAnnouncement = async (row) => {
      try {
        await ElMessageBox.confirm('确定要删除该公告吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await announcementAPI.delete(row.id)
        ElMessage.success('删除成功')
        loadAnnouncements()
      } catch (error) {
        // 取消操作
      }
    }
    
    const formatDate = (date) => {
      return new Date(date).toLocaleString('zh-CN')
    }
    
    onMounted(() => {
      loadAnnouncements()
    })
    
    return {
      loading, announcements, dialogVisible, detailDialogVisible, dialogTitle,
      isEdit, formRef, formData, rules, currentAnnouncement,
      loadAnnouncements, showDialog, showEditDialog, handleSubmit,
      viewDetail, deleteAnnouncement, formatDate
    }
  }
}
</script>
