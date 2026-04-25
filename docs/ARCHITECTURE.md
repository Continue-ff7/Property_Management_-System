# 物业管理系统 - 前后端通信架构文档

> 本文档详细说明项目的前后端通信机制、代理转发原理、WebSocket 连接方式、内网穿透原理，以及本地开发与公网部署的访问方式。

---

## 目录

1. [项目架构概览](#1-项目架构概览)
2. [前后端通信方式](#2-前后端通信方式)
3. [代理转发机制详解](#3-代理转发机制详解)
4. [WebSocket 通信机制](#4-websocket-通信机制)
5. [动态地址适配原理](#5-动态地址适配原理)
6. [内网穿透原理](#6-内网穿透原理)
7. [本地开发访问方式](#7-本地开发访问方式)
8. [公网部署访问方式](#8-公网部署访问方式)
9. [常见问题解答](#9-常见问题解答)

---

## 1. 项目架构概览

### 1.1 技术栈

```
前端技术栈：
├── 管理员端：Vue 2 + Element Plus + Webpack
├── 业主端：Vue 2 + Vant UI + Webpack
└── 共同特性：axios、WebSocket、PWA

后端技术栈：
├── FastAPI (Python Web 框架)
├── TortoiseORM (异步 ORM)
├── MySQL (数据库)
└── WebSocket (实时通信)
```

### 1.2 端口配置

| 服务 | 本地端口 | 说明 |
|------|---------|------|
| 后端 API | 8088 | FastAPI 服务 |
| 管理员前端 | 8080 | Vue DevServer |
| 业主端前端 | 8081 | Vue DevServer |
| MySQL | 3306 | 数据库 |

---

## 2. 前后端通信方式

### 2.1 通信方式分类

项目使用**混合通信模式**：

```
通信方式分为两种：
├── HTTP/HTTPS API 请求（RESTful API）
│   ├── 通过 axios 发送
│   ├── 走 webpack-dev-server 代理（开发环境）
│   └── 用于：CRUD 操作、数据查询、文件上传等
│
└── WebSocket 连接（实时通信）
    ├── 直接连接后端（不走代理）
    ├── 保持长连接
    └── 用于：实时通知、聊天消息、状态推送
```

### 2.2 为什么使用混合模式？

**HTTP API 的特点：**
- ✅ 请求-响应模式
- ✅ 适合 CRUD 操作
- ✅ 可以走代理（避免跨域）
- ❌ 不支持服务器主动推送

**WebSocket 的特点：**
- ✅ 全双工通信
- ✅ 服务器可主动推送
- ✅ 适合实时通知
- ❌ 不能走 HTTP 代理（需要 WebSocket 代理）

---

## 3. 代理转发机制详解

### 3.1 什么是代理转发？

**代理转发（Proxy）** 是 webpack-dev-server 提供的功能，用于在开发环境解决跨域问题。

### 3.2 跨域问题

**浏览器同源策略：**

```
同源 = 协议 + 域名 + 端口 完全相同

示例：
http://localhost:8080  (前端)
http://localhost:8088  (后端)
    ↓
端口不同 → 不同源 → 跨域 → 浏览器阻止
```

### 3.3 代理如何解决跨域？

**代理转发流程：**

```
                  浏览器                    Dev Server                后端
                    │                          │                       │
1. 发起请求         │ /api/v1/complaints       │                       │
   ├─────────────→  │                          │                       │
                    │                          │                       │
2. 同源请求         │  http://localhost:8080   │                       │
   （不跨域）       │  /api/v1/complaints      │                       │
                    │                          │                       │
3. 代理拦截         │                          │ 检测到 /api 前缀      │
                    │                          │ 触发代理规则          │
                    │                          │                       │
4. 转发请求         │                          │ http://localhost:8088 │
                    │                          │ /api/v1/complaints    │
                    │                          ├──────────────────────→│
                    │                          │                       │
5. 后端响应         │                          │     ← 数据 ←          │
                    │                          │                       │
6. 返回浏览器       │     ← 数据 ←             │                       │
                    │                          │                       │
```

**关键点：**
- ✅ 浏览器看到的是同源请求（`localhost:8080` → `localhost:8080`）
- ✅ 实际请求由 Dev Server 转发到后端（`localhost:8080` → `localhost:8088`）
- ✅ 转发在服务器端完成，不触发浏览器的跨域检查

### 3.4 代理配置

**管理员端配置（frontend-admin/vue.config.js）：**

```javascript
module.exports = defineConfig({
  devServer: {
    port: 8080,
    allowedHosts: 'all',  // 允许内网穿透访问
    proxy: {
      '/api': {
        target: 'http://localhost:8088',  // 后端地址
        changeOrigin: true                // 修改请求头的 Origin
      }
    }
  }
})
```

**业主端配置（frontend-owner/vue.config.js）：**

```javascript
module.exports = defineConfig({
  devServer: {
    port: 8081,
    allowedHosts: 'all',
    proxy: {
      '/api': {
        target: 'http://localhost:8088',
        changeOrigin: true
      }
    }
  }
})
```

### 3.5 什么样的请求会被代理？

**规则：以 `/api` 开头的相对路径请求**

```javascript
// ✅ 会被代理
axios.get('/api/v1/complaints')
  → Dev Server 拦截
  → 转发到 http://localhost:8088/api/v1/complaints

// ✅ 会被代理
request.post('/complaints', data)
  → 内部拼接为 /api/v1/complaints
  → Dev Server 拦截
  → 转发到 http://localhost:8088/api/v1/complaints

// ❌ 不会被代理（绝对路径）
fetch('http://localhost:8088/api/v1/complaints')
  → 直接访问指定地址
  → 触发跨域（从 8080 访问 8088）
```

---

## 4. WebSocket 通信机制

### 4.1 WebSocket 与 HTTP 的区别

| 特性 | HTTP | WebSocket |
|------|------|-----------|
| 连接方式 | 短连接 | 长连接 |
| 通信模式 | 请求-响应 | 全双工 |
| 服务器推送 | ❌ 不支持 | ✅ 支持 |
| 代理支持 | ✅ HTTP 代理 | ⚠️ 需要 WS 代理 |

### 4.2 为什么 WebSocket 不走 HTTP 代理？

**HTTP 代理的工作原理：**

```
HTTP 请求：
1. 客户端发送请求
2. 代理转发请求
3. 后端返回响应
4. 连接关闭 ✓

WebSocket 连接：
1. 客户端发起握手（HTTP Upgrade）
2. 升级为 WebSocket 协议
3. 保持长连接
4. 双向通信...
   ↓
   HTTP 代理不理解 WebSocket 协议
   无法正确转发 ❌
```

**结论：** WebSocket 需要**直接连接后端**，不能走普通的 HTTP 代理。

### 4.3 项目中的 WebSocket 使用

**管理员端 WebSocket（App.vue）：**

```javascript
// 连接管理员控制台 WebSocket
const wsUrl = getWebSocketUrl('/ws/manager/1')
// 结果：ws://localhost:8088/ws/manager/1

const ws = new WebSocket(wsUrl)
ws.onmessage = (event) => {
  // 接收实时通知：新工单、新投诉、新访客
}
```

**业主端 WebSocket（RepairChat.vue）：**

```javascript
// 连接聊天室 WebSocket
const wsUrl = getWebSocketUrl(`/ws/owner/${repairId}`)
// 结果：ws://localhost:8088/ws/owner/123

const ws = new WebSocket(wsUrl)
ws.onmessage = (event) => {
  // 接收聊天消息
}
```

### 4.4 WebSocket 协议适配

**根据 HTTP 协议自动选择 WebSocket 协议：**

```javascript
// utils/request.js
export const getWebSocketUrl = (path) => {
  // http:// → ws://
  // https:// → wss://
  const wsUrl = API_BASE_URL
    .replace('http://', 'ws://')
    .replace('https://', 'wss://')
  
  return `${wsUrl}${path}`
}
```

**示例：**

```javascript
// 本地开发
API_BASE_URL = 'http://localhost:8088'
  ↓
getWebSocketUrl('/ws/manager/1')
  ↓
'ws://localhost:8088/ws/manager/1'

// 生产环境（HTTPS）
API_BASE_URL = 'https://example.com'
  ↓
getWebSocketUrl('/ws/manager/1')
  ↓
'wss://example.com/ws/manager/1'
```

---

## 5. 动态地址适配原理

### 5.1 为什么需要动态地址？

**不同环境的访问地址不同：**

| 环境 | 前端地址 | 后端地址 | 问题 |
|------|---------|---------|------|
| 本地开发 | localhost:8080 | localhost:8088 | 固定地址 ✓ |
| 内网穿透 | continue99.qnway.cc | continue99.qnway.cc:8000 | 域名变化 |
| 生产部署 | example.com | example.com/api | 域名变化 |

**硬编码的问题：**

```javascript
// ❌ 硬编码
const API_URL = 'http://localhost:8088'

问题：
- 本地开发：✓ 正常
- 内网穿透：❌ 无法访问 localhost
- 生产环境：❌ 无法访问 localhost
```

### 5.2 动态地址生成逻辑

**utils/request.js：**

```javascript
// 动态获取 API 基础地址
const getApiBaseUrl = () => {
  // 1. 优先使用环境变量（生产环境）
  if (process.env.VUE_APP_API_BASE_URL) {
    return process.env.VUE_APP_API_BASE_URL
  }
  
  // 2. 根据当前访问地址动态决定
  const hostname = window.location.hostname
  
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    // 本地开发
    return 'http://localhost:8088'
  } else {
    // 内网穿透 / 生产环境
    // 使用当前主机名 + 后端端口
    return `http://${hostname}:8000`
  }
}

export const API_BASE_URL = getApiBaseUrl()
```

### 5.3 动态适配的工作流程

**本地开发：**

```javascript
浏览器访问：http://localhost:8080
  ↓
window.location.hostname = 'localhost'
  ↓
getApiBaseUrl() 返回：'http://localhost:8088'
  ↓
API_BASE_URL = 'http://localhost:8088'
  ↓
图片URL：http://localhost:8088/uploads/xxx.jpg ✓
WebSocket：ws://localhost:8088/ws/... ✓
```

**内网穿透（快解析）：**

```javascript
浏览器访问：http://continue99.qnway.cc
  ↓
window.location.hostname = 'continue99.qnway.cc'
  ↓
getApiBaseUrl() 返回：'http://continue99.qnway.cc:8000'
  ↓
API_BASE_URL = 'http://continue99.qnway.cc:8000'
  ↓
图片URL：http://continue99.qnway.cc:8000/uploads/xxx.jpg ✓
WebSocket：ws://continue99.qnway.cc:8000/ws/... ✓
```

### 5.4 为什么内网穿透不需要修改端口？

**关键点：动态地址自动适配**

```
硬编码方式（需要修改）：
const API_URL = 'http://localhost:8088'
  ↓
切换到内网穿透
  ↓
需要手动改为：'http://continue99.qnway.cc:8000'
  ↓
再切换回本地
  ↓
又要改回：'http://localhost:8088'
  ↓
非常麻烦 ❌

动态适配方式（无需修改）：
const API_URL = getApiBaseUrl()
  ↓
根据 hostname 自动判断
  ↓
本地：'http://localhost:8088'
内网穿透：'http://continue99.qnway.cc:8000'
  ↓
自动切换，无需修改代码 ✓
```

---

## 6. 内网穿透原理

### 6.1 什么是内网穿透？

**问题场景：**

```
你的电脑在内网（局域网）：
├── 内网IP：192.168.1.100
├── 只有同一局域网的设备能访问
└── 外网无法直接访问

目标：
让外网（互联网）的人也能访问你的本地服务
```

**内网穿透原理：**

```
                  互联网                    内网穿透服务器              你的电脑
                    │                          │                       │
1. 用户访问公网域名 │                          │                       │
   http://continue99.qnway.cc                  │                       │
   ├──────────────────────────────────────────→│                       │
                    │                          │                       │
2. 快解析服务器     │                          │ 查找隧道配置          │
   查找对应隧道     │                          │ 80端口 → 本地8080     │
                    │                          │                       │
3. 通过隧道转发     │                          │ 通过已建立的长连接    │
                    │                          ├──────────────────────→│
                    │                          │ 转发到 localhost:8080 │
                    │                          │                       │
4. 你的电脑响应     │                          │     ← 网页数据 ←      │
                    │                          │                       │
5. 返回给用户       │     ← 网页数据 ←         │                       │
                    │                          │                       │
```

### 6.2 快解析的隧道配置

**你的配置：**

| 隧道名称 | 公网端口 | 本地端口 | 协议 | 说明 |
|---------|---------|---------|------|------|
| 管理员前端 | 80 | 8080 | HTTP | Vue DevServer |
| 后端API | 8000 | 8088 | HTTP | FastAPI |
| 业主端前端 | 60034 | 8081 | HTTP | Vue DevServer |

**工作原理：**

```
快解析客户端在你电脑运行：
1. 建立到快解析服务器的长连接
2. 注册3个隧道
3. 等待转发请求

用户访问：http://continue99.qnway.cc
  ↓
快解析服务器：收到请求，端口80
  ↓
查找隧道配置：80 → 本地8080
  ↓
通过长连接转发：请求 → 你的电脑 localhost:8080
  ↓
你的电脑：Vue DevServer 响应
  ↓
快解析服务器：收到响应，返回给用户
```

### 6.3 为什么后端是 8000 而不是 8088？

**快解析的端口映射：**

```
公网访问地址：http://continue99.qnway.cc:8000
  ↓
快解析隧道配置：8000 → 本地8088
  ↓
实际访问：你的电脑 localhost:8088

所以：
- 用户看到：continue99.qnway.cc:8000
- 实际访问：localhost:8088
- 代码需要用：continue99.qnway.cc:8000
```

### 6.4 完整的请求流程

**本地开发环境：**

```
浏览器 http://localhost:8080
  ↓
axios.get('/api/v1/complaints')  (相对路径)
  ↓
Vue DevServer 代理拦截 (/api 前缀)
  ↓
转发到：http://localhost:8088/api/v1/complaints
  ↓
后端响应
```

**内网穿透环境：**

```
浏览器 http://continue99.qnway.cc
  ↓
快解析服务器（80端口）
  ↓
通过隧道转发到：你的电脑 localhost:8080
  ↓
Vue DevServer 收到请求
  ↓
axios.get('/api/v1/complaints')  (相对路径)
  ↓
Vue DevServer 代理拦截 (/api 前缀)
  ↓
转发到：http://localhost:8088/api/v1/complaints
  ↓
后端响应
  ↓
Vue DevServer → 快解析隧道 → 用户浏览器
```

**关键点：**
- ✅ 代理转发在你的电脑上完成（localhost:8080 → localhost:8088）
- ✅ 快解析只负责公网到内网的转发
- ✅ 本地的代理配置无需修改

---

## 7. 本地开发访问方式

### 7.1 启动服务

**步骤1：启动后端**

```bash
# 激活 conda 环境
conda activate property

# 进入后端目录
cd backend

# 启动 FastAPI
uvicorn main:app --host 0.0.0.0 --port 8088 --reload
```

**步骤2：启动管理员前端**

```bash
# 进入管理员前端目录
cd frontend-admin

# 启动开发服务器
npm run serve
```

**步骤3：启动业主端前端**

```bash
# 进入业主端目录
cd frontend-owner

# 启动开发服务器
npm run serve
```

### 7.2 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 管理员端 | http://localhost:8080 | Web 管理界面 |
| 业主端 | http://localhost:8081 | 移动端界面 |
| 后端 API | http://localhost:8088 | 不需要直接访问 |
| API 文档 | http://localhost:8088/docs | Swagger UI |

### 7.3 本地开发的网络流程

```
前端（localhost:8080）
  ↓
axios.get('/api/v1/complaints')
  ↓
webpack-dev-server 代理
  ↓
http://localhost:8088/api/v1/complaints
  ↓
FastAPI 后端
  ↓
MySQL 数据库
```

### 7.4 测试账号

**管理员账号：**
```
用户名：admin
密码：admin123
```

**业主账号：**
```
手机号：13800138000
密码：123456
```

---

## 8. 公网部署访问方式

### 8.1 内网穿透部署（快解析）

**步骤1：启动本地服务**

```bash
# 按照本地开发方式启动所有服务
# 后端、管理员前端、业主端前端
```

**步骤2：启动快解析客户端**

```
1. 打开快解析软件
2. 启动已配置的3个隧道：
   - 管理员前端（80 → 8080）
   - 后端API（8000 → 8088）
   - 业主端（60034 → 8081）
```

**步骤3：访问公网地址**

| 服务 | 公网地址 | 说明 |
|------|---------|------|
| 管理员端 | http://continue99.qnway.cc | 端口80 |
| 后端API | http://continue99.qnway.cc:8000 | 端口8000 |
| 业主端 | http://continue99.qnway.cc:60034 | 端口60034 |

### 8.2 公网访问的网络流程

```
用户浏览器（互联网）
  ↓
http://continue99.qnway.cc
  ↓
快解析服务器（公网）
  ↓
通过隧道转发（80 → 8080）
  ↓
你的电脑 localhost:8080
  ↓
Vue DevServer
  ↓
axios.get('/api/v1/complaints')
  ↓
webpack-dev-server 代理（/api → 8088）
  ↓
localhost:8088
  ↓
FastAPI 后端
```

### 8.3 关闭公网访问

**方法1：停止隧道（保留配置）**

```
在快解析客户端：
点击每个隧道的"停止"按钮
```

**方法2：关闭快解析**

```
关闭快解析软件
所有隧道自动停止
```

**方法3：删除隧道（永久删除）**

```
右键点击隧道 → 删除
```

---

## 9. 常见问题解答

### Q1: 为什么有些请求用 axios，有些用 fetch？

**A:** 历史遗留问题，我们已经统一改为 axios。

```javascript
// ❌ 旧代码（fetch + 绝对路径）
fetch('http://localhost:8088/api/v1/complaints')

// ✅ 新代码（axios + 相对路径）
request.get('/complaints')  // 会被代理
```

**原因：**
- fetch 使用绝对路径 → 直接访问指定地址 → 跨域 ❌
- axios 使用相对路径 → 走代理 → 不跨域 ✓

---

### Q2: 为什么图片 URL 需要拼接 API_BASE_URL？

**A:** 图片是静态资源，不能走代理。

```javascript
// 后端返回相对路径
/uploads/images/xxx.jpg

// 需要拼接完整 URL
http://localhost:8088/uploads/images/xxx.jpg  (本地)
http://continue99.qnway.cc:8000/uploads/images/xxx.jpg  (公网)

// 动态拼接
`${API_BASE_URL}/uploads/images/xxx.jpg`
```

**原因：**
- 图片通过 `<img src="...">` 加载
- 不是 axios 请求，不走代理
- 需要完整的 URL

---

### Q3: 为什么 WebSocket 连接会失败？

**A:** 免费版快解析的 HTTP 隧道可能不支持 WebSocket。

**解决方案：**

1. **暂时接受（推荐）：**
   - WebSocket 只影响实时通知
   - 基本功能完全正常
   - 手动刷新页面即可

2. **使用支持 WebSocket 的内网穿透工具：**
   - ngrok
   - frp
   - 付费版快解析

---

### Q4: 为什么本地访问正常，公网访问报错？

**A:** 检查以下几点：

1. **是否清除浏览器缓存？**
   ```
   按 Ctrl + Shift + Delete
   或 Ctrl + F5 硬刷新
   ```

2. **快解析隧道是否启动？**
   ```
   在快解析客户端查看隧道状态
   应该显示"运行中"
   ```

3. **端口配置是否正确？**
   ```
   管理员端：80 → 8080
   后端：8000 → 8088
   业主端：60034 → 8081
   ```

4. **vue.config.js 是否配置 allowedHosts？**
   ```javascript
   allowedHosts: 'all'
   ```

---

### Q5: 为什么修改了代码还是不生效？

**A:** 浏览器缓存或模块缓存问题。

**解决方法：**

1. **重启开发服务器：**
   ```bash
   Ctrl + C  (停止)
   npm run serve  (重启)
   ```

2. **清除浏览器缓存：**
   ```
   Ctrl + F5 硬刷新
   ```

3. **关闭所有浏览器标签，重新打开**

---

### Q6: 为什么连接手机热点后本地访问还能正常？

**A:** localhost 是本地回环地址，不依赖网络。

```
localhost = 127.0.0.1
    ↓
操作系统内部的虚拟网络接口
    ↓
不需要任何外部网络连接
    ↓
无论网络状态如何，localhost 永远可用
```

**网络状态 vs localhost：**

| 网络状态 | localhost 是否可用 |
|---------|-------------------|
| 有线网络 | ✓ 可用 |
| WiFi | ✓ 可用 |
| 手机热点 | ✓ 可用 |
| 完全断网 | ✓ 可用 |
| 飞行模式 | ✓ 可用 |

---

### Q7: 生产环境如何部署？

**A:** 生产环境需要不同的配置。

**推荐方案：**

```
云服务器 + Nginx + Docker

架构：
用户浏览器
  ↓
Nginx (80/443端口)
  ├─→ /api → FastAPI 后端（Docker 容器）
  ├─→ / → 前端静态文件
  └─→ /ws → WebSocket 连接

优点：
- ✓ 稳定性高
- ✓ 支持 HTTPS
- ✓ 支持 WebSocket
- ✓ 可以配置域名
```

**配置示例（Nginx）：**

```nginx
server {
    listen 80;
    server_name example.com;

    # 前端静态文件
    location / {
        root /var/www/frontend;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://127.0.0.1:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://127.0.0.1:8088;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 总结

### 核心概念

1. **代理转发：** 解决跨域问题，只对相对路径有效
2. **动态地址：** 自动适配不同环境，无需修改代码
3. **混合通信：** HTTP API 走代理，WebSocket 直连
4. **内网穿透：** 通过中间服务器将内网服务暴露到公网

### 关键配置文件

```
├── frontend-admin/
│   ├── vue.config.js          # 代理配置、端口配置
│   └── src/utils/request.js   # 动态地址生成
│
├── frontend-owner/
│   ├── vue.config.js          # 代理配置、端口配置
│   └── src/utils/request.js   # 动态地址生成
│
└── backend/
    └── main.py                # FastAPI 配置
```

### 最佳实践

1. ✅ 使用相对路径 + axios（走代理）
2. ✅ 使用动态地址适配（自动切换环境）
3. ✅ 图片 URL 拼接 API_BASE_URL
4. ✅ WebSocket 直连（不走代理）
5. ❌ 避免使用绝对路径 + fetch（跨域）
6. ❌ 避免硬编码地址（环境不灵活）

---

## 附录：完整的网络架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                          本地开发环境                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  浏览器 (localhost:8080)                                          │
│    │                                                              │
│    ├─ HTTP API (/api/v1/complaints)                              │
│    │    ↓                                                         │
│    │  Vue DevServer Proxy                                        │
│    │    ↓                                                         │
│    │  localhost:8088 (FastAPI)                                   │
│    │                                                              │
│    ├─ 图片 (http://localhost:8088/uploads/xxx.jpg)               │
│    │    ↓                                                         │
│    │  直接访问 localhost:8088                                     │
│    │                                                              │
│    └─ WebSocket (ws://localhost:8088/ws/...)                     │
│         ↓                                                         │
│       直接连接 localhost:8088                                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       内网穿透部署环境                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  用户浏览器 (continue99.qnway.cc)                                 │
│    │                                                              │
│    ↓                                                              │
│  快解析服务器 (公网)                                              │
│    │                                                              │
│    ├─ 80端口 → 隧道 → 你的电脑 localhost:8080                     │
│    ├─ 8000端口 → 隧道 → 你的电脑 localhost:8088                   │
│    └─ 60034端口 → 隧道 → 你的电脑 localhost:8081                  │
│                                                                   │
│  你的电脑：                                                        │
│    │                                                              │
│    ├─ localhost:8080 (Vue DevServer)                             │
│    │    │                                                         │
│    │    ├─ HTTP API → Proxy → localhost:8088                     │
│    │    ├─ 图片 → http://continue99.qnway.cc:8000/uploads/...   │
│    │    └─ WebSocket → ws://continue99.qnway.cc:8000/ws/...     │
│    │                                                              │
│    └─ localhost:8088 (FastAPI)                                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

**文档版本：** v1.0  
**最后更新：** 2024  
**维护者：** 开发团队
