# 智慧物业管理系统

基于 FastAPI + Vue3 的智慧物业管理平台，支持管理员端、业主端、维修人员端三端协同，集成 AI 智能助手与 PWA 离线能力。

## 功能特性

- **三端协同**：管理员端（PC）、业主端（移动端 PWA）、维修人员端（移动端）
- **AI 智能助手**：基于 DeepSeek R1 + Function Calling，支持自然语言交互
- **实时通信**：WebSocket 推送，工单状态实时同步
- **PWA 支持**：离线访问、添加到主屏幕
- **电子发票**：账单支付、PDF 发票生成与二维码验证

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + Python 3.11 + Tortoise ORM |
| 数据库 | MySQL 8.0 |
| 前端（管理端）| Vue 3 + Element Plus |
| 前端（移动端）| Vue 3 + Vant + PWA |
| AI 模型 | DeepSeek R1 |
| 部署 | Nginx + Uvicorn |

## 环境要求

- Python 3.11+
- Node.js 18+
- MySQL 8.0+

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Continue-ff7/Property_Management_-System.git
或者 git@github.com:Continue-ff7/Property_Management_-System.git
cd property-management-system
```

### 2. 配置数据库

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE property_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 后端部署

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（详见下方环境变量说明）
# 在 backend 目录下创建 .env 文件，填写数据库密码和密钥

# 创建默认管理员账号
python init_admin.py

# 启动服务（Windows 直接运行启动脚本）
start.bat

# 或手动启动
uvicorn main:app --reload --host 0.0.0.0 --port 8088
```

后端启动后访问：http://localhost:8088/docs （API 文档）

> **数据库初始化说明**：本项目使用 Tortoise ORM，数据库表结构会在后端启动时通过 `Tortoise.generate_schemas()` 自动创建，无需手动执行初始化脚本。

### 4. 前端部署

#### 管理员端

```bash
cd frontend-admin
npm install
npm run serve
```

访问：http://localhost:8080

#### 业主端 / 维修人员端

```bash
cd frontend-owner
npm install
npm run serve
```

访问：http://localhost:8081

### 5. 默认账号

运行 `python init_admin.py` 后生成：

- 管理员：`admin` / `admin123`

## 环境变量配置

### 后端环境变量（backend/.env）

在 `backend` 目录下创建 `.env` 文件：

```env
# ========== 数据库配置（必填） ==========
# MySQL 连接地址，格式：mysql://用户名:密码@主机:端口/数据库名
DATABASE_URL=mysql://root:你的密码@localhost:3306/property_management

# ========== JWT 安全配置（必填） ==========
# 随机密钥，用于 Token 签名，建议生成长度不低于 32 位的随机字符串
SECRET_KEY=your-secret-key-here

# Token 过期时间（分钟），默认 7 天
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# ========== 跨域配置（必填） ==========
# 前端直接请求后端 8088 端口，必须配置跨域允许前端地址
# 本地开发保持默认即可，生产环境修改为实际域名
CORS_ORIGINS=http://localhost:8080,http://localhost:8081,http://localhost:8082

# ========== 文件上传配置 ==========
# 上传文件保存路径，默认 uploads
UPLOAD_DIR=uploads

# 最大上传文件大小（字节），默认 10MB
MAX_UPLOAD_SIZE=10485760

# ========== 后端服务地址（可选） ==========
# 用于生成发票二维码中的验证 URL，生产环境配置域名
BACKEND_HOST=localhost:8088

```

### 前端业主端环境变量（frontend-owner/.env.development）

在 `frontend-owner` 目录下创建 `.env.development` 文件：

# DeepSeek API Key（必填，AI 助手功能需要）
# 从 https://platform.deepseek.com 注册获取
VUE_APP_DEEPSEEK_API_KEY=sk-your-deepseek-api-key
```

## 项目结构

```
property-management-system/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/               # API 路由
│   │   ├── core/              # 核心配置、安全、依赖
│   │   ├── models/            # 数据库模型
│   │   └── schemas/           # Pydantic 模型
│   ├── uploads/               # 上传文件目录
│   ├── main.py                # 入口文件
│   ├── requirements.txt       # Python 依赖
│   └── .env                   # 环境变量（自行创建，不上传）
├── frontend-admin/            # 管理员端（Vue3 PC端）
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env.development       # 环境变量（改环境变量可忽略）
├── frontend-owner/            # 业主端/维修人员端（Vue3 移动端 + PWA）
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env.development       # 环境变量（自行创建，不上传）
└── README.md
```

## 常见问题

### 1. 前端启动后无法连接后端

本项目前端直接请求后端 `http://localhost:8088`，依赖后端 CORS 配置。若出现跨域错误，请检查：

1. 后端 `.env` 中的 `CORS_ORIGINS` 是否包含前端地址
2. 后端服务是否正常运行
3. 防火墙是否放行 8088 端口

### 2. AI 助手无法使用

确认 `frontend-owner/.env.development` 中已正确配置 `VUE_APP_DEEPSEEK_API_KEY`，并重新启动前端服务。

### 3. 图片上传后无法显示

检查 `backend/.env` 中的 `UPLOAD_DIR` 配置，确保目录存在且有写入权限。


## 开源协议

MIT License
