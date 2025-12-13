<template>
  <div class="repair-create">
    <van-nav-bar
      title="提交报修"
      left-arrow
      @click-left="$router.back()"
      fixed
    />
    
    <div class="content">
      <van-form @submit="onSubmit">
        <van-cell-group inset>
          <van-field
            :model-value="selectedProperty ? `${selectedProperty.building_name} ${selectedProperty.unit}单元 ${selectedProperty.room_number}` : ''"
            is-link
            readonly
            label="报修地址"
            placeholder="选择房产"
            @click="showPropertyPicker = true"
          />
          
          <van-field
            v-model="form.description"
            rows="4"
            autosize
            type="textarea"
            maxlength="200"
            label="问题描述"
            placeholder="请详细描述遇到的问题..."
            show-word-limit
            :rules="[{ required: true, message: '请填写问题描述' }]"
          />
          
          <van-field
            v-model="urgencyText"
            is-link
            readonly
            label="紧急程度"
            placeholder="选择紧急程度"
            @click="showUrgencyPicker = true"
          />
          
          <van-field label="上传图片" name="uploader">
            <template #input>
              <van-uploader
                v-model="fileList"
                :max-count="3"
                :after-read="afterRead"
              />
            </template>
          </van-field>
        </van-cell-group>
        
        <div style="margin: 24px 16px;">
          <van-button round block type="primary" native-type="submit" :loading="submitting">
            提交报修
          </van-button>
        </div>
      </van-form>
    </div>
    
    <!-- 房产选择器 -->
    <van-popup 
      :show="showPropertyPicker" 
      @update:show="showPropertyPicker = $event"
      position="bottom"
    >
      <van-picker
        :columns="propertyColumns"
        @confirm="onPropertyConfirm"
        @cancel="showPropertyPicker = false"
      />
    </van-popup>
    
    <!-- 紧急程度选择器 -->
    <van-popup 
      :show="showUrgencyPicker" 
      @update:show="showUrgencyPicker = $event"
      position="bottom"
    >
      <van-picker
        :columns="urgencyColumns"
        @confirm="onUrgencyConfirm"
        @cancel="showUrgencyPicker = false"
      />
    </van-popup>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import { ownerAPI, repairAPI, uploadAPI } from '@/api'

export default {
  name: 'RepairCreate',
  setup() {
    const router = useRouter()
    const form = ref({
      property_id: '',
      description: '',
      urgency_level: 'medium',
      images: []
    })
    
    const selectedProperty = ref(null)
    const properties = ref([])
    const fileList = ref([])
    const submitting = ref(false)
    const showPropertyPicker = ref(false)
    const showUrgencyPicker = ref(false)
    
    const propertyColumns = computed(() => {
      return properties.value.map(p => ({
        text: `${p.building_name} ${p.unit}单元 ${p.room_number}`,
        value: p.id
      }))
    })
    
    const urgencyColumns = [
      { text: '一般', value: 'low' },
      { text: '紧急', value: 'medium' },
      { text: '非常紧急', value: 'high' }
    ]
    
    const urgencyText = computed(() => {
      const item = urgencyColumns.find(c => c.value === form.value.urgency_level)
      return item ? item.text : ''
    })
    
    const loadProperties = async () => {
      try {
        const data = await ownerAPI.getMyProperties()
        properties.value = data
        if (data.length > 0) {
          form.value.property_id = data[0].id
          selectedProperty.value = data[0]
        }
      } catch (error) {
        console.error('加载房产失败:', error)
      }
    }
    
    const onPropertyConfirm = ({ selectedOptions }) => {
      const property = properties.value.find(p => p.id === selectedOptions[0].value)
      if (property) {
        form.value.property_id = property.id
        selectedProperty.value = property
      }
      showPropertyPicker.value = false
    }
    
    const onUrgencyConfirm = ({ selectedOptions }) => {
      form.value.urgency_level = selectedOptions[0].value
      showUrgencyPicker.value = false
    }
    
    const afterRead = async (file) => {
      file.status = 'uploading'
      file.message = '上传中...'
      
      try {
        const res = await uploadAPI.upload(file.file)
        file.status = 'done'
        file.url = res.url  // 保存图片URL用于预览
        form.value.images.push(res.url)
        console.log('上传成功:', res.url)
      } catch (error) {
        file.status = 'failed'
        file.message = '上传失败'
        console.error('上传失败:', error)
      }
    }
    
    const onSubmit = async () => {
      if (!form.value.property_id) {
        showToast('请选择报修地址')
        return
      }
      
      if (!form.value.description) {
        showToast('请填写问题描述')
        return
      }
      
      submitting.value = true
      try {
        await repairAPI.createRepair(form.value)
        showSuccessToast('提交成功')
        router.back()
      } catch (error) {
        console.error('提交失败:', error)
      } finally {
        submitting.value = false
      }
    }
    
    onMounted(() => {
      loadProperties()
    })
    
    return {
      form,
      fileList,
      submitting,
      selectedProperty,
      showPropertyPicker,
      showUrgencyPicker,
      propertyColumns,
      urgencyColumns,
      urgencyText,
      onPropertyConfirm,
      onUrgencyConfirm,
      afterRead,
      onSubmit
    }
  }
}
</script>

<style scoped>
.repair-create {
  background: #f7f8fa;
  min-height: 100vh;
}

.content {
  padding-top: 46px;
  padding-bottom: 20px;
}
</style>
