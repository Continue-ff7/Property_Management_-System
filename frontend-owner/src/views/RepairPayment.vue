<template>
  <div class="payment-page">
    <van-nav-bar
      title="支付维修费用"
      left-arrow
      @click-left="$router.back()"
      fixed
    />
    
    <div class="content">
      <!-- 工单信息 -->
      <div class="order-card">
        <div class="card-title">工单信息</div>
        <van-cell-group>
          <van-cell title="工单号" :value="repair.order_number" />
          <van-cell title="报修地址" :value="repair.property_info" />
          <van-cell title="维修人员" :value="repair.maintenance_worker_name" />
        </van-cell-group>
      </div>
      
      <!-- 费用详情 -->
      <div class="cost-card">
        <div class="card-title">费用详情</div>
        <div class="cost-detail">
          <div class="cost-item">
            <span class="label">维修费用</span>
            <span class="value">￥{{ repair.repair_cost }}</span>
          </div>
          <van-divider />
          <div class="cost-total">
            <span class="label">合计</span>
            <span class="amount">￥{{ repair.repair_cost }}</span>
          </div>
        </div>
      </div>
      
      <!-- 支付方式 -->
      <div class="payment-method-card">
        <div class="card-title">支付方式</div>
        <van-radio-group v-model="paymentMethod">
          <van-cell-group>
            <van-cell title="微信支付" clickable @click="paymentMethod = 'wechat'">
              <template #icon>
                <van-icon name="wechat" size="24" color="#07C160" style="margin-right: 12px;" />
              </template>
              <template #right-icon>
                <van-radio name="wechat" />
              </template>
            </van-cell>
            <van-cell title="支付宝" clickable @click="paymentMethod = 'alipay'">
              <template #icon>
                <van-icon name="alipay" size="24" color="#1677FF" style="margin-right: 12px;" />
              </template>
              <template #right-icon>
                <van-radio name="alipay" />
              </template>
            </van-cell>
          </van-cell-group>
        </van-radio-group>
      </div>
      
      <!-- 提示信息 -->
      <div class="tips">
        <van-icon name="info-o" />
        <span>支付完成后将自动跳转到评价页面</span>
      </div>
    </div>
    
    <!-- 底部支付按钮 -->
    <div class="footer">
      <van-button 
        type="primary" 
        block 
        :loading="paying"
        @click="handlePay"
      >
        立即支付 ￥{{ repair.repair_cost }}
      </van-button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast, showLoadingToast, showConfirmDialog } from 'vant'
import { repairAPI } from '@/api'

export default {
  name: 'RepairPayment',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const repair = ref({})
    const paymentMethod = ref('wechat')  // 默认微信支付
    const paying = ref(false)
    
    // 加载工单详情
    const loadDetail = async () => {
      try {
        const id = parseInt(route.params.id)
        const data = await repairAPI.getRepairDetail(id)
        repair.value = data
        
        // 检查是否已支付
        if (data.cost_paid) {
          showToast('该工单费用已支付')
          router.replace(`/repair/${id}`)
          return
        }
        
        // 检查费用是否为0
        if (!data.repair_cost || data.repair_cost <= 0) {
          showToast('该工单无需支付')
          router.replace(`/repair/${id}`)
          return
        }
        
      } catch (error) {
        console.error('加载失败:', error)
        showToast('工单不存在')
        router.back()
      }
    }
    
    // 处理支付
    const handlePay = async () => {
      try {
        await showConfirmDialog({
          title: '确认支付',
          message: `确定使用${paymentMethod.value === 'wechat' ? '微信支付' : '支付宝'}支付 ￥${repair.value.repair_cost} 吗？`,
        })
        
        paying.value = true
        const toast = showLoadingToast({
          message: '支付中...',
          forbidClick: true,
          duration: 0
        })
        
        // 模拟支付延迟
        await new Promise(resolve => setTimeout(resolve, 1500))
        
        // 调用支付接口
        await repairAPI.payRepairCost(repair.value.id)
        
        toast.close()
        showSuccessToast('支付成功')
        
        // 延迟跳转到评价页面
        setTimeout(() => {
          router.replace(`/repair/${repair.value.id}`)
        }, 1000)
        
      } catch (error) {
        paying.value = false
        if (error === 'cancel') {
          // 用户取消
          return
        }
        console.error('支付失败:', error)
        showToast(error.message || '支付失败')
      }
    }
    
    onMounted(() => {
      loadDetail()
    })
    
    return {
      repair,
      paymentMethod,
      paying,
      handlePay
    }
  }
}
</script>

<style scoped>
.payment-page {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 70px;
}

.content {
  padding-top: 46px;
  padding-bottom: 16px;
}

.order-card,
.cost-card,
.payment-method-card {
  background: white;
  margin: 12px 16px;
  border-radius: 8px;
  overflow: hidden;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
  padding: 16px;
  background: #fafafa;
}

.cost-detail {
  padding: 16px;
}

.cost-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.cost-item .label {
  font-size: 14px;
  color: #646566;
}

.cost-item .value {
  font-size: 16px;
  color: #323233;
  font-weight: 500;
}

.cost-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.cost-total .label {
  font-size: 16px;
  color: #323233;
  font-weight: 600;
}

.cost-total .amount {
  font-size: 24px;
  color: #ee0a24;
  font-weight: bold;
}

.tips {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 16px;
  padding: 12px;
  background: #fff7e6;
  border-radius: 8px;
  font-size: 13px;
  color: #ed6a0c;
}

.footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px;
  background: white;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
}

:deep(.van-radio__icon--checked .van-icon) {
  background-color: #1989fa;
  border-color: #1989fa;
}
</style>
