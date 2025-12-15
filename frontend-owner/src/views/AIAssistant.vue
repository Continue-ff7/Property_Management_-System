<template>
  <div class="ai-assistant-page">
    <!-- 顶部导航栏 -->
    <van-nav-bar
      title="AI助手"
      left-arrow
      @click-left="$router.back()"
      fixed
      placeholder
    >
      <template #right>
        <van-icon name="user-o" size="20" />
      </template>
    </van-nav-bar>

    <!-- 聊天消息区域 -->
    <div class="chat-container" ref="chatContainer">
      <div class="message-list">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['message-item', msg.type]"
        >
          <!-- AI消息 -->
          <div v-if="msg.type === 'ai'" class="ai-message">
            <div class="avatar">
              <van-icon name="service-o" size="24" color="#1989fa" />
            </div>
            <div class="message-content">
              <div class="message-bubble">{{ msg.content }}</div>
              <!-- 工具调用状态显示 -->
              <div v-if="msg.tools && msg.tools.length > 0" class="tool-calls">
                <div v-for="(tool, idx) in msg.tools" :key="idx" class="tool-item">
                  <van-icon 
                    :name="tool.status === 'executing' ? 'clock-o' : tool.status === 'success' ? 'checked' : 'cross'"
                    :color="tool.status === 'executing' ? '#ff9800' : tool.status === 'success' ? '#07c160' : '#ee0a24'"
                    size="14"
                  />
                  <span>{{ tool.name }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 用户消息 -->
          <div v-if="msg.type === 'user'" class="user-message">
            <div class="message-content">
              <div class="message-bubble">{{ msg.content }}</div>
            </div>
            <div class="avatar">
              <van-icon name="user-o" size="24" color="#07c160" />
            </div>
          </div>
        </div>

        <!-- 加载中状态 -->
        <div v-if="loading" class="message-item ai">
          <div class="ai-message">
            <div class="avatar">
              <van-icon name="service-o" size="24" color="#1989fa" />
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 常见问题快捷按钮 -->
    <div v-if="showQuickButtons" class="quick-buttons">
      <div class="quick-title">常见问题</div>
      <div class="button-grid">
        <van-button
          v-for="(btn, index) in quickButtons"
          :key="index"
          size="small"
          plain
          type="primary"
          @click="sendQuickQuestion(btn.text)"
        >
          {{ btn.text }}
        </van-button>
      </div>
    </div>

    <!-- 底部输入框 -->
    <div class="input-area">
      <van-field
        v-model="inputText"
        placeholder="请输入您的问题..."
        @keyup.enter="sendMessage"
      >
        <template #button>
          <van-button
            size="small"
            type="primary"
            :disabled="!inputText.trim() || loading"
            @click="sendMessage"
          >
            发送
          </van-button>
        </template>
      </van-field>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { showToast, showLoadingToast, closeToast } from 'vant'
import { aiAssistantAPI } from '@/api'

export default {
  name: 'AIAssistant',
  setup() {
    const messages = ref([
      {
        type: 'ai',
        content: '您好！我是您的AI助手，我可以帮您：\n1. 查询账单信息\n2. 查询报修记录\n3. 帮您提交报修\n\n有什么可以帮助您的吗？'
      }
    ])
    const inputText = ref('')
    const loading = ref(false)
    const chatContainer = ref(null)
    const showQuickButtons = ref(true)
    
    // 对话历史（用于发送给DeepSeek API）
    const conversationHistory = ref([
      {
        role: 'system',
        content: '你是一个物业管理系统的AI助手。你可以帮助业主查询账单、报修记录、房产信息，也可以帮助他们提交报修工单。请用友好、专业的语气回答问题。'
      }
    ])
    
    // 流式响应的当前消息
    const streamingMessage = ref('')
    
    // 工具调用状态
    const toolCallStatus = ref([])

    // 常见问题快捷按钮
    const quickButtons = ref([
      { text: '查询我的账单' },
      { text: '查看报修记录' },
      { text: '我要报修' },
      { text: '查询房产信息' }
    ])
    
    // DeepSeek API配置
    const DEEPSEEK_API_KEY = process.env.VUE_APP_DEEPSEEK_API_KEY
    const DEEPSEEK_API_URL = 'https://api.deepseek.com/chat/completions'
    
    // 定义可用的工具
    const tools = [
      {
        type: 'function',
        function: {
          name: 'get_bills',
          description: '查询用户的账单信息，包括水费、电费、物业费等未缴费和已缴费账单',
          parameters: {
            type: 'object',
            properties: {},
            required: []
          }
        }
      },
      {
        type: 'function',
        function: {
          name: 'get_repairs',
          description: '查询用户的报修记录，包括报修状态、工单号、问题描述等',
          parameters: {
            type: 'object',
            properties: {},
            required: []
          }
        }
      },
      {
        type: 'function',
        function: {
          name: 'get_properties',
          description: '查询用户的房产信息，包括房产地址、面积等',
          parameters: {
            type: 'object',
            properties: {},
            required: []
          }
        }
      },
      {
        type: 'function',
        function: {
          name: 'create_repair',
          description: '帮用户创建报修工单，需要提供房产ID、问题描述和紧急程度',
          parameters: {
            type: 'object',
            properties: {
              property_id: {
                type: 'number',
                description: '房产ID，必须是用户拥有的房产'
              },
              description: {
                type: 'string',
                description: '报修问题的详细描述'
              },
              urgency_level: {
                type: 'string',
                description: '紧急程度，可选值：low(低)、medium(中)、high(高)、urgent(紧急)',
                enum: ['low', 'medium', 'high', 'urgent']
              }
            },
            required: ['property_id', 'description']
          }
        }
      }
    ]
    
    // 工具函数实现
    const toolFunctions = {
      get_bills: async () => {
        try {
          const response = await aiAssistantAPI.getBills()
          const bills = response.data || []
          
          if (bills.length === 0) {
            return '您当前没有任何账单记录。'
          }
          
          let result = `您共有 ${bills.length} 条账单记录：\n\n`
          bills.forEach((bill, index) => {
            result += `${index + 1}. 【${bill.type_text || bill.type}】\n`
            result += `   房产：${bill.property_info}\n`
            result += `   金额：￥${bill.amount}\n`
            result += `   账单月份：${bill.billing_month}\n`
            result += `   状态：${bill.status_text || (bill.status === 'paid' ? '已缴费' : '未缴费')}\n\n`
          })
          
          return result
        } catch (error) {
          console.error('Error fetching bills:', error)
          return '查询账单信息失败，请稍后重试。'
        }
      },
      
      get_repairs: async () => {
        try {
          const response = await aiAssistantAPI.getRepairs()
          const repairs = response.data || []
          
          if (repairs.length === 0) {
            return '您当前没有任何报修记录。'
          }
          
          let result = `您共有 ${repairs.length} 条报修记录：\n\n`
          repairs.forEach((repair, index) => {
            result += `${index + 1}. 【工单号: ${repair.order_number}】\n`
            result += `   房产：${repair.property_info}\n`
            result += `   问题：${repair.description}\n`
            result += `   状态：${repair.status_text || repair.status}\n`
            result += `   提交时间：${repair.created_at}\n\n`
          })
          
          return result
        } catch (error) {
          console.error('Error fetching repairs:', error)
          return '查询报修记录失败，请稍后重试。'
        }
      },
      
      get_properties: async () => {
        try {
          const response = await aiAssistantAPI.getProperties()
          const properties = response.data || []
          
          if (properties.length === 0) {
            return '您当前没有绑定任何房产。'
          }
          
          let result = `您共有 ${properties.length} 套房产：\n\n`
          properties.forEach((prop, index) => {
            result += `${index + 1}. 房产ID: ${prop.id}\n`
            result += `   地址：${prop.full_address}\n`
            result += `   面积：${prop.area}m²\n\n`
          })
          
          return result
        } catch (error) {
          console.error('Error fetching properties:', error)
          return '查询房产信息失败，请稍后重试。'
        }
      },
      
      create_repair: async (params) => {
        try {
          const { property_id, description, urgency_level = 'medium' } = params
          const response = await aiAssistantAPI.createRepair({
            property_id,
            description,
            urgency_level
          })
          
          if (response.code === 200 || response.success) {
            return `报修工单创建成功！\n工单号：${response.data.order_number}\n状态：待处理\n物业工作人员会尽快处理您的报修。`
          } else {
            return `创建报修工单失败：${response.message || '未知错误'}`
          }
        } catch (error) {
          console.error('Error creating repair:', error)
          const errorMsg = error.response?.data?.message || error.message || '未知错误'
          return `创建报修工单失败：${errorMsg}`
        }
      }
    }

    // 发送消息
    const sendMessage = async () => {
      if (!inputText.value.trim()) return

      const userMessage = inputText.value.trim()
      
      // 添加用户消息
      messages.value.push({
        type: 'user',
        content: userMessage
      })
      
      // 添加到对话历史
      conversationHistory.value.push({
        role: 'user',
        content: userMessage
      })

      // 清空输入框
      inputText.value = ''
      
      // 隐藏快捷按钮
      showQuickButtons.value = false

      // 滚动到底部
      await nextTick()
      scrollToBottom()

      // 显示加载状态
      loading.value = true
      streamingMessage.value = ''
      
      // 调用DeepSeek API
      await callDeepSeekAPI()
    }
    
    // 调用DeepSeek API
    const callDeepSeekAPI = async () => {
      try {
        const response = await fetch(DEEPSEEK_API_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${DEEPSEEK_API_KEY}`
          },
          body: JSON.stringify({
            model: 'deepseek-chat',
            messages: conversationHistory.value,
            temperature: 0.7,
            stream: true,
            tools: tools
          })
        })
        
        if (!response.ok) {
          throw new Error(`API request failed: ${response.status}`)
        }
        
        await handleStreamResponse(response)
      } catch (error) {
        console.error('Error calling DeepSeek API:', error)
        messages.value.push({
          type: 'ai',
          content: '抱歉，我遇到了一些问题。请稍后再试或联系人工客服。'
        })
        loading.value = false
        await nextTick()
        scrollToBottom()
      }
    }
    
    // 处理流式响应
    const handleStreamResponse = async (response) => {
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let toolCalls = []
      let currentToolCall = null
      
      try {
        for(;;) {
          const { done, value } = await reader.read()
          if (done) break
          
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''
          
          for (const line of lines) {
            if (!line.trim() || !line.startsWith('data: ')) continue
            
            const data = line.slice(6)
            if (data === '[DONE]') {
              // 流结束，检查是否有工具调用
              if (toolCalls.length > 0) {
                await handleToolCalls(toolCalls)
              } else if (streamingMessage.value) {
                // 没有工具调用，直接显示AI回复
                messages.value.push({
                  type: 'ai',
                  content: streamingMessage.value
                })
                conversationHistory.value.push({
                  role: 'assistant',
                  content: streamingMessage.value
                })
              }
              loading.value = false
              await nextTick()
              scrollToBottom()
              continue
            }
            
            try {
              const parsed = JSON.parse(data)
              const delta = parsed.choices?.[0]?.delta
              
              if (!delta) continue
              
              // 处理工具调用
              if (delta.tool_calls) {
                for (const toolCall of delta.tool_calls) {
                  const index = toolCall.index
                  
                  if (!toolCalls[index]) {
                    toolCalls[index] = {
                      id: toolCall.id || '',
                      type: toolCall.type || 'function',
                      function: {
                        name: toolCall.function?.name || '',
                        arguments: toolCall.function?.arguments || ''
                      }
                    }
                  } else {
                    if (toolCall.id) toolCalls[index].id = toolCall.id
                    if (toolCall.function?.name) toolCalls[index].function.name = toolCall.function.name
                    if (toolCall.function?.arguments) {
                      toolCalls[index].function.arguments += toolCall.function.arguments
                    }
                  }
                }
              }
              
              // 处理文本内容
              if (delta.content) {
                streamingMessage.value += delta.content
                
                // 实时显示流式文本（更新最后一条AI消息）
                const lastMsg = messages.value[messages.value.length - 1]
                if (lastMsg && lastMsg.type === 'ai' && !lastMsg.tools) {
                  lastMsg.content = streamingMessage.value
                } else {
                  messages.value.push({
                    type: 'ai',
                    content: streamingMessage.value
                  })
                }
                
                await nextTick()
                scrollToBottom()
              }
            } catch (e) {
              console.warn('Failed to parse line:', line, e)
            }
          }
        }
      } catch (error) {
        console.error('Stream reading error:', error)
        throw error
      }
    }
    
    // 处理工具调用
    const handleToolCalls = async (toolCalls) => {
      const toolResults = []
      
      // 显示AI正在调用工具
      const toolMessage = {
        type: 'ai',
        content: '正在查询相关信息...',
        tools: []
      }
      
      for (const toolCall of toolCalls) {
        const toolName = toolCall.function.name
        const toolArgs = toolCall.function.arguments ? JSON.parse(toolCall.function.arguments) : {}
        
        const toolNameMap = {
          get_bills: '查询账单',
          get_repairs: '查询报修记录',
          get_properties: '查询房产信息',
          create_repair: '创建报修工单'
        }
        
        toolMessage.tools.push({
          name: toolNameMap[toolName] || toolName,
          status: 'executing'
        })
      }
      
      messages.value.push(toolMessage)
      await nextTick()
      scrollToBottom()
      
      // 执行工具调用
      for (let i = 0; i < toolCalls.length; i++) {
        const toolCall = toolCalls[i]
        const toolName = toolCall.function.name
        const toolArgs = toolCall.function.arguments ? JSON.parse(toolCall.function.arguments) : {}
        
        try {
          const result = await toolFunctions[toolName](toolArgs)
          toolResults.push({
            tool_call_id: toolCall.id,
            role: 'tool',
            name: toolName,
            content: result
          })
          
          toolMessage.tools[i].status = 'success'
        } catch (error) {
          console.error(`Error executing tool ${toolName}:`, error)
          toolResults.push({
            tool_call_id: toolCall.id,
            role: 'tool',
            name: toolName,
            content: `执行失败: ${error.message}`
          })
          
          toolMessage.tools[i].status = 'error'
        }
      }
      
      // 更新工具执行状态
      await nextTick()
      
      // 将工具调用和结果添加到对话历史
      conversationHistory.value.push({
        role: 'assistant',
        tool_calls: toolCalls.map(tc => ({
          id: tc.id,
          type: 'function',
          function: {
            name: tc.function.name,
            arguments: tc.function.arguments
          }
        }))
      })
      
      for (const result of toolResults) {
        conversationHistory.value.push(result)
      }
      
      // 继续对话，让AI根据工具结果给出最终回复
      streamingMessage.value = ''
      await callDeepSeekAPI()
    }

    // 发送快捷问题
    const sendQuickQuestion = (question) => {
      inputText.value = question
      sendMessage()
    }

    // 滚动到底部
    const scrollToBottom = () => {
      if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
      }
    }

    onMounted(() => {
      scrollToBottom()
    })

    return {
      messages,
      inputText,
      loading,
      chatContainer,
      showQuickButtons,
      quickButtons,
      sendMessage,
      sendQuickQuestion
    }
  }
}
</script>

<style scoped>
.ai-assistant-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f7f8fa;
}

/* 聊天容器 */
.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  padding-bottom: 80px;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 消息项 */
.message-item {
  display: flex;
  width: 100%;
}

/* AI消息 */
.ai-message {
  display: flex;
  gap: 8px;
  max-width: 80%;
}

.ai-message .avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e8f4ff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ai-message .message-bubble {
  background: white;
  padding: 12px 16px;
  border-radius: 0 12px 12px 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  word-wrap: break-word;
  white-space: pre-line;
  line-height: 1.5;
  color: #333;
}

/* 工具调用状态 */
.tool-calls {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f7f8fa;
  border-radius: 8px;
  font-size: 12px;
}

.tool-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  color: #646566;
}

/* 用户消息 */
.user-message {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  max-width: 80%;
  margin-left: auto;
}

.user-message .avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e8ffe8;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-message .message-bubble {
  background: #1989fa;
  color: white;
  padding: 12px 16px;
  border-radius: 12px 0 12px 12px;
  word-wrap: break-word;
  white-space: pre-line;
  line-height: 1.5;
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: white;
  border-radius: 0 12px 12px 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #c8c9cc;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    opacity: 0.3;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-6px);
  }
}

/* 快捷按钮区域 */
.quick-buttons {
  background: white;
  padding: 16px;
  border-top: 1px solid #ebedf0;
  margin-bottom: 60px;
}

.quick-title {
  font-size: 14px;
  color: #646566;
  margin-bottom: 12px;
}

.button-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.button-grid .van-button {
  border-radius: 8px;
}

/* 输入区域 */
.input-area {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  padding: 8px 16px;
  border-top: 1px solid #ebedf0;
  z-index: 100;
}

.input-area .van-field {
  border-radius: 20px;
  background: #f7f8fa;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .chat-container {
    padding: 12px;
  }
  
  .ai-message .message-bubble,
  .user-message .message-bubble {
    max-width: 100%;
  }
}
</style>
