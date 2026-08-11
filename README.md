# ddWallpaper 项目

> 多点壁纸 —— HarmonyOS 壁纸平台（PC 官网 + FastAPI 后端）

## 项目结构

| 目录 | 说明 |
|------|------|
| `backend/` | FastAPI 后端（REST API + Web 管理后台） |
| `website/` | PC 官网前端（PHP 单页，部署于 pc.ddbz.art） |
| `docs/` | 源码与配置说明 |

## 部署总览

本项目分为两部分，可独立部署：

1. **后端** (`backend/`)：Docker Compose 一键启动 MySQL + FastAPI
2. **PC 官网** (`website/`)：PHP 站点，需 PHP 8.1+ + Nginx/Apache

---

# 🚀 后端部署（FastAPI + MySQL）

## 前置要求

- [Docker](https://docs.docker.com/get-docker/) 与 [Docker Compose](https://docs.docker.com/compose/install/)
- 或 Python 3.11+（本地开发模式）

## 方式一：Docker Compose（推荐，生产环境）

### 第 1 步：配置环境变量

```bash
cd backend/
cp .env.example .env
```

编辑 `.env`，填写真实密码：

```bash
# 必填项
DB_PASSWORD=你的数据库密码
MYSQL_ROOT_PASSWORD=你的MySQL root密码
SECRET_KEY=任意随机字符串（用于JWT签名）

# 可选：阿里云 OSS（后台也可动态配置）
OSS_ENABLED=false
# OSS_ACCESS_KEY_ID=...
# OSS_ACCESS_KEY_SECRET=...

# 可选：Webhook 通知
# WEBHOOK_URL=https://your-webhook-server.com/notify
```

### 第 2 步：启动服务

```bash
docker-compose up -d --build
```

等待约 30 秒，MySQL 初始化完成后自动启动 API。

### 第 3 步：验证

```bash
# 查看容器状态
docker-compose ps

# 查看后端日志
docker-compose logs -f backend

# 测试 API
curl http://localhost:8082/
# 应返回 API 信息
```

### 第 4 步：创建管理员账号

首次启动后，容器会自动创建默认管理员 `admin / admin123`。

如需自定义管理员密码，在 `.env` 中设置：

```bash
ADMIN_PASSWORD=你的管理员密码
```

然后重启容器：

```bash
docker-compose restart backend
```

### 第 5 步：访问管理后台

浏览器打开：
- 管理后台：`http://localhost:8082/admin/login`
- API 文档（仅限管理员）：`http://localhost:8082/docs`

---

## 方式二：本地开发（Python 直接运行）

适合本地调试，不需要 Docker。

### 第 1 步：创建数据库

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS wallpaper_db CHARACTER SET utf8mb4;"
mysql -u root -p -e "CREATE USER IF NOT EXISTS 'wallpaper'@'%' IDENTIFIED BY '你的密码';"
mysql -u root -p -e "GRANT ALL ON wallpaper_db.* TO 'wallpaper'@'%';"
```

### 第 2 步：安装依赖

```bash
cd backend/
pip install -r requirements.txt
```

### 第 3 步：配置环境变量

```bash
cp .env.example .env
# 编辑 .env，将 DB_HOST 改为 localhost，填好密码
```

### 第 4 步：启动

```bash
uvicorn backend.main:app --reload --port 8082
```

---

## 双服务器同步部署（可选）

如需要同时部署到主/从两台服务器：

1. 编辑 `backend/sync.py`，将 `SERVER_IP_MAIN` / `SERVER_IP_SLAVE` / `YOUR_SSH_PASSWORD` 替换为真实地址
2. 安装 paramiko：`pip install paramiko`
3. 执行同步：

```bash
python backend/sync.py
```

---

# 🌐 PC 官网部署（website/）

## 前置要求

- PHP 8.1+
- Nginx 或 Apache
- SSL 证书（生产环境推荐）

## 部署步骤

### 第 1 步：上传文件

将 `website/` 目录下所有文件上传到服务器 Web 根目录，例如：

```
/www/wwwroot/pc.ddbz.art/
├── 404.html
├── api_session.php
├── config.php
├── download.php
├── feedback.php
├── img.php
├── index.php
└── static/
```

### 第 2 步：修改配置

编辑 `website/config.php`，将 `API_BASE` 指向你的后端地址：

```php
<?php
define('API_BASE', 'https://api.yourdomain.com/api/v1');
define('SITE_NAME', '多点壁纸');
define('LOGO_PATH', 'https://api.yourdomain.com/static/images/logo.png');
define('APP_URL', 'https://pc.yourdomain.com');
```

### 第 3 步：配置 Nginx

```nginx
server {
    listen 80;
    server_name pc.yourdomain.com;
    root /www/wwwroot/pc.yourdomain.com;
    index index.php;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }
}
```

### 第 4 步：上传 logo 图片

将 `logo.png` 上传到后端服务器的 `/app/uploads/static/images/` 目录（Docker 容器内），确保 `LOGO_PATH` 可访问。

---

## ⚠️ 安全提醒

- **永远不要**将 `.env` 文件提交到 Git（已配置 `.gitignore`）
- **永远不要**将服务器密码、API Key 等写入代码注释或文档
- 生产环境务必启用 HTTPS
- 定期更换 JWT 密钥和管理员密码

---

> 本文档生成日期：2026-08-11
