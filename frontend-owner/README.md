# 物业管理系统 - 业主移动端

基于 Vue 3 + Vant UI 的物业管理系统业主端移动应用

## 功能特性

✅ 已实现的功能：

1. **用户认证**
   - 业主登录
   - 自动Token管理

2. **个人信息**
   - 查看业主信息
   - 查看房产列表（楼栋、单元、房号、面积）

3. **账单管理**
   - 查看缴费记录
   - 按状态筛选（全部/未支付/已支付）
   - 在线支付物业费用（支付宝/微信支付）
   - 账单详情展示

4. **报修管理**
   - 提交报修申请（问题描述、图片上传、紧急程度）
   - 查看报修进度
   - 查看维修人员信息
   - 对完成的维修进行评价（星级+文字）

5. **公告通知**
   - 查看小区公告和通知
   - 公告详情

6. **UI设计**
   - 基于参考图片的蓝紫色渐变风格
   - 移动端友好的操作界面
   - 底部Tab导航（首页/账单/报修/我的）

⏸️ 暂缓功能：
- 下载个人缴费发票
- 与AI客服进行对话咨询

## 技术栈

- **前端框架**：Vue 3 (Composition API)
- **UI组件库**：Vant 4.x
- **路由管理**：Vue Router 4
- **状态管理**：Vuex 4
- **HTTP客户端**：Axios
- **构建工具**：Vue CLI 5

## 目录结构

```
frontend-owner/
├── public/               # 静态资源
├── src/
│   ├── api/             # API接口封装
│   │   └── index.js     # 所有API定义
│   ├── layout/          # 布局组件
│   │   └── Index.vue    # 主布局（含底部Tab）
│   ├── router/          # 路由配置
│   │   └── index.js
│   ├── store/           # Vuex状态管理
│   │   └── index.js
│   ├── utils/           # 工具函数
│   │   └── request.js   # Axios封装
│   ├── views/           # 页面组件
│   │   ├── Login.vue              # 登录页
│   │   ├── Home.vue               # 首页
│   │   ├── Bills.vue              # 账单列表
│   │   ├── Repairs.vue            # 报修列表
│   │   ├── RepairCreate.vue       # 提交报修
│   │   ├── Announcements.vue      # 公告列表
│   │   └── Profile.vue            # 个人中心
│   ├── App.vue
│   └── main.js
├── vue.config.js        # Vue CLI配置
├── package.json
└── start.bat           # Windows启动脚本
```

## 快速开始

### 1. 安装依赖

```bash
cd frontend-owner
npm install --legacy-peer-deps
```

### 2. 配置后端地址

后端API默认地址：`http://localhost:8088`

如需修改，编辑 `vue.config.js`：

```javascript
devServer: {
  port: 8081,
  proxy: {
    '/api': {
      target: 'http://localhost:8088',  // 修改为你的后端地址
      changeOrigin: true
    }
  }
}
```

### 3. 启动开发服务器

**方式1：使用npm命令**
```bash
npm run serve
```

**方式2：使用启动脚本（Windows）**
```bash
start.bat
```

应用将运行在：`http://localhost:8081`（如果端口被占用会自动切换）

### 4. 启动后端服务

确保后端服务已启动并运行在 8088 端口：

```bash
cd ../backend
python main.py
```

## API接口说明

### 业主端API（/api/v1/owner）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/profile` | GET | 获取个人信息 |
| `/properties` | GET | 获取我的房产 |
| `/bills` | GET | 获取账单列表 |
| `/bills/{id}/pay` | POST | 支付账单 |
| `/repairs` | GET | 获取报修列表 |
| `/repairs` | POST | 提交报修 |
| `/repairs/{id}/evaluate` | POST | 评价维修 |

### 公共API（/api/v1/common）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/announcements` | GET | 获取公告列表 |
| `/upload` | POST | 上传文件 |

### 认证API（/api/v1/auth）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/login` | POST | 用户登录 |

## 构建生产版本

```bash
npm run build
```

构建产物位于 `dist/` 目录

## 常见问题

### 1. 端口冲突
如果默认端口8081被占用，修改 `vue.config.js` 中的 `port` 配置

### 2. 代理错误
确保后端服务已启动，检查 `vue.config.js` 中的代理配置是否正确

### 3. 依赖安装失败
使用 `npm install --legacy-peer-deps` 解决版本冲突

## 开发说明

- 使用Vue 3 Composition API（setup语法）
- 所有API调用已添加Token认证
- 图片上传支持最多3张
- 支持下拉刷新和上拉加载
- 自动处理401登录过期

## 与PWA打包

后续可将此移动端通过PWA技术打包为独立应用，供业主在手机上安装使用。

## 相关项目

- **后端API**: `../backend`
- **管理员Web端**: `../frontend-admin`
- **维修人员移动端**: 待开发

## License

MIT
