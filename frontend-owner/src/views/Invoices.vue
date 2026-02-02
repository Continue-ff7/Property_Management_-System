<template>
  <div class="invoices-page">
    <van-nav-bar 
      title="发票下载" 
      left-arrow
      @click-left="$router.back()"
      fixed 
    />
    
    <div class="content">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="onLoad"
        >
          <!-- 发票卡片 -->
          <div v-for="bill in bills" :key="bill.id" class="invoice-card" @click="previewInvoice(bill)">
            <div class="invoice-header">
              <div class="invoice-title">
                <van-icon name="description" color="#1989fa" size="20" />
                <span>电子发票</span>
              </div>
              <van-tag type="success" size="medium">已开具</van-tag>
            </div>
            
            <div class="invoice-divider"></div>
            
            <div class="invoice-body">
              <div class="invoice-row">
                <span class="label">发票号码</span>
                <span class="value">{{ generateInvoiceNo(bill.id) }}</span>
              </div>
              <div class="invoice-row">
                <span class="label">开票日期</span>
                <span class="value">{{ formatDate(bill.paid_at) }}</span>
              </div>
              <div class="invoice-row">
                <span class="label">费用类型</span>
                <span class="value">{{ getFeeTypeText(bill.fee_type) }}</span>
              </div>
              <div class="invoice-row">
                <span class="label">账期</span>
                <span class="value">{{ bill.billing_period }}</span>
              </div>
              <div class="invoice-row">
                <span class="label">房产地址</span>
                <span class="value">{{ bill.property_info }}</span>
              </div>
              
              <div class="invoice-amount">
                <span class="amount-label">开票金额</span>
                <span class="amount">¥{{ Number(bill.amount || 0).toFixed(2) }}</span>
              </div>
            </div>
            
            <div class="invoice-footer">
              <van-button 
                type="primary" 
                size="small" 
                icon="down" 
                plain
                @click.stop="downloadInvoice(bill)"
              >
                下载发票
              </van-button>
            </div>
          </div>
          
          <van-empty v-if="bills.length === 0" description="暂无可开票记录" />
        </van-list>
      </van-pull-refresh>
    </div>
    
    <!-- 发票预览弹窗 -->
    <van-popup 
      v-model="showPreview" 
      position="bottom" 
      :style="{ height: '80%' }"
      round
    >
      <div class="preview-container" v-show="currentBill">
        <div class="preview-header">
          <van-icon name="cross" @click="showPreview = false" />
          <span>发票预览</span>
          <van-button type="primary" size="small" @click="downloadInvoice(currentBill)">
            下载
          </van-button>
        </div>
        
        <!-- 模拟发票内容 -->
        <div class="invoice-preview" ref="invoiceRef">
          <div class="preview-title">电子发票</div>
          <div class="preview-subtitle">Electronic Invoice</div>
          
          <div class="preview-section">
            <div class="preview-row">
              <span class="preview-label">发票号码：</span>
              <span>{{ generateInvoiceNo(currentBill.id) }}</span>
            </div>
            <div class="preview-row">
              <span class="preview-label">开票日期：</span>
              <span>{{ formatDate(currentBill.paid_at) }}</span>
            </div>
            <div class="preview-row">
              <span class="preview-label">发票代码：</span>
              <span>{{ generateInvoiceCode() }}</span>
            </div>
          </div>
          
          <div class="preview-divider"></div>
          
          <div class="preview-section">
            <div class="preview-subtitle2">购买方信息</div>
            <div class="preview-row">
              <span class="preview-label">名称：</span>
              <span>{{ userInfo.name || userInfo.username }}</span>
            </div>
            <div class="preview-row">
              <span class="preview-label">地址：</span>
              <span>{{ currentBill.property_info }}</span>
            </div>
          </div>
          
          <div class="preview-divider"></div>
          
          <div class="preview-section">
            <div class="preview-subtitle2">销售方信息</div>
            <div class="preview-row">
              <span class="preview-label">名称：</span>
              <span>智慧物业管理有限公司</span>
            </div>
            <div class="preview-row">
              <span class="preview-label">地址：</span>
              <span>XX市XX区XX路XX号</span>
            </div>
            <div class="preview-row">
              <span class="preview-label">电话：</span>
              <span>400-888-8888</span>
            </div>
          </div>
          
          <div class="preview-divider"></div>
          
          <div class="preview-section">
            <div class="preview-subtitle2">费用明细</div>
            <table class="preview-table">
              <thead>
                <tr>
                  <th>项目名称</th>
                  <th>账期</th>
                  <th>金额</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ getFeeTypeText(currentBill.fee_type) }}</td>
                  <td>{{ currentBill.billing_period }}</td>
                  <td>¥{{ Number(currentBill.amount || 0).toFixed(2) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <div class="preview-total">
            <span>价税合计（大写）：</span>
            <span class="total-amount">{{ convertToChinese(currentBill.amount) }}</span>
          </div>
          
          <div class="preview-total">
            <span>价税合计（小写）：</span>
            <span class="total-amount">¥{{ Number(currentBill.amount || 0).toFixed(2) }}</span>
          </div>
          
          <div class="preview-footer">
            <div>开票人：系统自动</div>
            <div>复核：自动复核</div>
            <div>收款人：财务部</div>
          </div>
          
          <div class="preview-qrcode">
            <img v-if="qrCodeUrl" :src="qrCodeUrl" alt="发票二维码" class="qrcode-image" />
            <div v-else class="qrcode-placeholder">二维码区域</div>
          </div>
        </div>
      </div>
    </van-popup>
    
    <!-- 隐藏的发票内容（用于生成PDF） -->
    <div v-if="currentBill" style="position: fixed; left: -9999px; top: 0; width: 800px;">
      <div class="invoice-preview" ref="invoiceRef">
        <div class="preview-title">电子发票</div>
        <div class="preview-subtitle">Electronic Invoice</div>
        
        <div class="preview-section">
          <div class="preview-row">
            <span class="preview-label">发票号码：</span>
            <span>{{ generateInvoiceNo(currentBill.id) }}</span>
          </div>
          <div class="preview-row">
            <span class="preview-label">开票日期：</span>
            <span>{{ formatDate(currentBill.paid_at) }}</span>
          </div>
          <div class="preview-row">
            <span class="preview-label">发票代码：</span>
            <span>{{ generateInvoiceCode() }}</span>
          </div>
        </div>
        
        <div class="preview-divider"></div>
        
        <div class="preview-section">
          <div class="preview-subtitle2">购买方信息</div>
          <div class="preview-row">
            <span class="preview-label">名称：</span>
            <span>{{ userInfo.name || userInfo.username }}</span>
          </div>
          <div class="preview-row">
            <span class="preview-label">地址：</span>
            <span>{{ currentBill.property_info }}</span>
          </div>
        </div>
        
        <div class="preview-divider"></div>
        
        <div class="preview-section">
          <div class="preview-subtitle2">销售方信息</div>
          <div class="preview-row">
            <span class="preview-label">名称：</span>
            <span>智慧物业管理有限公司</span>
          </div>
          <div class="preview-row">
            <span class="preview-label">地址：</span>
            <span>XX市XX区XX路XX号</span>
          </div>
          <div class="preview-row">
            <span class="preview-label">电话：</span>
            <span>400-888-8888</span>
          </div>
        </div>
        
        <div class="preview-divider"></div>
        
        <div class="preview-section">
          <div class="preview-subtitle2">费用明细</div>
          <table class="preview-table">
            <thead>
              <tr>
                <th>项目名称</th>
                <th>账期</th>
                <th>金额</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{{ getFeeTypeText(currentBill.fee_type) }}</td>
                <td>{{ currentBill.billing_period }}</td>
                <td>¥{{ Number(currentBill.amount || 0).toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div class="preview-total">
          <span>价税合计（大写）：</span>
          <span class="total-amount">{{ convertToChinese(currentBill.amount) }}</span>
        </div>
        
        <div class="preview-total">
          <span>价税合计（小写）：</span>
          <span class="total-amount">¥{{ Number(currentBill.amount || 0).toFixed(2) }}</span>
        </div>
        
        <div class="preview-footer">
          <div>开票人：系统自动</div>
          <div>复核：自动复核</div>
          <div>收款人：财务部</div>
        </div>
        
        <div class="preview-qrcode">
          <img v-if="qrCodeUrl" :src="qrCodeUrl" alt="发票二维码" class="qrcode-image" />
          <div v-else class="qrcode-placeholder">二维码区域</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { billAPI } from '@/api'
import { showToast, showNotify, showLoadingToast, closeToast } from 'vant'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import QRCode from 'qrcode'

export default {
  name: 'Invoices',
  setup() {
    const router = useRouter()
    const store = useStore()
    const userInfo = computed(() => store.state.userInfo)
    
    const bills = ref([])
    const loading = ref(false)
    const finished = ref(false)
    const refreshing = ref(false)
    const showPreview = ref(false)
    const currentBill = ref(null)
    const invoiceRef = ref(null)
    const qrCodeUrl = ref('') // 二维码图片URL
    
    // 加载已支付账单
    const loadBills = async () => {
      try {
        const data = await billAPI.getMyBills({ status: 'paid' })
        bills.value = data
        loading.value = false
        finished.value = true
      } catch (error) {
        console.error('加载失败:', error)
        showToast('加载失败')
        loading.value = false
        finished.value = true
      }
    }
    
    const onLoad = () => {
      loadBills()
    }
    
    const onRefresh = () => {
      finished.value = false
      loading.value = true
      loadBills()
      refreshing.value = false
    }
    
    // 生成发票号码
    const generateInvoiceNo = (billId) => {
      const date = new Date()
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      return `INV${year}${month}${String(billId).padStart(8, '0')}`
    }
    
    // 生成发票代码
    const generateInvoiceCode = () => {
      const date = new Date()
      const year = date.getFullYear()
      return `${year}1100000000`
    }
    
    // 格式化日期
    const formatDate = (dateStr) => {
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    }
    
    // 费用类型文本
    const getFeeTypeText = (type) => {
      const map = {
        property_management: '物业管理费',
        water: '水费',
        electricity: '电费',
        gas: '燃气费',
        parking: '停车费',
        other: '其他费用'
      }
      return map[type] || type
    }
    
    // 金额转大写
    const convertToChinese = (amount) => {
      const cnNums = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
      const cnIntRadice = ['', '拾', '佰', '仟']
      const cnIntUnits = ['', '万', '亿', '兆']
      const cnDecUnits = ['角', '分']
      const cnInteger = '整'
      const cnIntLast = '元'
      const maxNum = 999999999999.99
      
      let money = parseFloat(amount)
      if (money >= maxNum) {
        return '金额过大'
      }
      if (money === 0) {
        return cnNums[0] + cnIntLast + cnInteger
      }
      
      let chineseStr = ''
      let integerNum = Math.floor(money)
      let decimalNum = Math.round((money - integerNum) * 100)
      
      if (integerNum > 0) {
        let zeroCount = 0
        let IntLen = integerNum.toString().length
        for (let i = 0; i < IntLen; i++) {
          let n = integerNum % 10
          let p = Math.floor(i / 4)
          let q = i % 4
          if (n === 0) {
            zeroCount++
          } else {
            if (zeroCount > 0) {
              chineseStr = cnNums[0] + chineseStr
            }
            zeroCount = 0
            chineseStr = cnNums[n] + cnIntRadice[q] + chineseStr
          }
          if (q === 0 && zeroCount < 4) {
            chineseStr = cnIntUnits[p] + chineseStr
          }
          integerNum = Math.floor(integerNum / 10)
        }
        chineseStr = chineseStr + cnIntLast
      }
      
      if (decimalNum > 0) {
        let jiao = Math.floor(decimalNum / 10)
        let fen = decimalNum % 10
        if (jiao > 0) {
          chineseStr += cnNums[jiao] + cnDecUnits[0]
        }
        if (fen > 0) {
          chineseStr += cnNums[fen] + cnDecUnits[1]
        }
      } else {
        chineseStr += cnInteger
      }
      
      return chineseStr
    }
    
    // 预览发票
    const previewInvoice = async (bill) => {
      currentBill.value = bill
      
      // 生成二维码
      await generateQRCode(bill)
      
      showPreview.value = true
    }
    
    // 生成二维码
    const generateQRCode = async (bill) => {
      try {
        const invoiceNo = generateInvoiceNo(bill.id)
        const invoiceCode = generateInvoiceCode()
        const amount = Number(bill.amount || 0).toFixed(2)
        const date = formatDate(bill.paid_at)
        
        // 二维码内容：使用URL链接（微信支持）
        const baseUrl = window.location.origin
        const verifyUrl = `${baseUrl}/invoice-verify?no=${encodeURIComponent(invoiceNo)}&code=${encodeURIComponent(invoiceCode)}&amt=${encodeURIComponent(amount)}&date=${encodeURIComponent(date)}`
        
        console.log('二维码URL:', verifyUrl)
        
        // 生成二维码图片
        qrCodeUrl.value = await QRCode.toDataURL(verifyUrl, {
          width: 120,
          margin: 1,
          color: {
            dark: '#000000',
            light: '#FFFFFF'
          },
          errorCorrectionLevel: 'M'
        })
      } catch (error) {
        console.error('生成二维码失败:', error)
      }
    }
    
    // 下载发票（生成PDF）
    const downloadInvoice = async (bill) => {
      try {
        // 设置当前账单
        currentBill.value = bill
        
        // 生成二维码
        await generateQRCode(bill)
        
        // 如果预览窗口未打开，先打开预览窗口
        if (!showPreview.value) {
          showPreview.value = true
          // 等待弹窗动画完成
          await new Promise(resolve => setTimeout(resolve, 400))
        }
        
        // 等待 Vue DOM 更新
        await nextTick()
        await nextTick() // 双重 nextTick 确保内容完全渲染
        
        // 检查 invoiceRef 是否存在
        const element = invoiceRef.value
        console.log('invoiceRef.value:', element)
        
        if (!element) {
          console.error('发票元素未找到')
          showToast('发票内容未加载，请稍后重试')
          return
        }
        
        // 显示加载提示
        showLoadingToast({
          message: '正在生成PDF...',
          forbidClick: true,
          duration: 0
        })
        
        // 等待一下确保所有CSS样式应用完毕
        await new Promise(resolve => setTimeout(resolve, 300))
        
        // 使用 html2canvas 将发票内容转换为图片
        const canvas = await html2canvas(element, {
          scale: 2, // 提高清晰度
          useCORS: true,
          backgroundColor: '#ffffff',
          logging: false,
          windowWidth: element.scrollWidth,
          windowHeight: element.scrollHeight
        })
        
        // 计算PDF尺寸（A4纸张）
        const imgWidth = 210 // A4宽度（mm）
        const imgHeight = (canvas.height * imgWidth) / canvas.width
        
        // 创建PDF
        const pdf = new jsPDF({
          orientation: 'portrait',
          unit: 'mm',
          format: 'a4'
        })
        
        // 将canvas转换为图片并添加到PDF
        const imgData = canvas.toDataURL('image/png')
        pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight)
        
        // 生成文件名
        const invoiceNo = generateInvoiceNo(bill.id)
        const fileName = `发票_${invoiceNo}.pdf`
        
        // 下载PDF
        pdf.save(fileName)
        
        // 关闭加载提示
        closeToast()
        
        // 显示成功提示
        showNotify({
          type: 'success',
          message: `发票 ${invoiceNo} 已下载！`,
          duration: 2000
        })
        
      } catch (error) {
        console.error('生成PDF失败:', error)
        closeToast()
        showToast('生成PDF失败，请重试')
      }
    }
    
    onMounted(() => {
      loadBills()
    })
    
    return {
      bills,
      loading,
      finished,
      refreshing,
      showPreview,
      currentBill,
      invoiceRef,
      qrCodeUrl,
      userInfo,
      onLoad,
      onRefresh,
      generateInvoiceNo,
      generateInvoiceCode,
      formatDate,
      getFeeTypeText,
      convertToChinese,
      previewInvoice,
      downloadInvoice
    }
  }
}
</script>

<style scoped>
.invoices-page {
  min-height: 100vh;
  background-color: #f7f8fa;
  padding-bottom: 20px;
}

.content {
  padding-top: 46px;
  padding: 56px 16px 20px;
}

/* 发票卡片样式 */
.invoice-card {
  background: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.3s;
}

.invoice-card:active {
  transform: scale(0.98);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.invoice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.invoice-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: bold;
  color: #323233;
}

.invoice-divider {
  height: 1px;
  background: linear-gradient(to right, transparent, #e5e5e5, transparent);
  margin: 12px 0;
}

.invoice-body {
  padding: 8px 0;
}

.invoice-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  font-size: 14px;
}

.invoice-row .label {
  color: #969799;
  width: 80px;
  flex-shrink: 0;
}

.invoice-row .value {
  color: #323233;
  text-align: right;
  flex: 1;
}

.invoice-amount {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #e5e5e5;
}

.invoice-amount .amount-label {
  font-size: 14px;
  color: #646566;
}

.invoice-amount .amount {
  font-size: 22px;
  font-weight: bold;
  color: #1989fa;
}

.invoice-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
  text-align: right;
}

/* 发票预览样式 */
.preview-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #ebedf0;
  font-size: 16px;
  font-weight: bold;
}

.preview-header .van-icon {
  font-size: 20px;
  color: #969799;
  cursor: pointer;
}

.invoice-preview {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: white;
}

.preview-title {
  text-align: center;
  font-size: 24px;
  font-weight: bold;
  color: #323233;
  margin-bottom: 8px;
}

.preview-subtitle {
  text-align: center;
  font-size: 14px;
  color: #969799;
  margin-bottom: 24px;
}

.preview-subtitle2 {
  font-size: 15px;
  font-weight: bold;
  color: #646566;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #1989fa;
}

.preview-section {
  margin-bottom: 20px;
}

.preview-row {
  display: flex;
  padding: 6px 0;
  font-size: 14px;
  color: #323233;
}

.preview-label {
  color: #646566;
  min-width: 80px;
  flex-shrink: 0;
}

.preview-divider {
  height: 1px;
  background: #e5e5e5;
  margin: 16px 0;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
}

.preview-table th,
.preview-table td {
  border: 1px solid #e5e5e5;
  padding: 10px;
  text-align: center;
  font-size: 13px;
}

.preview-table th {
  background: #f7f8fa;
  font-weight: bold;
  color: #646566;
}

.preview-table td {
  color: #323233;
}

.preview-total {
  display: flex;
  align-items: center;
  padding: 8px 0;
  font-size: 14px;
  color: #323233;
}

.preview-total .total-amount {
  font-weight: bold;
  color: #1989fa;
  margin-left: 8px;
}

.preview-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e5e5e5;
  font-size: 13px;
  color: #646566;
}

.preview-qrcode {
  margin-top: 24px;
  text-align: center;
}

.qrcode-image {
  width: 120px;
  height: 120px;
  display: block;
  margin: 0 auto;
}

.qrcode-placeholder {
  width: 120px;
  height: 120px;
  margin: 0 auto;
  background: #f7f8fa;
  border: 2px dashed #dcdee0;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #969799;
  font-size: 12px;
}
</style>
