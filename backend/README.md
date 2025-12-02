# 物业管理系统后端API

基于 FastAPI + TortoisORM + MySQL 的物业管理系统后端API。

## 功能特性

### 三个用户端
1. **业主端**
   - 查看个人和房产信息
   - 查看缴费记录和账单
   - 在线支付物业费用
   - 下载缴费发票
   - 提交报修申请（含图片上传、紧急程度选择）
   - 查看报修进度和维修人员信息
   - 对完成的维修进行评价
   - 查看小区公告
   - AI客服对话咨询

2. **物业管理端**
   - 管理业主信息（增删改查）
   - 生成和发送缴费账单
   - 设置收费标准
   - 批量生成账单
   - 处理报修工单（派单、分配维修人员、更新进度）
   - 发布和管理小区公告
   - 查看预警信息
   - 数据统计报表（收入、维修、业主统计）
   - 管理维修人员信息

3. **维修人员端**
   - 查看分配的维修工单
   - 更新维修进度（开始维修、完成维修）
   - 上传维修现场照片
   - 查看业主联系方式（仅限当前工单）
   - 个人工作统计

## 技术栈

- FastAPI - 现代高性能Web框架
- TortoisORM - 异步ORM
- MySQL - 数据库
- JWT - 身份认证
- Pydantic - 数据验证
- ReportLab - PDF发票生成

## 安装部署

### 1. 环境要求
- Python 3.8+
- MySQL 5.7+

### 2. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置环境变量
复制 `.env.example` 为 `.env` 并修改配置：
```bash
cp .env.example .env
```

修改 `.env` 文件中的数据库连接和其他配置。

### 4. 创建数据库
```sql
CREATE DATABASE property_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. 运行服务
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务将在 http://localhost:8000 启动。

### 6. 访问API文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API路由结构

### 认证路由 `/api/v1/auth`
- `POST /login` - 用户登录

### 公共路由 `/api/v1/common`
- `POST /upload` - 上传文件
- `GET /announcements` - 获取公告列表
- `GET /announcements/{id}` - 获取公告详情

### 业主端路由 `/api/v1/owner`
- `GET /profile` - 获取个人信息
- `GET /properties` - 获取房产信息
- `GET /bills` - 获取账单列表
- `POST /bills/{id}/pay` - 支付账单
- `GET /bills/{id}/invoice` - 下载发票
- `POST /repairs` - 提交报修
- `GET /repairs` - 查看报修列表
- `POST /repairs/{id}/evaluate` - 评价维修
- `POST /chat` - AI客服对话

### 物业管理端路由 `/api/v1/manager`
- **业主管理**
  - `GET /owners` - 业主列表
  - `POST /owners` - 创建业主
  - `PUT /owners/{id}` - 更新业主
  - `DELETE /owners/{id}` - 注销业主
  - `GET /owners/{id}/properties` - 查看业主房产

- **房产管理**
  - `GET /buildings` - 楼栋列表
  - `POST /buildings` - 创建楼栋
  - `GET /properties` - 房产列表
  - `POST /properties` - 创建房产

- **账单管理**
  - `GET /fee-standards` - 收费标准列表
  - `POST /fee-standards` - 创建收费标准
  - `PUT /fee-standards/{id}` - 更新收费标准
  - `POST /bills` - 生成账单
  - `POST /bills/batch` - 批量生成账单
  - `GET /bills` - 查看所有账单

- **报修管理**
  - `GET /repairs` - 查看所有工单
  - `POST /repairs/{id}/assign` - 分配工单
  - `PUT /repairs/{id}` - 更新工单状态

- **维修人员管理**
  - `GET /maintenance-workers` - 维修人员列表
  - `POST /maintenance-workers` - 创建维修人员
  - `PUT /maintenance-workers/{id}` - 更新维修人员
  - `DELETE /maintenance-workers/{id}` - 停用维修人员

- **公告管理**
  - `POST /announcements` - 发布公告
  - `GET /announcements` - 公告列表
  - `PUT /announcements/{id}` - 更新公告
  - `DELETE /announcements/{id}` - 删除公告

- **统计报表**
  - `GET /statistics/revenue` - 收入统计
  - `GET /statistics/repairs` - 维修统计
  - `GET /statistics/owners` - 业主统计
  - `GET /alerts` - 预警信息

### 维修人员端路由 `/api/v1/maintenance`
- `GET /profile` - 获取个人信息
- `GET /orders` - 查看分配的工单
- `GET /orders/{id}` - 查看工单详情
- `POST /orders/{id}/start` - 开始维修
- `POST /orders/{id}/complete` - 完成维修
- `POST /orders/{id}/upload-image` - 上传维修照片
- `GET /statistics` - 个人工作统计

## 数据库表结构

- `users` - 用户表（业主、物业管理员、维修人员）
- `buildings` - 楼栋表
- `properties` - 房产表
- `bills` - 账单表
- `repair_orders` - 报修工单表
- `announcements` - 公告表
- `fee_standards` - 收费标准表
- `chat_messages` - AI客服聊天记录表

## 权限说明

系统使用JWT进行身份认证，根据用户角色（owner/manager/maintenance）控制访问权限。

## 开发说明

### 项目结构
```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py          # 认证路由
│   │       ├── common.py        # 公共路由
│   │       ├── owner.py         # 业主端路由
│   │       ├── property_manager.py  # 物业管理端路由
│   │       └── maintenance.py   # 维修人员端路由
│   ├── core/
│   │   ├── config.py           # 配置
│   │   ├── security.py         # 安全相关
│   │   └── dependencies.py     # 依赖项
│   ├── models/
│   │   └── __init__.py         # 数据库模型
│   └── schemas/
│       └── __init__.py         # Pydantic模型
├── uploads/                    # 上传文件目录
├── main.py                     # 应用入口
├── requirements.txt            # 依赖包
└── .env.example               # 环境变量示例
```

## 注意事项

1. 生产环境务必修改 SECRET_KEY
2. 配置合适的CORS策略
3. 定期备份数据库
4. 上传文件建议使用对象存储服务
5. AI客服功能需要集成第三方AI服务

## License

MIT
