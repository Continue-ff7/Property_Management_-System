<template>
  <div class="create-complaint-page">
    <van-nav-bar 
      title="提交投诉" 
      left-arrow
      @click-left="$router.back()"
      fixed 
    />
    
    <div class="content">
      <van-form @submit="onSubmit">
        <van-cell-group inset>
          <van-field
            v-model="form.type"
            is-link
            readonly
            name="type"
            label="投诉类型"
            placeholder="请选择投诉类型"
            @click="showTypePicker = true"
            :rules="[{ required: true, message: '请选择投诉类型' }]"
          />
          
          <van-field
            v-model="form.content"
            rows="4"
            autosize
            type="textarea"
            name="content"
            label="投诉内容"
            maxlength="500"
            placeholder="请详细描述您的投诉内容"
            show-word-limit
            :rules="[{ required: true, message: '请输入投诉内容' }]"
          />
          
          <van-field name="uploader" label="上传图片">
            <template #input>
              <van-uploader
                v-model="fileList"
                :max-count="3"
                :after-read="afterRead"
              />
            </template>
          </van-field>
          
          <van-field
            v-model="form.contact_phone"
            readonly
            name="contact_phone"
            label="联系电话"
          />
        </van-cell-group>
        
        <div style="margin: 16px;">
          <van-button round block type="primary" native-type="submit" :loading="submitting">
            提交
          </van-button>
        </div>
      </van-form>
    </div>
    
    <!-- 类型选择器 -->
    <van-popup :show="showTypePicker" @update:show="showTypePicker = $event" position="bottom">
      <van-picker
        :columns="typeColumns"
        @confirm="onTypeConfirm"
        @cancel="showTypePicker = false"
      />
    </van-popup>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import { uploadAPI } from '@/api'

export default {
  name: 'CreateComplaint',
  setup() {
    const router = useRouter()
    const form = ref({
      type: '',
      content: '',
      contact_phone: ''
    })
    const fileList = ref([])
    const showTypePicker = ref(false)
    const submitting = ref(false)
    
    const typeColumns = [
      { text: '环境卫生', value: 'environment' },
      { text: '设施维修', value: 'facility' },
      { text: '噪音扰民', value: 'noise' },
      { text: '停车管理', value: 'parking' },
      { text: '安全问题', value: 'security' },
      { text: '服务态度', value: 'service' },
      { text: '其他', value: 'other' }
    ]
    
    const onTypeConfirm = ({ selectedOptions }) => {
      form.value.type = selectedOptions[0].text
      form.value.typeValue = selectedOptions[0].value
      showTypePicker.value = false
    }
    
    const afterRead = async (file) => {
      // 上传图片到服务器
      file.status = 'uploading'
      file.message = '上传中...'
      
      try {
        const res = await uploadAPI.upload(file.file)
        file.status = 'done'
        // 后端返回的是相对路径，需要拼接完整URL
        const fullUrl = `http://localhost:8088${res.url}`
        file.url = fullUrl  // 保存完整URL用于预览
        console.log('上传成功:', fullUrl)
      } catch (error) {
        file.status = 'failed'
        file.message = '上传失败'
        console.error('上传失败:', error)
      }
    }
    
    const onSubmit = async () => {
      if (submitting.value) return
      
      try {
        submitting.value = true
        
        const token = localStorage.getItem('token')
        // 从 fileList 中提取已上传的图片URL
        const images = fileList.value
          .filter(item => item.url)  // 只取上传成功的
          .map(item => item.url)
        
        const response = await fetch('http://localhost:8088/api/v1/complaints', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            type: form.value.typeValue,
            content: form.value.content,
            images: images
          })
        })
        
        if (!response.ok) {
          throw new Error('提交失败')
        }
        
        showSuccessToast('提交成功')
        router.back()
      } catch (error) {
        console.error('提交投诉失败:', error)
        showToast('提交失败，请重试')
      } finally {
        submitting.value = false
      }
    }
    
    onMounted(() => {
      // 获取用户信息
      const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
      form.value.contact_phone = userInfo.phone || ''
    })
    
    return {
      form,
      fileList,
      showTypePicker,
      submitting,
      typeColumns,
      onTypeConfirm,
      afterRead,
      onSubmit
    }
  }
}
</script>

<style scoped>
.create-complaint-page {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.content {
  padding: 56px 0 20px;
}
</style>
