# ddWallpaper 项目

> 多点壁纸 —— HarmonyOS 壁纸平台（前端 ArkTS + 后端 FastAPI）

## 项目结构

| 目录 | 说明 |
|------|------|
| `frontend/` | HarmonyOS ArkTS 应用（包名 com.ddwallpaper.app） |
| `backend/` | FastAPI 后端（REST API + Web 管理后台） |
| `website/` | PC 官网前端（index.php/config.php 等，部署于 pc.ddbz.art） |
| `docs/` | 源码与配置说明、会话记录 |
| `敏感数据/` | 脱敏前原始数据归档（完整备份 zip、版权申报资料、设计素材），**勿对外分发** |
| `frontend/证书/` | 应用签名证书目录（**已脱敏，证书文件已移除**） |

## 环境信息（已脱敏）

- **API 域名**: `https://api.ddbz.art`
- **后端版本**: v1.5.0
- **前端版本**: v1.7.0（versionName 1.1.1）
- **部署**: Docker Compose，双服务器

---

# 🔒 脱敏说明

本仓库为对外共享/交付版本，所有**敏感信息已被脱敏替换**，完整原始内容保存在备份压缩包中：

> **备份文件**: `敏感数据/ddWallpaper-backup-<DATE>.zip`（含全部原始代码、`.env`、签名证书）

## 脱敏内容对照表

> 说明：以下仅列出脱敏项类型与占位符。原始敏感值（服务器 IP、SSH/DB/管理员密码、API Key 等）已全部从本仓库移除，完整原始内容见备份压缩包。

| 敏感信息类型 | 脱敏后占位符 | 涉及文件 |
|-------------|-------------|---------|
| 主服务器 IP | `SERVER_IP_MAIN` | sync.py、Logs、docs |
| 从服务器 IP | `SERVER_IP_SLAVE` | sync.py、Logs、docs |
| SSH 登录密码 | `YOUR_SSH_PASSWORD` | sync.py、devRules.md |
| MySQL 数据库密码 | `YOUR_DB_PASSWORD` / `YOUR_MYSQL_ROOT_PASSWORD` | `.env`、ai_tag_wallpapers.py |
| JWT 密钥 | `YOUR_SECRET_KEY` | `.env` |
| 管理员密码 | `YOUR_ADMIN_PASSWORD` | main.py、Logs |
| 阿里云 OSS AccessKey | `YOUR_OSS_ACCESS_KEY_ID` / `YOUR_OSS_ACCESS_KEY_SECRET` | 文档 |
| DashScope AI API Key | `YOUR_DASHSCOPE_API_KEY` | ai_tag_wallpapers.py |
| uniPush Webhook URL | `YOUR_UNIPUSH_WEBHOOK_URL` | database.py |
| 管理员邮箱 | `admin@example.com` | docker-compose.yml、database.py |
| 签名证书密码（DevEco 加密值） | `YOUR_STORE_PASSWORD_ENCRYPTED` / `YOUR_KEY_PASSWORD_ENCRYPTED` | build-profile.json5 |

## 已移除的敏感文件

| 文件 | 说明 | 恢复来源 |
|------|------|---------|
| `frontend/证书/正式证书/ddWP.p12` | release 签名密钥库 | 备份 zip |
| `frontend/证书/正式证书/ddWPRelease.p7b` | release 配置文件 | 备份 zip |
| `frontend/证书/正式证书/ddWP.cer` | release 证书 | 备份 zip |
| `frontend/证书/调试证书/ddWallpaper_debug_260810.p12` | debug 签名密钥库 | 备份 zip |
| `frontend/证书/调试证书/ddWallpaper_debug_260810Debug.p7b` | debug 配置文件 | 备份 zip |
| `frontend/证书/调试证书/ddWallpaper_debug_260810.cer` | debug 证书 | 备份 zip |
| `backend/.env`（真实密码版） | 环境配置 | 备份 zip 或 `.env.example` 模板 |

## 如何恢复原始配置

1. 从备份 `ddWallpaper-backup-<DATE>.zip` 解压对应文件
2. `frontend/证书/`：恢复证书后，将 `frontend/build-profile.json5` 中的
   `YOUR_STORE_PASSWORD_ENCRYPTED` / `YOUR_KEY_PASSWORD_ENCRYPTED` 替换为 DevEco 重新生成的加密值
3. `backend/.env`：从备份恢复，或复制 `.env.example` 填入真实密码
4. `backend/sync.py`：将 `SERVER_IP_MAIN` / `SERVER_IP_SLAVE` / `YOUR_SSH_PASSWORD` 替换为真实服务器地址

## ⚠️ 安全提醒

- 禁止将 `.env`、`证书/` 目录、服务器 IP/密码提交到任何公开仓库
- `.gitignore` 已包含 `/证书`、`.env`、`.cache` 等敏感路径
- 泄露密钥请立即在对应平台（阿里云/华为AGC/服务器）轮换

---

> 本文档生成日期：2026-08-11
