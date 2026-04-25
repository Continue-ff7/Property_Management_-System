<template>
  <div class="page-container">
    <div class="card">
      <div class="toolbar">
        <div class="filter-group">
          <el-select
            v-model="filterCategory"
            placeholder="选择类别"
            clearable
            style="width: 140px; margin-right: 10px"
            @change="onCategoryChange"
          >
            <el-option
              v-for="cat in categoryOptions"
              :key="cat"
              :label="cat"
              :value="cat"
            />
          </el-select>
          <el-select
            v-model="filterItem"
            placeholder="选择项目"
            clearable
            :disabled="!filterCategory"
            style="width: 180px; margin-right: 10px"
            @change="() => {}"
          >
            <el-option
              v-for="item in itemOptions"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
          <el-button @click="resetFilter">重置</el-button>
        </div>
        <el-button type="primary" :icon="Plus" @click="showAddDialog">新增价格</el-button>
      </div>

      <el-table :data="filteredPrices" v-loading="loading">
        <el-table-column prop="category" label="维修类别" width="120" />
        <el-table-column prop="item" label="维修项目" />
        <el-table-column label="参考价格（元）" width="180">
          <template #default="{ row }">
            <span class="price-range">{{ row.price_min }} ~ {{ row.price_max }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" show-overflow-tooltip />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="480px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="维修类别" prop="category">
          <el-select
            v-model="form.category"
            placeholder="选择或输入类别"
            allow-create
            filterable
            style="width: 100%"
          >
            <el-option v-for="cat in categoryOptions" :key="cat" :label="cat" :value="cat" />
          </el-select>
        </el-form-item>
        <el-form-item label="维修项目" prop="item">
          <el-input v-model="form.item" placeholder="如：普通灯泡更换、下水道疏通" />
        </el-form-item>
        <el-form-item label="最低价格" prop="price_min">
          <el-input-number v-model="form.price_min" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="最高价格" prop="price_max">
          <el-input-number v-model="form.price_max" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" placeholder="可选，如：品牌款价格更高" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { repairPriceAPI } from '@/api/index'

export default {
  name: 'RepairPrices',
  setup() {
    const loading = ref(false)
    const submitting = ref(false)
    const prices = ref([])
    const filterCategory = ref('')
    const filterItem = ref('')
    const dialogVisible = ref(false)
    const isEdit = ref(false)
    const editId = ref(null)
    const formRef = ref(null)

    const form = ref({
      category: '',
      item: '',
      price_min: 0,
      price_max: 0,
      remark: ''
    })

    const rules = {
      category: [{ required: true, message: '请选择或输入维修类别', trigger: 'change' }],
      item: [{ required: true, message: '请输入维修项目', trigger: 'blur' }],
      price_min: [{ required: true, message: '请输入最低价格', trigger: 'blur' }],
      price_max: [{ required: true, message: '请输入最高价格', trigger: 'blur' }]
    }

    const dialogTitle = computed(() => isEdit.value ? '编辑维修价格' : '新增维修价格')

    // 从已有数据中提取所有类别（去重）
    const categoryOptions = computed(() => {
      const cats = prices.value.map(p => p.category)
      return [...new Set(cats)]
    })

    // 根据选中的类别，过滤出对应的项目
    const itemOptions = computed(() => {
      if (!filterCategory.value) return []
      return prices.value
        .filter(p => p.category === filterCategory.value)
        .map(p => p.item)
    })

    const filteredPrices = computed(() => {
      let list = prices.value
      if (filterCategory.value) {
        list = list.filter(p => p.category === filterCategory.value)
      }
      if (filterItem.value) {
        list = list.filter(p => p.item === filterItem.value)
      }
      return list
    })

    const onCategoryChange = () => {
      filterItem.value = ''
    }

    const resetFilter = () => {
      filterCategory.value = ''
      filterItem.value = ''
    }

    const loadPrices = async () => {
      loading.value = true
      try {
        const res = await repairPriceAPI.getList()
        prices.value = Array.isArray(res) ? res : (res.data || [])
      } catch (e) {
        ElMessage.error('获取价格列表失败')
      } finally {
        loading.value = false
      }
    }

    const showAddDialog = () => {
      isEdit.value = false
      editId.value = null
      dialogVisible.value = true
    }

    const showEditDialog = (row) => {
      isEdit.value = true
      editId.value = row.id
      form.value = {
        category: row.category,
        item: row.item,
        price_min: parseFloat(row.price_min),
        price_max: parseFloat(row.price_max),
        remark: row.remark || ''
      }
      dialogVisible.value = true
    }

    const resetForm = () => {
      form.value = { category: '', item: '', price_min: 0, price_max: 0, remark: '' }
      formRef.value?.resetFields()
    }

    const handleSubmit = async () => {
      await formRef.value?.validate()
      if (form.value.price_max < form.value.price_min) {
        ElMessage.warning('最高价格不能低于最低价格')
        return
      }
      submitting.value = true
      try {
        const payload = {
          category: form.value.category,
          item: form.value.item,
          price_min: form.value.price_min,
          price_max: form.value.price_max,
          remark: form.value.remark || null
        }
        if (isEdit.value) {
          await repairPriceAPI.update(editId.value, payload)
          ElMessage.success('更新成功')
        } else {
          await repairPriceAPI.create(payload)
          ElMessage.success('新增成功')
        }
        dialogVisible.value = false
        loadPrices()
      } catch (e) {
        ElMessage.error('操作失败')
      } finally {
        submitting.value = false
      }
    }

    const handleDelete = async (row) => {
      try {
        await ElMessageBox.confirm(`确定删除"${row.item}"的价格记录吗？`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await repairPriceAPI.delete(row.id)
        ElMessage.success('删除成功')
        loadPrices()
      } catch (e) {
        // 取消
      }
    }

    onMounted(loadPrices)

    return {
      loading, submitting, prices, filterCategory, filterItem,
      dialogVisible, isEdit, form, rules, formRef,
      dialogTitle, filteredPrices, categoryOptions, itemOptions, Plus,
      showAddDialog, showEditDialog, resetForm, handleSubmit, handleDelete,
      onCategoryChange, resetFilter
    }
  }
}
</script>

<style lang="scss" scoped>
.page-container {
  padding: 20px;
}
.page-header {
  margin-bottom: 16px;
  .page-title {
    font-size: 20px;
    font-weight: 600;
    color: #1a1a1a;
    margin: 0 0 4px;
  }
  .page-desc {
    font-size: 13px;
    color: #909399;
    margin: 0;
  }
}
.card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.filter-group {
  display: flex;
  align-items: center;
}
.price-range {
  font-weight: 500;
  color: #e6a23c;
}
</style>
