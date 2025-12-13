<template>
  <div class="complete-page">
    <van-nav-bar
      title="完成维修"
      left-arrow
      @click-left="$router.back()"
      fixed
    />
    
    <div class="content">
      <van-form @submit="onSubmit">
        <!-- 工单信息 -->
        <div class="info-section">
          <div class="order-info">
            <span class="label">工单号：</span>
            <span class="value">#{{ workorder?.order_number }}</span>
          </div>
          <div class="order-info">
            <span class="label">报修地址：</span>
            <span class="value">{{ workorder?.property_info }}</span>
          </div>
        </div>
        
        <!-- 上传维修现场照片 -->
        <van-cell-group inset>
          <van-cell title="上传维修完成照片" />
        </van-cell-group>
        
        <div class="upload-section">
          <van-uploader
            v-model="fileList"
            :max-count="5"
            :after-read="afterRead"
            multiple
          >
            <div class="upload-btn">
              <van-icon name="photograph" size="32" color="#4A90E2" />
              <div class="upload-text">点击上传</div>
              <div class="upload-tips">最多5张</div>
            </div>
          </van-uploader>
        </div>
        
        <!-- 维修说明 -->
        <van-cell-group inset style="margin-top: 16px;">
          <van-field
            v-model="form.note"
            rows="4"
            autosize
            type="textarea"
            maxlength="200"
            placeholder="请输入维修说明（选填）"
            show-word-limit
          />
        </van-cell-group>
        
        <div style="margin: 24px 16px;">
          <van-button 
            round 
            block 
            type="primary" 
            native-type="submit"
            :loading="submitting"
          >
            提交完成
          </van-button>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast, showConfirmDialog } from 'vant'
import { maintenanceWorkorderAPI, uploadAPI } from '@/api'

export default {
  name: 'CompleteWorkorder',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const workorder = ref(null)
    const fileList = ref([])
    const submitting = ref(false)
    const form = reactive({
      note: '',
      images: []
    })
    
    const loadDetail = async () => {
      try {
        const id = parseInt(route.params.id)
        const data = await maintenanceWorkorderAPI.getWorkorderDetail(id)
        workorder.value = data
      } catch (error) {
        console.error('加载失败:', error)
        showToast('工单不存在')
        router.back()
      }
    }
    
    const afterRead = async (file) => {
      // 单个文件上传
      if (!Array.isArray(file)) {
        file = [file]
      }
      
      for (const item of file) {
        item.status = 'uploading'
        item.message = '上传中...'
        
        try {
          const res = await uploadAPI.upload(item.file)
          item.status = 'done'
          item.url = res.url
          form.images.push(res.url)
          console.log('上传成功:', res.url)
        } catch (error) {
          item.status = 'failed'
          item.message = '上传失败'
          console.error('上传失败:', error)
        }
      }
    }
    
    const onSubmit = async () => {
      if (form.images.length === 0) {
        const confirmed = await showConfirmDialog({
          title: '提示',
          message: '未上传维修完成照片，确定要提交吗？'
        }).catch(() => false)
        
        if (!confirmed) return
      }
      
      submitting.value = true
      try {
        await maintenanceWorkorderAPI.completeWork(workorder.value.id, {
          repair_images: form.images,
          note: form.note
        })
        
        showSuccessToast('维修已完成')
        router.push('/maintenance/workorders')
      } catch (error) {
        console.error('提交失败:', error)
      } finally {
        submitting.value = false
      }
    }
    
    onMounted(() => {
      loadDetail()
    })
    
    return {
      workorder,
      fileList,
      form,
      submitting,
      afterRead,
      onSubmit
    }
  }
}
</script>

<style scoped>
.complete-page {
  background: #f7f8fa;
  min-height: 100vh;
}

.content {
  padding-top: 46px;
}

.info-section {
  background: white;
  padding: 16px;
  margin: 12px 16px;
  border-radius: 8px;
}

.order-info {
  display: flex;
  padding: 8px 0;
  font-size: 14px;
}

.order-info .label {
  color: #969799;
  min-width: 80px;
}

.order-info .value {
  color: #323233;
  flex: 1;
  font-weight: 500;
}

.upload-section {
  padding: 16px;
}

.upload-btn {
  width: 100px;
  height: 100px;
  border: 2px dashed #dcdee0;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #fafafa;
}

.upload-text {
  margin-top: 8px;
  font-size: 13px;
  color: #646566;
}

.upload-tips {
  margin-top: 4px;
  font-size: 11px;
  color: #969799;
}
</style>
