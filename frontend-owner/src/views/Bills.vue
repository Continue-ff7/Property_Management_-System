<template>
  <div class="bills-page">
    <van-nav-bar title="我的账单" fixed />
    
    <div class="content">
      <van-tabs v-model="activeTab" @change="loadBills">
        <van-tab title="全部"></van-tab>
        <van-tab title="未支付"></van-tab>
        <van-tab title="已支付"></van-tab>
      </van-tabs>
      
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="onLoad"
        >
          <div v-for="bill in bills" :key="bill.id" class="bill-card">
            <div class="bill-header">
              <span class="fee-type">{{ getFeeTypeText(bill.fee_type) }}</span>
              <van-tag :type="getStatusType(bill.status)">
                {{ getStatusText(bill.status) }}
              </van-tag>
            </div>
            
            <div class="bill-body">
              <div class="bill-info">
                <div class="info-item">
                  <span class="label">房产地址</span>
                  <span class="value">{{ bill.property_info }}</span>
                </div>
                <div class="info-item">
                  <span class="label">账期</span>
                  <span class="value">{{ bill.billing_period }}</span>
                </div>
                <div class="info-item">
                  <span class="label">截止日期</span>
                  <span class="value">{{ bill.due_date }}</span>
                </div>
              </div>
              
              <div class="bill-amount">
                <span class="amount-label">应缴金额</span>
                <span class="amount">¥{{ Number(bill.amount || 0).toFixed(2) }}</span>
              </div>
            </div>
            
            <div class="bill-footer" v-if="bill.status === 'unpaid'">
              <van-button type="primary" size="small" @click.stop="payBill(bill)">
                立即缴费
              </van-button>
            </div>
          </div>
          
          <van-empty v-if="bills.length === 0" description="暂无账单" />
        </van-list>
      </van-pull-refresh>
    </div>
    
    <!-- 支付弹窗 -->
    <van-action-sheet :show="showPaySheet" @update:show="showPaySheet = $event" title="选择支付方式">
      <div class="pay-content">
        <!-- 支付金额 -->
        <div class="pay-amount" v-if="currentBill">
          <div class="amount-label">支付金额</div>
          <div class="amount-value">￥{{ Number(currentBill.amount || 0).toFixed(2) }}</div>
        </div>
        
        <van-radio-group v-model="payMethod">
          <van-cell-group>
            <van-cell title="支付宝" clickable @click="payMethod = 'alipay'">
              <template #icon>
                <van-icon name="alipay" size="24" color="#1677ff" style="margin-right: 12px;" />
              </template>
              <template #right-icon>
                <van-radio name="alipay" />
              </template>
            </van-cell>
            <van-cell title="微信支付" clickable @click="payMethod = 'wechat'">
              <template #icon>
                <van-icon name="wechat-pay" size="24" color="#07c160" style="margin-right: 12px;" />
              </template>
              <template #right-icon>
                <van-radio name="wechat" />
              </template>
            </van-cell>
          </van-cell-group>
        </van-radio-group>
        
        <div style="padding: 16px;">
          <van-button type="primary" block @click="confirmPay" :loading="paying">
            确认支付
          </van-button>
        </div>
      </div>
    </van-action-sheet>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { showToast, showSuccessToast } from 'vant'
import { billAPI } from '@/api'

export default {
  name: 'Bills',
  setup() {
    const activeTab = ref(0)
    const bills = ref([])
    const loading = ref(false)
    const finished = ref(false)
    const refreshing = ref(false)
    const showPaySheet = ref(false)
    const payMethod = ref('alipay')
    const paying = ref(false)
    const currentBill = ref(null)
    
    const statusMap = ['', 'unpaid', 'paid']
    
    const loadBills = async () => {
      try {
        loading.value = true
        finished.value = false
        bills.value = [] // 清空旧数据
        
        const status = statusMap[activeTab.value]
        const params = status ? { status } : {}
        console.log('加载账单, tab:', activeTab.value, 'status:', status, 'params:', params)
        
        const data = await billAPI.getMyBills(params)
        console.log('账单数据:', data)
        
        bills.value = data || []
        finished.value = true
      } catch (error) {
        console.error('加载失败:', error)
        showToast('加载账单失败')
      } finally {
        loading.value = false
      }
    }
    
    const onLoad = () => {
      loadBills()
      loading.value = false
    }
    
    const onRefresh = () => {
      finished.value = false
      loading.value = true
      loadBills().finally(() => {
        refreshing.value = false
      })
    }
    
    const payBill = (bill) => {
      console.log('点击缴费按钮:', bill)
      console.log('弹窗状态前:', showPaySheet.value)
      currentBill.value = bill
      showPaySheet.value = true
      console.log('弹窗状态后:', showPaySheet.value)
    }
    
    const confirmPay = async () => {
      if (!payMethod.value) {
        showToast('请选择支付方式')
        return
      }
      
      paying.value = true
      try {
        // 模拟支付过程
        await new Promise(resolve => setTimeout(resolve, 1500))
        
        await billAPI.payBill(currentBill.value.id, {
          payment_method: payMethod.value
        })
        
        const payMethodText = payMethod.value === 'alipay' ? '支付宝' : '微信支付'
        showSuccessToast(`${payMethodText}支付成功！金额￥${Number(currentBill.value.amount).toFixed(2)}`)
        showPaySheet.value = false
        
        // 重新加载账单列表
        loadBills()
      } catch (error) {
        console.error('支付失败:', error)
        showToast('支付失败，请重试')
      } finally {
        paying.value = false
      }
    }
    
    const getFeeTypeText = (type) => {
      const map = { property: '物业费', parking: '停车费', water: '水费', electricity: '电费' }
      return map[type] || type
    }
    
    const getStatusType = (status) => {
      const map = { unpaid: 'warning', paid: 'success', overdue: 'danger' }
      return map[status] || 'default'
    }
    
    const getStatusText = (status) => {
      const map = { unpaid: '未支付', paid: '已支付', overdue: '已逾期' }
      return map[status] || status
    }
    
    // 初始化加载
    onMounted(() => {
      loadBills()
    })
    
    return {
      activeTab,
      bills,
      loading,
      finished,
      refreshing,
      showPaySheet,
      payMethod,
      paying,
      currentBill,
      loadBills,
      onLoad,
      onRefresh,
      payBill,
      confirmPay,
      getFeeTypeText,
      getStatusType,
      getStatusText
    }
  }
}
</script>

<style scoped>
.bills-page {
  background: #f7f8fa;
  min-height: 100vh;
}

.content {
  padding-top: 46px;
}

.bill-card {
  background: white;
  margin: 12px 16px;
  border-radius: 8px;
  overflow: hidden;
}

.bill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f2f3f5;
}

.fee-type {
  font-size: 16px;
  font-weight: bold;
  color: #323233;
}

.bill-body {
  padding: 16px;
}

.bill-info {
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.info-item .label {
  color: #969799;
}

.info-item .value {
  color: #323233;
}

.bill-amount {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f7f8fa;
  border-radius: 4px;
}

.amount-label {
  font-size: 14px;
  color: #646566;
}

.amount {
  font-size: 24px;
  font-weight: bold;
  color: #ee0a24;
}

.bill-footer {
  padding: 12px 16px;
  border-top: 1px solid #f2f3f5;
  text-align: right;
}

.pay-content {
  padding-top: 16px;
}

.pay-amount {
  text-align: center;
  padding: 24px 16px;
  border-bottom: 1px solid #f2f3f5;
}

.pay-amount .amount-label {
  font-size: 14px;
  color: #969799;
  margin-bottom: 8px;
}

.pay-amount .amount-value {
  font-size: 36px;
  font-weight: bold;
  color: #ee0a24;
}
</style>
