# 智慧物业管理系统 - 部署方案

## 一、系统架构说明

本系统包含以下组件：
- **后端服务**：FastAPI (Python) - 端口 8088
- **管理员端前端**：Vue 3 PC端 - 端口 8080
- **业主/维修人员端前端**：Vue 3 移动端 - 端口 8081
- **数据库**：MySQL

通信方式：
- **HTTP API**：传统接口调用（需要 `/api/v1` 前缀）
- **WebSocket**：实时通信（不需要前缀）
- **静态资源**：图片直接访问后端

---

## 二、部署架构方案

### 推荐架构：Nginx 反向代理 + 单域名多路径

```
用户访问
   ↓
域名：yourdomain.com
   ↓
Nginx (80/443端口)
   ├─ /admin/        → 管理员端前端 (8080)
   ├─ /mobile/       → 业主端前端 (8081)
   ├─ /api/          → 后端API (8088)
   ├─ /ws/           → WebSocket (8088)
   └─ /uploads/      → 静态资源 (8088)
```

**优势**：
- ✅ 只需要一个域名和IP
- ✅ 自动处理跨域问题
- ✅ 支持 HTTPS 加密
- ✅ 便于移动端访问

---

## 三、服务器准备

### 3.1 服务器要求

- **CPU**：2核及以上
- **内存**：2GB及以上
- **硬盘**：20GB及以上
- **系统**：Ubuntu 20.04 / CentOS 7+ / Windows Server

### 3.2 安装必要软件

#### Ubuntu/CentOS
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y  # Ubuntu
# sudo yum update -y  # CentOS

# 安装 Python 3.9+
sudo apt install python3.9 python3.9-venv python3-pip -y

# 安装 MySQL
sudo apt install mysql-server -y

# 安装 Nginx
sudo apt install nginx -y

# 安装 Node.js 16+
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install nodejs -y
```

#### Windows Server
1. 安装 Python 3.9+：https://www.python.org/downloads/
2. 安装 MySQL：https://dev.mysql.com/downloads/installer/
3. 安装 Nginx：http://nginx.org/en/download.html
4. 安装 Node.js：https://nodejs.org/

---

## 四、后端部署

### 4.1 上传代码

```bash
# 创建部署目录
mkdir -p /opt/property-system
cd /opt/property-system

# 上传 backend 文件夹到服务器
# 使用 FTP/SCP 工具上传，或使用 Git
git clone <你的仓库地址> .
```

### 4.2 配置数据库

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE property_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 创建用户
CREATE USER 'property_user'@'localhost' IDENTIFIED BY '你的密码';
GRANT ALL PRIVILEGES ON property_management.* TO 'property_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4.3 配置后端环境

```bash
cd /opt/property-system/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 修改 .env 配置文件
nano .env
```

**.env 配置示例**：
```env
# 数据库配置
DATABASE_URL=mysql://property_user:你的密码@localhost:3306/property_management

# JWT密钥（随机生成一个复杂字符串）
SECRET_KEY=your-secret-key-change-this-in-production

# 跨域配置（生产环境配置你的域名）
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# 文件上传路径
UPLOAD_DIR=./uploads
```

### 4.4 初始化数据库

```bash
# 执行数据库初始化脚本
python init_db.py

# 添加维修工单新状态（如果需要）
python add_new_repair_statuses.py
```

### 4.5 使用 Supervisor 管理后端服务

#### 安装 Supervisor
```bash
sudo apt install supervisor -y
```

#### 创建配置文件
```bash
sudo nano /etc/supervisor/conf.d/property-backend.conf
```

**配置内容**：
```ini
[program:property-backend]
command=/opt/property-system/backend/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8088 --workers 2
directory=/opt/property-system/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/property-backend.log
```

#### 启动服务
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start property-backend

# 查看状态
sudo supervisorctl status property-backend
```

---

## 五、前端部署

### 5.1 构建前端项目

#### 管理员端
```bash
cd /opt/property-system/frontend-admin

# 安装依赖
npm install

# 修改生产环境配置
nano .env.production
```

**.env.production**：
```env
VUE_APP_API_BASE_URL=/api/v1
VUE_APP_WS_BASE_URL=wss://yourdomain.com
```

```bash
# 构建生产版本
npm run build

# 构建完成后，dist 文件夹就是部署文件
```

#### 业主/维修人员端
```bash
cd /opt/property-system/frontend-owner

# 安装依赖
npm install

# 修改生产环境配置
nano .env.production
```

**.env.production**：
```env
VUE_APP_API_BASE_URL=/api/v1
VUE_APP_WS_BASE_URL=wss://yourdomain.com
```

```bash
# 构建生产版本
npm run build
```

### 5.2 部署前端文件

```bash
# 创建前端部署目录
sudo mkdir -p /var/www/property-system/admin
sudo mkdir -p /var/www/property-system/mobile

# 复制构建文件
sudo cp -r /opt/property-system/frontend-admin/dist/* /var/www/property-system/admin/
sudo cp -r /opt/property-system/frontend-owner/dist/* /var/www/property-system/mobile/

# 设置权限
sudo chown -R www-data:www-data /var/www/property-system
sudo chmod -R 755 /var/www/property-system
```

---

## 六、Nginx 配置

### 6.1 创建 Nginx 配置文件

```bash
sudo nano /etc/nginx/sites-available/property-system
```

### 6.2 配置内容

```nginx
# HTTP 强制跳转 HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS 主配置
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL 证书配置（后面申请）
    ssl_certificate /etc/nginx/ssl/yourdomain.com.crt;
    ssl_certificate_key /etc/nginx/ssl/yourdomain.com.key;

    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 日志配置
    access_log /var/log/nginx/property-access.log;
    error_log /var/log/nginx/property-error.log;

    # 管理员端前端（PC端）
    location /admin {
        alias /var/www/property-system/admin;
        try_files $uri $uri/ /admin/index.html;
        index index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 7d;
            add_header Cache-Control "public, immutable";
        }
    }

    # 业主/维修人员端前端（移动端）
    location /mobile {
        alias /var/www/property-system/mobile;
        try_files $uri $uri/ /mobile/index.html;
        index index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 7d;
            add_header Cache-Control "public, immutable";
        }
    }

    # 后端 API（HTTP）
    location /api/ {
        proxy_pass http://127.0.0.1:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 允许跨域（如果需要）
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }

    # WebSocket 连接
    location /ws/ {
        proxy_pass http://127.0.0.1:8088;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 超时配置
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }

    # 静态资源（上传的图片等）
    location /uploads/ {
        proxy_pass http://127.0.0.1:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # 图片缓存
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 首页重定向到管理员端
    location = / {
        return 301 /admin/;
    }
}
```

### 6.3 启用配置

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/property-system /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

---

## 七、SSL 证书配置（HTTPS）

### 7.1 使用 Let's Encrypt 免费证书

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 申请证书（自动配置 Nginx）
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 证书会自动续期，测试续期
sudo certbot renew --dry-run
```

### 7.2 或使用云服务商证书

如果使用阿里云、腾讯云等，可以在控制台申请免费证书，然后：

```bash
# 创建证书目录
sudo mkdir -p /etc/nginx/ssl

# 上传证书文件到服务器
# yourdomain.com.crt - 证书文件
# yourdomain.com.key - 私钥文件

# 设置权限
sudo chmod 600 /etc/nginx/ssl/yourdomain.com.key
```

---

## 八、域名配置

### 8.1 DNS 解析

在域名服务商（如阿里云、腾讯云）添加 A 记录：

| 主机记录 | 记录类型 | 记录值 |
|---------|---------|--------|
| @ | A | 你的服务器IP |
| www | A | 你的服务器IP |

### 8.2 访问地址

配置完成后，访问地址为：
- **管理员端**：https://yourdomain.com/admin
- **业主端**：https://yourdomain.com/mobile
- **维修人员端**：https://yourdomain.com/mobile （登录后自动区分）

---

## 九、防火墙配置

### 9.1 开放必要端口

```bash
# Ubuntu (UFW)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH（确保开启，否则断开连接）
sudo ufw enable

# CentOS (Firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

### 9.2 云服务器安全组

如果使用阿里云、腾讯云等，在控制台的安全组规则中添加：
- **80** (HTTP)
- **443** (HTTPS)
- **22** (SSH)

---

## 十、移动端配置说明

### 10.1 前端代码调整

确保前端的 `utils/request.js` 使用相对路径：

```javascript
// frontend-owner/src/utils/request.js
const service = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || '/api/v1',  // 使用相对路径
  timeout: 30000
})

// WebSocket 地址
export const getWebSocketUrl = (path) => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  return `${protocol}//${host}${path}`  // 自动适配当前域名
}
```

### 10.2 移动端访问方式

#### 方式1：浏览器直接访问（推荐）
- 手机浏览器打开：`https://yourdomain.com/mobile`
- 可以添加到桌面，体验类似原生APP

#### 方式2：微信小程序（可选）
- 如果需要，可以将移动端封装为微信小程序
- 需要在微信公众平台配置域名白名单

#### 方式3：打包成 APP（可选）
使用 Cordova 或 UniApp 打包成安卓/iOS APP

---

## 十一、日常维护

### 11.1 查看日志

```bash
# 后端日志
sudo tail -f /var/log/property-backend.log

# Nginx 访问日志
sudo tail -f /var/log/nginx/property-access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/property-error.log

# Supervisor 日志
sudo supervisorctl tail -f property-backend
```

### 11.2 重启服务

```bash
# 重启后端
sudo supervisorctl restart property-backend

# 重启 Nginx
sudo systemctl restart nginx

# 重启 MySQL
sudo systemctl restart mysql
```

### 11.3 更新代码

```bash
# 拉取最新代码
cd /opt/property-system
git pull

# 重新构建前端
cd frontend-admin
npm run build
sudo cp -r dist/* /var/www/property-system/admin/

cd ../frontend-owner
npm run build
sudo cp -r dist/* /var/www/property-system/mobile/

# 重启后端
cd ../backend
source venv/bin/activate
pip install -r requirements.txt  # 如果有新依赖
sudo supervisorctl restart property-backend
```

### 11.4 数据库备份

```bash
# 创建备份脚本
sudo nano /opt/backup-db.sh
```

**backup-db.sh**：
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u property_user -p你的密码 property_management > /opt/backups/property_$DATE.sql
# 删除30天前的备份
find /opt/backups -name "property_*.sql" -mtime +30 -delete
```

```bash
# 设置权限
sudo chmod +x /opt/backup-db.sh

# 添加定时任务（每天凌晨3点备份）
sudo crontab -e
# 添加: 0 3 * * * /opt/backup-db.sh
```

---

## 十二、故障排查

### 问题1：无法访问网站

**检查步骤**：
```bash
# 1. 检查 Nginx 是否运行
sudo systemctl status nginx

# 2. 检查后端是否运行
sudo supervisorctl status property-backend

# 3. 检查端口是否监听
sudo netstat -tlnp | grep 8088
sudo netstat -tlnp | grep 80

# 4. 检查防火墙
sudo ufw status
```

### 问题2：WebSocket 连接失败

**检查步骤**：
1. 确认 Nginx 配置中 `/ws/` 路径正确
2. 检查后端日志是否有 WebSocket 连接记录
3. 确认浏览器控制台没有跨域错误
4. 如果使用 HTTPS，WebSocket 必须用 WSS

### 问题3：图片无法显示

**检查步骤**：
1. 确认 `/uploads/` 路径在 Nginx 配置中正确
2. 检查后端 uploads 目录权限
3. 确认图片上传后路径正确保存到数据库

### 问题4：跨域错误

**解决方案**：
- 确保使用 Nginx 反向代理，前后端同域名
- 检查 `.env` 中 CORS_ORIGINS 配置
- 确认前端使用相对路径而非绝对路径

---

## 十三、性能优化建议

### 13.1 数据库优化

```sql
-- 添加索引
ALTER TABLE repair_orders ADD INDEX idx_status (status);
ALTER TABLE repair_orders ADD INDEX idx_owner_id (owner_id);
ALTER TABLE bills ADD INDEX idx_status (status);
```

### 13.2 Nginx 优化

```nginx
# 在 http 块中添加
gzip on;
gzip_vary on;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

# 连接优化
keepalive_timeout 65;
client_max_body_size 20M;  # 文件上传大小限制
```

### 13.3 后端优化

```bash
# 增加 workers 数量
# 在 supervisor 配置中修改
command=... --workers 4  # 根据CPU核心数调整
```

---

## 十四、安全建议

1. **定期更新系统和软件包**
2. **使用强密码**（数据库、服务器）
3. **启用 SSH 密钥登录**，禁用密码登录
4. **配置 fail2ban** 防止暴力破解
5. **定期备份数据库**
6. **监控日志**，及时发现异常访问

---

## 附录：快速部署脚本

```bash
#!/bin/bash
# 快速部署脚本（请根据实际情况修改）

echo "开始部署智慧物业系统..."

# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 安装必要软件
sudo apt install python3.9 python3-pip mysql-server nginx supervisor nodejs npm -y

# 3. 创建目录
sudo mkdir -p /opt/property-system
sudo mkdir -p /var/www/property-system/{admin,mobile}

# 4. 配置数据库（需要手动设置密码）
echo "请手动配置数据库..."

# 5. 部署后端
cd /opt/property-system/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python init_db.py

# 6. 构建前端
cd /opt/property-system/frontend-admin
npm install && npm run build
sudo cp -r dist/* /var/www/property-system/admin/

cd /opt/property-system/frontend-owner
npm install && npm run build
sudo cp -r dist/* /var/www/property-system/mobile/

# 7. 配置服务
# （复制上面的配置文件）

echo "部署完成！请配置 Nginx 和 SSL 证书。"
```

---

## 联系支持

如有问题，请查看：
- 后端日志：`/var/log/property-backend.log`
- Nginx日志：`/var/log/nginx/property-error.log`
- 系统日志：`journalctl -u nginx -f`
