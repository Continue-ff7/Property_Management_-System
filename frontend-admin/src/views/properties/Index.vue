<template>
  <div class="page-container">
    <div class="card">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="楼栋管理" name="buildings">
          <el-button type="primary" icon="Plus" @click="showBuildingDialog" style="margin-bottom: 20px">
            添加楼栋
          </el-button>
          
          <el-table 
            v-if="activeTab === 'buildings'" 
            :data="buildings" 
            v-loading="buildingsLoading"
            :key="'buildings-table'"
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="name" label="楼栋名称" />
            <el-table-column prop="floors" label="楼层数" />
            <el-table-column prop="units_per_floor" label="每层单元数" />
          </el-table>
        </el-tab-pane>
        
        <el-tab-pane label="房产管理" name="properties">
          <div class="toolbar">
            <el-select v-model="filterBuilding" placeholder="选择楼栋" clearable style="width: 200px" @change="loadProperties">
              <el-option
                v-for="building in buildings"
                :key="building.id"
                :label="building.name"
                :value="building.id"
              />
            </el-select>
            
            <el-button type="primary" icon="Plus" @click="showPropertyDialog">
              添加房产
            </el-button>
          </div>
          
          <el-table 
            v-if="activeTab === 'properties'" 
            :data="properties" 
            v-loading="propertiesLoading"
            :key="'properties-table'"
          >
            <el-table-column prop="building_name" label="楼栋" width="120" />
            <el-table-column prop="unit" label="单元" width="80" />
            <el-table-column prop="floor" label="楼层" width="80" />
            <el-table-column prop="room_number" label="房间号" width="100" />
            <el-table-column prop="area" label="面积(㎡)" width="100" />
            <el-table-column label="业主" width="150">
              <template #default="{ row }">
                <el-tag v-if="row.owner_name" type="success">{{ row.owner_name }}</el-tag>
                <el-tag v-else type="info">未分配</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button 
                    v-if="!row.owner_id" 
                    size="small" 
                    type="primary"
                    @click="showAssignDialog(row)"
                  >
                    分配业主
                  </el-button>
                  <el-button 
                    v-else 
                    size="small" 
                    type="warning"
                    @click="unbindOwner(row)"
                  >
                    解绑业主
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <!-- 添加楼栋对话框 -->
    <el-dialog v-model="buildingDialogVisible" title="添加楼栋" width="400px">
      <el-form :model="buildingForm" label-width="100px">
        <el-form-item label="楼栋名称">
          <el-input v-model="buildingForm.name" />
        </el-form-item>
        <el-form-item label="楼层数">
          <el-input-number v-model="buildingForm.floors" :min="1" />
        </el-form-item>
        <el-form-item label="每层单元数">
          <el-input-number v-model="buildingForm.units_per_floor" :min="1" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="buildingDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddBuilding">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 添加房产对话框 -->
    <el-dialog v-model="propertyDialogVisible" title="添加房产" width="500px">
      <el-form :model="propertyForm" label-width="100px">
        <el-form-item label="楼栋">
          <el-select v-model="propertyForm.building_id" placeholder="请选择" style="width: 100%">
            <el-option
              v-for="building in buildings"
              :key="building.id"
              :label="building.name"
              :value="building.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="单元号">
          <el-input v-model="propertyForm.unit" />
        </el-form-item>
        <el-form-item label="楼层">
          <el-input-number v-model="propertyForm.floor" :min="1" />
        </el-form-item>
        <el-form-item label="房间号">
          <el-input v-model="propertyForm.room_number" />
        </el-form-item>
        <el-form-item label="面积(㎡)">
          <el-input-number v-model="propertyForm.area" :min="0" :precision="2" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="propertyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddProperty">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 分配业主对话框 -->
    <el-dialog v-model="assignDialogVisible" title="分配业主" width="500px">
      <el-alert 
        title="提示" 
        type="info" 
        :closable="false"
        style="margin-bottom: 20px"
      >
        为「{{ currentProperty?.building_name }} {{ currentProperty?.unit }}单元 {{ currentProperty?.room_number }}」分配业主
      </el-alert>
      
      <el-form label-width="80px">
        <el-form-item label="选择业主">
          <el-select 
            v-model="selectedOwnerId" 
            placeholder="请选择业主" 
            filterable
            style="width: 100%"
            v-loading="ownersLoading"
          >
            <el-option
              v-for="owner in owners"
              :key="owner.id"
              :label="`${owner.name} (${owner.phone})`"
              :value="owner.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAssign" :loading="assigning">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { propertyAPI, ownerAPI } from '@/api'

export default {
  name: 'Properties',
  setup() {
    const activeTab = ref('buildings')
    const buildingsLoading = ref(false)
    const propertiesLoading = ref(false)
    const buildings = ref([])
    const properties = ref([])
    const filterBuilding = ref(null)
    
    const buildingDialogVisible = ref(false)
    const propertyDialogVisible = ref(false)
    const assignDialogVisible = ref(false)
    const assigning = ref(false)
    const ownersLoading = ref(false)
    
    const owners = ref([])
    const currentProperty = ref(null)
    const selectedOwnerId = ref(null)
    
    const buildingForm = reactive({
      name: '',
      floors: 1,
      units_per_floor: 1
    })
    
    const propertyForm = reactive({
      building_id: null,
      unit: '',
      floor: 1,
      room_number: '',
      area: 0
    })
    
    const loadBuildings = async () => {
      buildingsLoading.value = true
      try {
        const data = await propertyAPI.getBuildings()
        buildings.value = data
      } catch (error) {
        console.error('加载失败:', error)
      } finally {
        buildingsLoading.value = false
      }
    }
    
    const loadProperties = async () => {
      propertiesLoading.value = true
      try {
        const params = {}
        if (filterBuilding.value) {
          params.building_id = filterBuilding.value
        }
        const data = await propertyAPI.getList(params)
        properties.value = data
      } catch (error) {
        console.error('加载失败:', error)
      } finally {
        propertiesLoading.value = false
      }
    }
    
    const loadOwners = async () => {
      ownersLoading.value = true
      try {
        const data = await ownerAPI.getList({ limit: 1000 })
        owners.value = data
      } catch (error) {
        console.error('加载业主失败:', error)
        ElMessage.error('加载业主列表失败')
      } finally {
        ownersLoading.value = false
      }
    }
    
    const showBuildingDialog = () => {
      Object.assign(buildingForm, { name: '', floors: 1, units_per_floor: 1 })
      buildingDialogVisible.value = true
    }
    
    const showPropertyDialog = () => {
      Object.assign(propertyForm, { building_id: null, unit: '', floor: 1, room_number: '', area: 0 })
      propertyDialogVisible.value = true
    }
    
    const showAssignDialog = async (row) => {
      currentProperty.value = row
      selectedOwnerId.value = null
      assignDialogVisible.value = true
      await loadOwners()
    }
    
    const handleAddBuilding = async () => {
      try {
        await propertyAPI.createBuilding(buildingForm)
        ElMessage.success('添加成功')
        buildingDialogVisible.value = false
        loadBuildings()
      } catch (error) {
        console.error('添加失败:', error)
        ElMessage.error(error.response?.data?.detail || '添加失败')
      }
    }
    
    const handleAddProperty = async () => {
      try {
        await propertyAPI.create(propertyForm)
        ElMessage.success('添加成功')
        propertyDialogVisible.value = false
        loadProperties()
      } catch (error) {
        console.error('添加失败:', error)
        ElMessage.error(error.response?.data?.detail || '添加失败')
      }
    }
    
    const handleAssign = async () => {
      if (!selectedOwnerId.value) {
        ElMessage.warning('请选择业主')
        return
      }
      
      assigning.value = true
      try {
        await propertyAPI.assignOwner(currentProperty.value.id, selectedOwnerId.value)
        ElMessage.success('分配成功')
        assignDialogVisible.value = false
        loadProperties()
      } catch (error) {
        console.error('分配失败:', error)
        ElMessage.error(error.response?.data?.detail || '分配失败')
      } finally {
        assigning.value = false
      }
    }
    
    const unbindOwner = async (row) => {
      try {
        await ElMessageBox.confirm(
          `确定要解绑业主「${row.owner_name}」与该房产的关联吗？`,
          '提示',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await propertyAPI.unbindOwner(row.id)
        ElMessage.success('解绑成功')
        loadProperties()
      } catch (error) {
        if (error !== 'cancel') {
          console.error('解绑失败:', error)
          ElMessage.error(error.response?.data?.detail || '解绑失败')
        }
      }
    }
    
    // Tab切换处理
    const handleTabChange = (tabName) => {
      // 延迟加载，避免 ResizeObserver 错误
      setTimeout(() => {
        if (tabName === 'properties' && properties.value.length === 0) {
          loadProperties()
        }
      }, 100)
    }
    
    onMounted(() => {
      loadBuildings()
      loadProperties()
    })
    
    return {
      activeTab, buildingsLoading, propertiesLoading, buildings, properties, filterBuilding,
      buildingDialogVisible, propertyDialogVisible, assignDialogVisible, assigning, ownersLoading,
      buildingForm, propertyForm, owners, currentProperty, selectedOwnerId,
      loadBuildings, loadProperties, loadOwners, showBuildingDialog, showPropertyDialog, 
      showAssignDialog, handleAddBuilding, handleAddProperty, handleAssign, unbindOwner,
      handleTabChange
    }
  }
}
</script>
