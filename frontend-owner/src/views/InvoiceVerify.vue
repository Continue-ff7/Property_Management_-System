<template>
  <div class="invoice-verify-page">
    <van-nav-bar 
      title="发票验证" 
      left-arrow
      @click-left="$router.back()"
      fixed 
    />
    
    <div class="content">
      <div class="verify-card">
        <div class="verify-header">
          <van-icon name="passed" color="#07c160" size="48" />
          <div class="verify-title">发票验证成功</div>
          <div class="verify-subtitle">该发票为有效电子发票</div>
        </div>
        
        <div class="invoice-info">
          <div class="info-row">
            <span class="label">发票号码</span>
            <span class="value">{{ invoiceNo }}</span>
          </div>
          <div class="info-row">
            <span class="label">发票代码</span>
            <span class="value">{{ invoiceCode }}</span>
          </div>
          <div class="info-row">
            <span class="label">开票金额</span>
            <span class="value amount">¥{{ amount }}</span>
          </div>
          <div class="info-row">
            <span class="label">开票日期</span>
            <span class="value">{{ date }}</span>
          </div>
          <div class="info-row">
            <span class="label">开票单位</span>
            <span class="value">智慧物业管理有限公司</span>
          </div>
        </div>
        
        <div class="verify-footer">
          <div class="verify-time">验证时间：{{ verifyTime }}</div>
        </div>
      </div>
      
      <div class="tips">
        <van-icon name="info-o" /> 
        <span>此发票信息仅供验证使用，如有疑问请联系开票单位</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

export default {
  name: 'InvoiceVerify',
  setup() {
    const route = useRoute()
    
    const invoiceNo = ref('')
    const invoiceCode = ref('')
    const amount = ref('')
    const date = ref('')
    const verifyTime = ref('')
    
    onMounted(() => {
      // 从 URL 参数获取发票信息
      invoiceNo.value = route.query.no || '-'
      invoiceCode.value = route.query.code || '-'
      amount.value = route.query.amt || '0.00'
      date.value = route.query.date || '-'
      verifyTime.value = new Date().toLocaleString('zh-CN')
    })
    
    return {
      invoiceNo,
      invoiceCode,
      amount,
      date,
      verifyTime
    }
  }
}
</script>

<style scoped>
.invoice-verify-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #e8f4ff 0%, #d6ebff 100%);
  padding-bottom: 20px;
}

.content {
  padding: 56px 16px 20px;
}

.verify-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.verify-header {
  text-align: center;
  padding-bottom: 20px;
  border-bottom: 1px dashed #e5e5e5;
}

.verify-title {
  font-size: 20px;
  font-weight: bold;
  color: #323233;
  margin-top: 12px;
}

.verify-subtitle {
  font-size: 14px;
  color: #969799;
  margin-top: 8px;
}

.invoice-info {
  padding: 20px 0;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  font-size: 14px;
}

.info-row .label {
  color: #646566;
}

.info-row .value {
  color: #323233;
  font-weight: 500;
}

.info-row .value.amount {
  color: #1989fa;
  font-size: 18px;
  font-weight: bold;
}

.verify-footer {
  padding-top: 16px;
  border-top: 1px dashed #e5e5e5;
  text-align: center;
}

.verify-time {
  font-size: 12px;
  color: #969799;
}

.tips {
  margin-top: 16px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  font-size: 12px;
  color: #646566;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
