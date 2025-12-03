<template>
  <div class="page-container">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #1890ff">
            <el-icon :size="32"><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ ownerStats.total_owners }}</div>
            <div class="stat-label">业主总数</div>
          </div>
        </div>
      </el-col>
      
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #52c41a">
            <el-icon :size="32"><Money /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">¥{{ revenueStats.total_revenue }}</div>
            <div class="stat-label">总收入</div>
          </div>
        </div>
      </el-col>
      
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #faad14">
            <el-icon :size="32"><Tools /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ repairStats.total_orders }}</div>
            <div class="stat-label">报修工单</div>
          </div>
        </div>
      </el-col>
      
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #f5222d">
            <el-icon :size="32"><Warning /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ alerts.length }}</div>
            <div class="stat-label">预警信息</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <div class="card">
          <h3 class="card-title">收入统计</h3>
          <div ref="revenueChartRef" style="height: 300px"></div>
        </div>
      </el-col>
      
      <el-col :span="12">
        <div class="card">
          <h3 class="card-title">维修工单统计</h3>
          <div ref="repairChartRef" style="height: 300px"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 预警信息 -->
    <div class="card" style="margin-top: 20px" v-if="alerts.length > 0">
      <h3 class="card-title">预警信息</h3>
      <el-alert
        v-for="(alert, index) in alerts"
        :key="index"
        :title="alert.message"
        :type="alert.level"
        :closable="false"
        style="margin-bottom: 10px"
      />
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import * as echarts from 'echarts'
import { statisticsAPI } from '@/api'
import { User, Money, Tools, Warning } from '@element-plus/icons-vue'

export default {
  name: 'Dashboard',
  components: {
    User, Money, Tools, Warning
  },
  setup() {
    const revenueChartRef = ref(null)
    const repairChartRef = ref(null)
    
    const ownerStats = reactive({
      total_owners: 0,
      active_owners: 0,
      total_properties: 0
    })
    
    const revenueStats = reactive({
      total_revenue: 0,
      paid_revenue: 0,
      unpaid_revenue: 0,
      overdue_revenue: 0,
      payment_rate: 0
    })
    
    const repairStats = reactive({
      total_orders: 0,
      pending_orders: 0,
      in_progress_orders: 0,
      completed_orders: 0,
      average_rating: 0
    })
    
    const alerts = ref([])
    
    // 初始化收入图表
    const initRevenueChart = () => {
      const chart = echarts.init(revenueChartRef.value)
      const option = {
        tooltip: {
          trigger: 'item'
        },
        legend: {
          bottom: '5%',
          left: 'center'
        },
        series: [
          {
            name: '收入统计',
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: 20,
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: [
              { 
                value: revenueStats.paid_revenue, 
                name: '已支付',
                itemStyle: { color: '#52c41a' }
              },
              { 
                value: revenueStats.unpaid_revenue, 
                name: '未支付',
                itemStyle: { color: '#1890ff' }
              },
              { 
                value: revenueStats.overdue_revenue, 
                name: '已逾期',
                itemStyle: { color: '#f5222d' }
              }
            ]
          }
        ]
      }
      chart.setOption(option)
      window.addEventListener('resize', () => chart.resize())
    }
    
    // 初始化维修图表
    const initRepairChart = () => {
      const chart = echarts.init(repairChartRef.value)
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: ['待处理', '进行中', '已完成']
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: '工单数量',
            type: 'bar',
            data: [
              {
                value: repairStats.pending_orders,
                itemStyle: { color: '#faad14' }
              },
              {
                value: repairStats.in_progress_orders,
                itemStyle: { color: '#1890ff' }
              },
              {
                value: repairStats.completed_orders,
                itemStyle: { color: '#52c41a' }
              }
            ],
            barWidth: '60%'
          }
        ]
      }
      chart.setOption(option)
      window.addEventListener('resize', () => chart.resize())
    }
    
    // 加载数据
    const loadData = async () => {
      try {
        // 加载业主统计
        const ownerData = await statisticsAPI.getOwners()
        Object.assign(ownerStats, ownerData)
        
        // 加载收入统计
        const revenueData = await statisticsAPI.getRevenue()
        Object.assign(revenueStats, revenueData)
        
        // 加载维修统计
        const repairData = await statisticsAPI.getRepairs()
        Object.assign(repairStats, repairData)
        
        // 加载预警
        const alertData = await statisticsAPI.getAlerts()
        alerts.value = alertData.alerts || []
        
        // 初始化图表
        initRevenueChart()
        initRepairChart()
      } catch (error) {
        console.error('加载数据失败:', error)
      }
    }
    
    onMounted(() => {
      loadData()
    })
    
    return {
      revenueChartRef,
      repairChartRef,
      ownerStats,
      revenueStats,
      repairStats,
      alerts
    }
  }
}
</script>

<style lang="scss" scoped>
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  
  .stat-icon {
    width: 64px;
    height: 64px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
  }
  
  .stat-content {
    flex: 1;
    
    .stat-value {
      font-size: 24px;
      font-weight: bold;
      color: #333;
      margin-bottom: 4px;
    }
    
    .stat-label {
      font-size: 14px;
      color: #999;
    }
  }
}

.card-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 20px;
  color: #333;
}
</style>
