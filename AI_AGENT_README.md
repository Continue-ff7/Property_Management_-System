# AI Agent 功能使用说明

## 功能概述

AI助手基于DeepSeek Function Calling实现，可以帮助业主完成以下操作：

### 支持的功能

1. **查询账单信息** - 查看所有水费、电费、物业费账单
2. **查询报修记录** - 查看所有报修工单的状态和进度
3. **查询房产信息** - 查看绑定的房产详情
4. **创建报修工单** - 通过对话方式提交报修（无需上传图片）

## 技术实现

### 架构设计

```
用户输入 → DeepSeek API → Function Calling → 后端API → 数据库
                ↓
          AI理解意图
                ↓
          调用对应工具
                ↓
          格式化返回结果
```

### 核心组件

#### 1. 后端API (backend/app/api/v1/ai_assistant.py)

提供4个RESTful接口：

- `GET /api/v1/ai/bills` - 查询用户账单
- `GET /api/v1/ai/repairs` - 查询用户报修记录
- `GET /api/v1/ai/properties` - 查询用户房产信息
- `POST /api/v1/ai/create-repair` - 创建报修工单

#### 2. 前端集成 (frontend-owner/src/views/AIAssistant.vue)

- DeepSeek API调用
- 流式响应处理
- Function Calling机制
- 工具调用状态展示

#### 3. API配置

- API Key: `xxxxxxxxxxxxxxxxx`
- API URL: `https://api.deepseek.com/chat/completions`
- Model: `deepseek-chat`

### 工具定义

```javascript
const tools = [
  {
    type: 'function',
    function: {
      name: 'get_bills',
      description: '查询用户的账单信息，包括水费、电费、物业费等',
      parameters: { type: 'object', properties: {}, required: [] }
    }
  },
  {
    type: 'function',
    function: {
      name: 'get_repairs',
      description: '查询用户的报修记录',
      parameters: { type: 'object', properties: {}, required: [] }
    }
  },
  {
    type: 'function',
    function: {
      name: 'get_properties',
      description: '查询用户的房产信息',
      parameters: { type: 'object', properties: {}, required: [] }
    }
  },
  {
    type: 'function',
    function: {
      name: 'create_repair',
      description: '帮用户创建报修工单',
      parameters: {
        type: 'object',
        properties: {
          property_id: { type: 'number', description: '房产ID' },
          description: { type: 'string', description: '报修问题描述' },
          urgency_level: { 
            type: 'string', 
            enum: ['low', 'medium', 'high', 'urgent'],
            description: '紧急程度'
          }
        },
        required: ['property_id', 'description']
      }
    }
  }
]
```

## 使用示例

### 示例1：查询账单

**用户输入：** "帮我查一下我的账单"

**AI处理流程：**
1. 理解意图 → 需要查询账单
2. 调用工具 → `get_bills()`
3. 获取数据 → 从后端API获取账单列表
4. 格式化回复 → 以友好的方式展示账单信息

**AI回复：**
```
您共有 3 条账单记录：

1. 【水费】
   房产：某小区1号楼101室
   金额：¥120.50
   账单月份：2025-01
   状态：未缴费

2. 【电费】
   房产：某小区1号楼101室
   金额：¥250.00
   账单月份：2025-01
   状态：已缴费
...
```

### 示例2：查询报修记录

**用户输入：** "我上次提交的报修处理的怎么样了？"

**AI处理流程：**
1. 理解意图 → 查询报修进度
2. 调用工具 → `get_repairs()`
3. 获取数据 → 从后端API获取报修列表
4. 格式化回复 → 展示报修状态

**AI回复：**
```
您共有 2 条报修记录：

1. 【工单号: R20251216001】
   房产：某小区1号楼101室
   问题：水龙头漏水
   状态：维修中
   提交时间：2025-12-15 10:30:00

2. 【工单号: R20251210002】
   房产：某小区1号楼101室
   问题：门锁损坏
   状态：已完成
   提交时间：2025-12-10 14:20:00
```

### 示例3：创建报修工单

**用户输入：** "我家的空调坏了，帮我报修一下"

**AI处理流程：**
1. 理解意图 → 需要创建报修
2. 询问必要信息 → 房产ID、问题描述、紧急程度
3. 调用工具 → `create_repair({ property_id: 1, description: '空调故障', urgency_level: 'high' })`
4. 创建工单 → 调用后端API创建报修记录
5. 确认反馈 → 告知用户工单号

**AI回复：**
```
报修工单创建成功！
工单号：R20251216003
状态：待处理
物业工作人员会尽快处理您的报修。
```

## 工具调用状态展示

在AI回复中会显示工具调用状态：

- 🕐 **执行中** (橙色) - 工具正在调用
- ✓ **成功** (绿色) - 工具调用成功
- ✗ **失败** (红色) - 工具调用失败

## 对话历史管理

系统会维护完整的对话历史，包括：
- 用户消息
- AI回复
- 工具调用记录
- 工具返回结果

这使得AI能够：
- 理解上下文
- 进行多轮对话
- 智能推断用户意图

## 流式响应

使用Server-Sent Events (SSE)实现流式响应：
- 实时显示AI回复
- 逐字展示，提升用户体验
- 工具调用状态实时更新

## 错误处理

### 1. API调用失败
```
抱歉，我遇到了一些问题。请稍后再试或联系人工客服。
```

### 2. 工具执行失败
```
查询账单信息失败，请稍后重试。
```

### 3. 参数缺失
AI会主动询问缺失的参数：
```
好的，我帮您创建报修工单。请问是哪个房产需要报修？
```

## 快捷按钮

为提升用户体验，提供常见问题快捷按钮：
- 查询我的账单
- 查看报修记录
- 我要报修
- 查询房产信息

## 未来扩展

可以继续添加更多工具函数：
- 缴费功能
- 公告查询
- 投诉建议
- 预约服务
- 访客登记
- 车辆管理

只需在tools数组中添加新的工具定义，并实现对应的toolFunctions即可。
