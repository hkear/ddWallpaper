# 多点壁纸后端部署指南

> FastAPI + MySQL + Docker 壁纸平台 API

---

## 前置要求

- [Docker](https://docs.docker.com/get-docker/) 与 [Docker Compose](https://docs.docker.com/compose/install/)
- 或 Python 3.11+（仅本地开发模式）

---

## 方式一：Docker Compose（推荐，生产环境）

### 第 1 步：配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，至少填写以下必填项：

```bash
# 数据库密码（必填）
DB_PASSWORD=你的数据库密码
MYSQL_ROOT_PASSWORD=你的MySQL root密码

# JWT 密钥（必填，任意随机字符串）
SECRET_KEY=change-this-to-a-random-secret-key

# 管理员密码（可选，默认 admin123）
ADMIN_PASSWORD=你的管理员密码
```

> ⚠️ **安全提醒**：`.env` 文件已加入 `.gitignore`，**切勿提交到仓库**。

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

### 第 4 步：访问管理后台

| 地址 | 说明 |
|------|------|
| `http://localhost:8082/admin/login` | 管理后台登录 |
| `http://localhost:8082/docs` | Swagger API 文档（仅管理员） |
| `http://localhost:8082/redoc` | ReDoc API 文档（仅管理员） |

默认管理员账号：`admin` / `.env` 中配置的 `ADMIN_PASSWORD`（未配置则为 `admin123`）

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
pip install -r requirements.txt
```

### 第 3 步：配置环境变量

```bash
cp .env.example .env
# 编辑 .env：DB_HOST 改为 localhost，填好密码
```

### 第 4 步：启动

```bash
uvicorn backend.main:app --reload --port 8082
```

---

## 环境变量说明

| 变量 | 说明 | 默认值 | 是否必填 |
|------|------|--------|---------|
| `DB_HOST` | MySQL 主机 | `mysql` | 否 |
| `DB_PORT` | MySQL 端口 | `3306` | 否 |
| `DB_USER` | 数据库用户名 | `wallpaper` | 否 |
| `DB_PASSWORD` | 数据库密码 | `wallpaper123` | **是** |
| `DB_NAME` | 数据库名 | `wallpaper_db` | 否 |
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码 | `root123` | **是** |
| `SECRET_KEY` | JWT 签名密钥 | `change-this...` | **是** |
| `ADMIN_PASSWORD` | 管理员密码 | `admin123` | 否 |
| `WEBHOOK_URL` | 审核通知 Webhook | 空 | 否 |
| `OSS_ENABLED` | 启用阿里云 OSS | `false` | 否 |
| `OSS_ACCESS_KEY_ID` | OSS AccessKey ID | 空 | 否 |
| `OSS_ACCESS_KEY_SECRET` | OSS AccessKey Secret | 空 | 否 |

---

## 目录结构

```
backend/
├── backend/            # Python 包
│   ├── main.py         # FastAPI 入口
│   ├── config.py       # Pydantic 配置
│   ├── database.py     # MySQL 连接
│   ├── models.py       # SQLAlchemy 模型
│   ├── schemas.py      # Pydantic Schema
│   ├── auth.py         # JWT 认证
│   ├── storage.py      # 文件存储（本地/OSS）
│   ├── webhook.py      # 通知封装
│   └── routers/        # API 路由
├── scripts/            # 运维脚本（备份/迁移）
├── docker-compose.yml  # Docker 编排
├── Dockerfile
├── requirements.txt    # 锁定依赖
├── .env.example        # 环境变量模板
└── sync.py             # 双服务器同步脚本
```

---

## 常用命令

```bash
# 重启后端
docker-compose restart backend

# 查看日志
docker-compose logs -f backend

# 进入容器调试
docker exec -it wallpaper_api bash

# 进入 MySQL
docker exec -it wallpaper_mysql mysql -u root -p

# 停止所有服务
docker-compose down

# 停止并删除数据卷（⚠️ 会清空数据库）
docker-compose down -v
```

---

## 接口速查

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/users/register` | 注册 |
| POST | `/api/v1/users/login` | 登录 |
| GET | `/api/v1/users/me` | 个人信息 |
| GET | `/api/v1/wallpapers/` | 壁纸列表 |
| GET | `/api/v1/wallpapers/{id}` | 壁纸详情 |
| POST | `/api/v1/wallpapers/` | 上传壁纸（需登录） |
| GET | `/api/v1/wallpapers/{id}/download` | 下载壁纸 |
| GET | `/api/v1/users/me/favorites` | 收藏列表 |
| GET | `/api/v1/admin/submissions` | 审核列表（需管理员） |
| POST | `/api/v1/admin/submissions/{id}` | 审核通过/拒绝 |
