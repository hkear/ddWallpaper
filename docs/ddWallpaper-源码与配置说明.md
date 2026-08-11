# ddWallpaper 源码与配置说明

> 汇总前端（HarmonyOS ArkTS）与后端（FastAPI）的关键代码注释、重要配置与部署信息。
>
> 生成日期：2026-08-11（2026-08-10 更新域名）  
> 前端版本：v1.7.0  
> 后端版本：v1.5.0  
> API 域名：https://api.ddbz.art（旧 https://api.ddbz.cn 仍可用）  
> 包名：com.ddwallpaper.app

---

## 目录

1. [项目概览](#1-项目概览)
2. [前端（HarmonyOS ArkTS）](#2-前端harmonyos-arkts)
3. [后端（FastAPI）](#3-后端fastapi)
4. [部署与运维](#4-部署与运维)
5. [常见问题与注意事项](#5-常见问题与注意事项)
6. [开发纪要](#6-开发纪要)

---

## 1. 项目概览

| 项目 | 路径 | 技术栈 | 说明 |
|------|------|--------|------|
| 前端 | `<PROJECT_ROOT>\frontend` | HarmonyOS ArkTS / ArkUI | 壁纸平台 App，目标 HarmonyOS 5.0 (API 12) |
| 后端 | `<PROJECT_ROOT>\backend` | FastAPI + SQLAlchemy + MySQL (Docker) | REST API + Web 管理后台 |

### 核心功能

- 多设备形态壁纸分类：竖屏（portrait）、横屏（landscape）、两折叠（fold2）、三折叠（fold3）
- 用户注册/登录、收藏、下载、上传（pending 审核）
- 管理员后台：审核、壁纸管理、用户管理、分类管理、反馈管理、系统配置
- 存储层：本地文件 或 阿里云 OSS（支持私有签名 URL）
- 通知：Webhook（企业微信机器人）

---

## 2. 前端（HarmonyOS ArkTS）

### 2.1 技术栈与目标版本

- **开发语言**：ArkTS（TypeScript 子集）
- **UI 框架**：ArkUI 声明式 UI
- **目标 SDK**：`5.0.0(12)`（`build-profile.json5` 中 `targetSdkVersion` / `compatibleSdkVersion`）
- **构建工具**：hvigor 6.22.3+
- **包名**：`com.ddwallpaper.app`
- **应用名称**：中文「多点壁纸」，英文「ddWallpaper」

### 2.2 目录结构

```
ddWallpaper/frontend/
├── AppScope/
│   ├── app.json5                 # 应用级配置：bundleName、版本、图标
│   └── resources/                # 应用级资源（图标、多语言）
│       ├── base/media/           # 分层图标 foreground / background / layered_image.json
│       ├── dark/media/           # 深色模式前景图标
│       └── zh_CN|en_US/          # 多语言 string.json
├── entry/                        # 入口模块
│   ├── build-profile.json5       # 模块构建配置
│   ├── oh-package.json5          # 模块依赖
│   └── src/main/
│       ├── ets/
│       │   ├── entryability/EntryAbility.ets      # 应用入口 Ability
│       │   ├── entrybackupability/                # 备份 Ability
│       │   ├── components/WallpaperCard.ets       # 壁纸卡片组件
│       │   ├── model/WallpaperModel.ets           # 数据模型
│       │   ├── pages/                             # 页面
│       │   │   ├── Index.ets           # 首页（分类 + 瀑布流）
│       │   │   ├── Splash.ets          # 启动页 + 协议弹窗
│       │   │   ├── Login.ets           # 登录/注册
│       │   │   ├── Profile.ets         # 个人中心
│       │   │   ├── Favorites.ets       # 我的收藏
│       │   │   ├── MySubmissions.ets   # 我上传的
│       │   │   ├── WallpaperDetail.ets # 壁纸详情（下载/收藏）
│       │   │   ├── Upload.ets          # 上传壁纸
│       │   │   ├── Settings.ets        # 设置
│       │   │   ├── UserAgreement.ets   # 用户协议
│       │   │   ├── PrivacyPolicy.ets   # 隐私政策
│       │   │   └── ChildrenPrivacy.ets # 儿童隐私保护声明
│       │   └── utils/
│       │       ├── ApiConfig.ets       # API 域名/Host 配置
│       │       ├── api.ets             # HTTP 请求、登录态、所有 API 调用
│       │       ├── cache.ets           # Preferences 页面缓存 + TTL
│       │       ├── network.ets         # 网络可用性检测
│       │       ├── htmlText.ets        # HTML 转结构化文本（协议页渲染）
│       │       └── url.ets             # 图片 URL 解析（相对路径补 Host）
│       ├── module.json5              # 模块配置：权限、Ability、页面
│       └── resources/
│           ├── base/element/           # 颜色、尺寸、字符串
│           ├── base/media/             # 图片资源（logo、设备图标、startIcon）
│           ├── base/profile/           # main_pages.json 页面注册
│           ├── rawfile/                # 内置 HTML（协议/隐私/儿童声明离线兜底）
│           └── dark/media/             # 深色模式资源
├── build-profile.json5             # 工程级构建配置、签名
├── hvigorfile.ts                   # 工程级 hvigor 脚本
└── oh-package.json5                # 工程依赖
```

### 2.3 重要配置文件

#### `AppScope/app.json5`

```json5
{
  "app": {
    "bundleName": "com.ddwallpaper.app",  // 应用包名
    "vendor": "ddwallpaper",              // 厂商
    "versionCode": 1000001,               // 版本号（整数，用于升级）
    "versionName": "1.1.0",               // 版本名称（展示用）
    "icon": "$media:layered_image",       // 分层图标（ foreground + background ）
    "label": "$string:app_name"           // 应用名称，多语言
  }
}
```

#### `entry/src/main/module.json5`

```json5
{
  "module": {
    "name": "entry",
    "type": "entry",
    "mainElement": "EntryAbility",        // 主 Ability
    "deviceTypes": ["phone", "tablet", "tv", "2in1"],
    "pages": "$profile:main_pages",       // 页面注册文件
    "abilities": [
      {
        "name": "EntryAbility",
        "srcEntry": "./ets/entryability/EntryAbility.ets",
        "icon": "$media:layered_image",
        "startWindowIcon": "$media:startIcon",    // 启动页图标
        "exported": true,
        "skills": [
          {
            "entities": ["entity.system.home"],
            "actions": ["ohos.want.action.home"]  // 桌面入口
          }
        ]
      }
    ],
    "requestPermissions": [
      { "name": "ohos.permission.INTERNET" },       // 网络
      { "name": "ohos.permission.GET_NETWORK_INFO" },
      {
        "name": "ohos.permission.WRITE_IMAGEVIDEO", // 保存壁纸到图库
        "reason": "$string:permission_write_media_reason",
        "usedScene": { "abilities": ["EntryAbility"], "when": "always" }
      }
    ]
  }
}
```

#### `build-profile.json5`

```json5
{
  "app": {
    "signingConfigs": [
      {
        "name": "release",
        "type": "HarmonyOS",
        "material": {
          "certpath": "...",      // 调试/发布证书路径
          "keyAlias": "debugKey",
          "keyPassword": "...",
          "profile": "...",       // .p7b profile
          "signAlg": "SHA256withECDSA",
          "storeFile": "...",     // .p12 密钥库
          "storePassword": "..."
        }
      },
      { "name": "default", ... }   // 自动签名/调试签名
    ],
    "products": [
      {
        "name": "default",
        "signingConfig": "release",
        "targetSdkVersion": "5.0.0(12)",        // 目标 API 12
        "compatibleSdkVersion": "5.0.0(12)",
        "runtimeOS": "HarmonyOS",
        "buildOption": {
          "strictMode": {
            "caseSensitiveCheck": true,
            "useNormalizedOHMUrl": true
          }
        }
      }
    ]
  }
}
```

### 2.4 核心代码模块说明

#### `entry/src/main/ets/entryability/EntryAbility.ets`

- 应用入口 `UIAbility`
- 启动时检测系统语言：
  - `zh` 开头 → `appName = '多点壁纸'`
  - 其他 → `appName = 'ddWallpaper'`
- 将 `appName` 写入 `AppStorage`，供所有页面通过 `@StorageLink('appName')` 动态读取
- 初始化 `ApiConfig`

#### `entry/src/main/ets/utils/ApiConfig.ets`

```typescript
export class ApiConfig {
  private baseUrl: string = 'https://api.ddbz.art/api/v1';  // API 基础路径
  private downloadHost: string = 'https://api.ddbz.art';    // 下载/图片 Host
  public agreementUrl: string = 'https://ddbz.art/agreement.html';
  public privacyUrl: string = 'https://ddbz.art/privacy.html';

  public getBaseUrl(): string { return this.baseUrl; }
  public getDownloadHost(): string { return this.downloadHost; }
  public getApiUrl(path: string): string { return this.baseUrl + path; }
  public getDownloadUrl(wallpaperId: string): string {
    return `${this.downloadHost}/api/v1/wallpapers/${wallpaperId}/download`;
  }
}
```

- 支持从 `AppStorage` 读取动态配置（用于测试环境切换）
- 默认生产环境指向 `https://api.ddbz.art`（2026-08-10 起，旧域名 api.ddbz.cn 兼容保留）

#### `entry/src/main/ets/utils/api.ets`

核心 HTTP 层与业务 API 封装：

- **登录态管理**：
  - `initTokenStorage()`：启动时从 Preferences 恢复 token/username/isAdmin 到 AppStorage
  - `saveUserSession()`：登录成功后持久化
  - `clearUserSession()`：退出/401 时清除持久化 + AppStorage + 收藏缓存
- **请求头**：`buildHeaders(hasBody)`，按需设置 `Content-Type: application/json`，自动附加 `Authorization: Bearer <token>`
- **401 处理**：收到 401 时调用 `clearUserSession()`，避免过期 token 残留
- **主要 API**：
  - `login / register`
  - `getWallpapers`（分页、分类、标签、搜索、排序、device_type）
  - `getWallpaperById`
  - `toggleFavorite`（收藏/取消收藏）
  - `getFavorites`
  - `getMySubmissions`
  - `uploadWallpaper`（手动拼装 multipart/form-data，带文本字段 + 图片二进制）
  - `getDownloadUrl`
  - `submitFeedback`
  - `changePassword`

#### `entry/src/main/ets/utils/cache.ets`

- 基于 `data.preferences` 的页面缓存
- `saveCache<T>(key, data, maxAgeMs?)` / `loadCache<T>(key)`
- 支持 TTL（默认 24h），过期自动失效
- 用于首页、收藏、协议等页面的离线兜底

#### `entry/src/main/ets/utils/network.ets`

- `isNetworkAvailable()`：使用 `connection.getDefaultNetSync()` + `NET_CAPABILITY_VALIDATED` 判断网络是否可用
- 用于离线提示与缓存策略

#### `entry/src/main/ets/utils/htmlText.ets`

- `extractTextFromHtml(html)`：将官网 HTML 解析为 `TextSection[]`（标题 + 段落数组）
- `fetchPolicyText(url, cacheKey, rawfileName)`：联网 → 缓存 → rawfile 三级兜底
- `fetchPolicyTextRawfile(rawfileName)`：仅读 rawfile，快速展示
- 供 `UserAgreement.ets`、`PrivacyPolicy.ets`、`Splash.ets`、`ChildrenPrivacy.ets` 复用

#### `entry/src/main/ets/utils/url.ets`

```typescript
export function resolveImageUrl(url: string | undefined | null): string {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  return ApiConfig.getInstance().getDownloadHost() + url;
}
```

- 统一处理后端返回的相对/绝对图片 URL

### 2.5 页面说明

| 页面 | 文件 | 关键功能 |
|------|------|----------|
| 首页 | `pages/Index.ets` | 底部设备分类导航、搜索、排序 chips、壁纸 Grid 分页、设置入口 |
| 启动页 | `pages/Splash.ets` | 首次启动协议弹窗、登录态恢复、跳转首页 |
| 登录/注册 | `pages/Login.ets` | 账号密码登录、注册（支持邮箱/短信验证码） |
| 个人中心 | `pages/Profile.ets` | 修改密码、我的壁纸、我的收藏、上传、管理后台入口、退出登录 |
| 收藏 | `pages/Favorites.ets` | 收藏列表分页、离线缓存 |
| 我的上传 | `pages/MySubmissions.ets` | 投稿列表分页、24h 内 pending 可删除 |
| 壁纸详情 | `pages/WallpaperDetail.ets` | 预览、收藏、下载（带进度条） |
| 上传 | `pages/Upload.ets` | 图片选择、设备/分类/标签/说明填写、multipart 上传 |
| 设置 | `pages/Settings.ets` | 协议入口、关于、意见反馈、退出登录（无需登录） |
| 用户协议 | `pages/UserAgreement.ets` | Web/缓存/rawfile 三级加载 |
| 隐私政策 | `pages/PrivacyPolicy.ets` | Web/缓存/rawfile 三级加载 |
| 儿童隐私 | `pages/ChildrenPrivacy.ets` | rawfile 离线展示 |

### 2.6 离线兜底策略

1. **协议/隐私页**：优先联网 → 失败则读缓存 → 再失败读 `rawfile/*.html`
2. **首页/收藏**：有网时请求 API 并缓存；无网时读缓存；缓存为空则展示 3 张内置壁纸（`builtin_1/2/3`）
3. **网络检测**：`network.ets` 在页面加载前判断，顶部显示「📡 当前离线模式」横幅

---

## 3. 后端（FastAPI）

### 3.1 技术栈

- **框架**：FastAPI + Uvicorn
- **ORM**：SQLAlchemy 2.x
- **数据库**：MySQL 8.0（Docker 容器 `wallpaper_mysql`）
- **认证**：JWT（python-jose + passlib），Token 有效期 7 天
- **部署**：Docker Compose，双服务器（主 + 从）通过 `sync.py` 同步
- **文件存储**：本地 `/app/uploads` 或 阿里云 OSS
- **缩略图**：Pillow 生成 300/720/1080 三种尺寸
- **通知**：Webhook（企业微信机器人）

### 3.2 目录结构

```
ddWallpaper/backend/
├── backend/
│   ├── main.py              # FastAPI 入口、lifespan、中间件、路由挂载
│   ├── config.py            # Pydantic Settings，读取环境变量
│   ├── database.py          # MySQL 连接、Session、init_db
│   ├── models.py            # SQLAlchemy 数据模型
│   ├── schemas.py           # Pydantic Schema
│   ├── auth.py              # 密码哈希、JWT encode/decode
│   ├── storage.py           # 本地存储 / 阿里云 OSS 抽象
│   ├── webhook.py           # Webhook 通知封装
│   ├── migrations.py        # 数据库迁移/字段初始化
│   ├── routers/
│   │   ├── main.py          # 根路由、公开接口
│   │   ├── users.py         # 注册/登录/个人信息/修改密码
│   │   ├── wallpapers.py    # 壁纸 CRUD、上传、下载、收藏状态
│   │   ├── favorites.py     # 收藏接口
│   │   ├── categories.py    # 分类接口
│   │   ├── feedback.py      # 反馈提交（新）
│   │   ├── admin.py         # 管理员 API（审核、用户、分类、壁纸批量管理）
│   │   ├── admin_web.py     # Web 管理后台 HTML 页面
│   │   └── schemas.py       # 路由内公共 schema
│   └── scripts/
│       ├── wallpapers.py    # 壁纸相关脚本函数
│       └── regenerate_urls.py  # 批量刷新壁纸 OSS URL
├── scripts/                 # 数据库备份/迁移脚本
├── .env / .env.example      # 环境变量
├── docker-compose.yml       # Docker Compose 编排
├── Dockerfile
├── requirements.txt

> 注：`website/`（PC 官网前端，index.php/config.php 等）已移至项目根，与 backend/、frontend/ 同级。
├── sync.py                  # 双服务器一键同步部署
└── Logs/                    # 后端日志
```

### 3.3 重要配置文件

#### `.env.example`

```bash
# 数据库
DB_HOST=localhost
DB_PORT=3306
DB_USER=wallpaper
DB_PASSWORD=your_mysql_password
DB_NAME=wallpaper_db
MYSQL_ROOT_PASSWORD=your_mysql_root_password

# JWT（生产环境必须改）
SECRET_KEY=change-this-to-a-random-secret-key

# 注册验证开关（会被 DB 中 auth_config 覆盖，仅作为初始值）
REGISTER_REQUIRE_EMAIL=true
REGISTER_ENABLE_EMAIL_VERIFY=false
REGISTER_ENABLE_SMS_VERIFY=false

# 短信服务商: aliyun | yunpian
SMS_PROVIDER=aliyun

# 邮箱 SMTP 配置
EMAIL_SMTP_HOST=
EMAIL_SMTP_PORT=465
EMAIL_SMTP_USER=
EMAIL_SMTP_PASSWORD=
EMAIL_FROM=
EMAIL_FROM_NAME=多点壁纸

# 阿里云短信配置
ALIYUN_ACCESS_KEY_ID=
ALIYUN_ACCESS_KEY_SECRET=
ALIYUN_SMS_SIGN_NAME=
ALIYUN_SMS_TEMPLATE_CODE=

# 云片短信配置
YUNPIAN_API_KEY=

# 华为 OAuth 配置（预留）
HUAWEI_CLIENT_ID=
HUAWEI_CLIENT_SECRET=

# 阿里云 OSS（可在后台“存储配置”中动态配置，优先级高于环境变量）
OSS_ENABLED=false
OSS_BUCKET=
OSS_ENDPOINT=
OSS_ACCESS_KEY_ID=
OSS_ACCESS_KEY_SECRET=
OSS_CDN_DOMAIN=
OSS_PATH_PREFIX=wallpapers/

# Webhook（可选，审核通知）
# WEBHOOK_URL=https://your-webhook-server.com/notify
```

#### `docker-compose.yml`

```yaml
services:
  mysql:
    image: mysql:8.0
    container_name: wallpaper_mysql
    restart: unless-stopped
    command:
      - --default-authentication-plugin=mysql_native_password
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-root123}
      MYSQL_DATABASE: ${DB_NAME:-wallpaper_db}
      MYSQL_USER: ${DB_USER:-wallpaper}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD:-wallpaper123}
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  backend:
    build: .
    container_name: wallpaper_api
    restart: unless-stopped
    depends_on:
      mysql:
        condition: service_healthy
    environment:
      DB_HOST: ${DB_HOST:-mysql}
      DB_PORT: ${DB_PORT:-3306}
      DB_USER: ${DB_USER:-wallpaper}
      DB_PASSWORD: ${DB_PASSWORD:-${MYSQL_PASSWORD:-wallpaper123}}
      DB_NAME: ${DB_NAME:-wallpaper_db}
      SECRET_KEY: ${SECRET_KEY:-change-this-to-a-random-secret-key}
      ADMIN_PASSWORD: ${ADMIN_PASSWORD:-admin123}
      ADMIN_EMAIL: ${ADMIN_EMAIL:-admin@example.com}
      OSS_SIGNED_URL: ${OSS_SIGNED_URL:-false}
      # ... 其他环境变量
    ports:
      - "8082:8082"
    volumes:
      - uploads:/app/uploads

volumes:
  mysql_data:
  uploads:
```

#### `backend/config.py`

```python
class Settings(BaseSettings):
    # Database
    DB_HOST: str = "mysql"
    DB_PORT: int = 3306
    DB_USER: str = "wallpaper"
    DB_PASSWORD: str = "wallpaper123"
    DB_NAME: str = "wallpaper_db"

    # JWT
    SECRET_KEY: str = "change-me-in-production-abc123xyz"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Upload
    UPLOAD_DIR: str = "/app/uploads"
    MAX_FILE_SIZE: int = 20 * 1024 * 1024  # 20MB

    # CORS
    CORS_ORIGINS: list[str] = ["https://api.ddbz.art", "https://ddbz.art", "https://www.ddbz.art",
                               "https://api.ddbz.cn", "https://ddbz.cn", "https://www.ddbz.cn",
                               "https://app.ddbz.cn", "https://wallpaper.ddbz.cn"]

    # Debug / security toggles
    DEBUG_MODE: bool = False
    ENABLE_API_DOCS: bool = False
    ENABLE_HEALTH_CHECK: bool = False

    # Auth verification toggles (can be overridden by DB AuthConfig at runtime)
    REGISTER_REQUIRE_EMAIL: bool = True
    REGISTER_ENABLE_EMAIL_VERIFY: bool = False
    REGISTER_ENABLE_SMS_VERIFY: bool = False
    SMS_PROVIDER: str = "aliyun"

    # Aliyun OSS (env defaults; can be overridden by DB StorageConfig)
    OSS_ENABLED: bool = False
    OSS_BUCKET: str = ""
    OSS_ENDPOINT: str = ""
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_CDN_DOMAIN: str = ""
    OSS_PATH_PREFIX: str = "wallpapers/"
    OSS_SIGNED_URL: bool = False
```

- 环境变量优先级最高，`.env` 文件次之，代码默认值最后
- 数据库、OSS、SMTP、短信等配置均可在后台动态修改并覆盖环境变量

### 3.4 核心代码模块说明

#### `backend/main.py`

- `lifespan`：
  - 启动时创建 `UPLOAD_DIR`
  - `init_db()` 初始化数据库表
  - 强制重置 id=1 管理员密码为 `YOUR_ADMIN_PASSWORD`
  - 启动时清理一次超 24h pending 壁纸
  - 创建每小时定期清理任务 `_periodic_cleanup()`
- 中间件：
  - `CORSMiddleware`：跨域白名单
  - `TrustedHostMiddleware`：允许的 Host（`api.ddbz.art`, `ddbz.art`, `www.ddbz.art`, `api.ddbz.cn`, `ddbz.cn`, `www.ddbz.cn`, `localhost`, `<IP_ADDRESS>`）
  - `SecurityHeadersMiddleware`：安全响应头
  - `AdminDocsMiddleware`：拦截 `/docs`, `/redoc`, `/openapi.json`，仅管理员可访问
- 静态文件：`/static` 映射本地上传目录
- 路由挂载：`/api/v1` 前缀 + `/admin` Web 后台

#### `backend/database.py`

- `SQLALCHEMY_DATABASE_URL`：`mysql+pymysql://...`
- `init_db()`：创建所有表，若不存在 `admin` 用户则自动创建默认管理员
- `SessionLocal`：请求级数据库会话

#### `backend/models.py`

核心模型：

| 模型 | 说明 |
|------|------|
| `User` | 用户（id, username, email, hashed_password, is_admin, created_at） |
| `Category` | 壁纸分类 |
| `Wallpaper` | 壁纸（title, device_type, category_id, tags, status, original_url, thumbnails, uploader_id 等） |
| `Favorite` | 用户收藏关联表 |
| `Like` | 点赞记录（当前版本已弱化，收藏独立） |
| `WebhookConfig` | Webhook URL 配置 |
| `StorageConfig` | 存储配置（本地/OSS/签名 URL） |
| `SmtpConfig` / `SmsConfig` / `AuthConfig` | 邮件/短信/注册验证开关配置 |
| `Feedback` | 用户反馈 |

#### `backend/routers/wallpapers.py`

- 壁纸列表、详情、上传、下载、删除
- 上传后自动生成缩略图（300/720/1080）
- 普通用户上传 → `status=pending`，触发 webhook「新投稿待审核」
- 管理员上传 → `status=approved`
- 下载接口 `/api/v1/wallpapers/{id}/download`：匿名访问，实时生成签名 URL 后 302 跳转
- 删除规则：管理员任意删除；普通用户仅 24h 内 pending 可删

#### `backend/routers/admin.py`

管理员接口：

- `GET /admin/submissions`：待审核/已审核/已拒绝/已下架 列表
- `POST /admin/wallpapers/{id}/review`：审核通过/拒绝
- `PUT /admin/wallpapers/{id}`：单个壁纸编辑
- `POST /admin/wallpapers/batch`：批量更新（分类/设备/标题）
- `GET /admin/users` / `PUT /admin/users/{id}` / `DELETE /admin/users/{id}`：用户管理
- `GET /admin/categories` / `POST /admin/categories` / `PUT /admin/categories/{id}` / `DELETE`：分类 CRUD
- `GET /admin/feedback` / `DELETE /admin/feedback/{id}`：反馈管理
- `POST /admin/test-storage` / `test-smtp` / `test-sms`：连通性测试

#### `backend/routers/admin_web.py`

- Web 管理后台所有 HTML 页面
- 页面路由公开，权限由前端 JS 调用 API 时通过 Bearer token/Cookie `admin_token` 校验
- 包含：登录页、仪表盘、审核、壁纸管理、用户管理、分类管理、反馈管理、配置页

#### `backend/storage.py`

- `LocalStorage`：本地文件存储，URL 为 `/static/...`
- `AliyunOSSStorage`：阿里云 OSS 存储
  - `url(key)`：根据 `signed_url` 开关返回 CDN URL 或 7 天有效签名 URL
  - 上传接口：`put_object`
- `get_storage()`：优先读取 DB `StorageConfig`，其次环境变量，最后 fallback 本地

#### `backend/webhook.py`

- 统一封装 `get_webhook_url()`、`send_webhook()`、`send_webhook_async()`
- 事件类型：`wallpaper_uploaded`、`wallpaper_approved`、`wallpaper_rejected`、`feedback_received`、`admin_notification`
- 识别 `<WEBHOOK_DOMAIN>` 时发送企业微信文本消息格式

### 3.5 API 概览

#### 公开接口

- `GET /`：API 信息
- `GET /api/v1/wallpapers`：壁纸列表
- `GET /api/v1/wallpapers/{id}`：壁纸详情
- `GET /api/v1/wallpapers/{id}/download`：下载壁纸（302 到存储 URL）
- `GET /api/v1/categories`：分类列表

#### 需登录接口

- `POST /api/v1/users/register`
- `POST /api/v1/users/login`
- `GET /api/v1/users/me`
- `POST /api/v1/users/me/change-password`
- `GET /api/v1/users/me/favorites`
- `POST /api/v1/users/me/favorites/{id}`
- `POST /api/v1/wallpapers`：用户上传
- `GET /api/v1/users/me/submissions`

#### 管理员接口

- `/api/v1/admin/*`

#### 反馈

- `POST /api/v1/feedback`：匿名/登录均可提交

---

## 4. 部署与运维

### 4.1 前端构建

```powershell
# 设置环境变量
$env:JAVA_HOME = "<JAVA_HOME>"
$env:PATH = "<JAVA_HOME>\bin;$env:PATH"
$env:HWSDK_DIR = "D:\HarmonyOS_Dev\commandline-tools-windows-x64-<IP_ADDRESS>\command-line-tools\sdk"
$env:DEVECO_SDK_HOME = "D:\HarmonyOS_Dev\commandline-tools-windows-x64-<IP_ADDRESS>\command-line-tools\sdk"

# 构建
node "D:\HarmonyOS_Dev\commandline-tools-windows-x64-<IP_ADDRESS>\command-line-tools\hvigor\hvigor\bin\hvigor.js" assembleApp
```

### 4.2 后端部署

#### 本地 Docker 启动

```bash
cd <PROJECT_ROOT>\backend
docker compose up -d --build
```

#### 双服务器同步部署

```bash
python <PROJECT_ROOT>\backend\sync.py
```

- 自动上传 9 个核心文件到 `SERVER_IP_MAIN` 和 `SERVER_IP_SLAVE`
- 执行 `docker compose down && build --no-cache && up -d`

#### 服务器手动部署

```bash
ssh kay@SERVER_IP_MAIN
cd /www/wwwroot/ddbz/backend
sudo docker compose build backend
sudo docker compose up -d backend
```

### 4.3 关键运维脚本

| 脚本 | 路径 | 用途 |
|------|------|------|
| `sync.py` | 后端根目录 | 双服一键同步部署 |
| `regenerate_urls.py` | `backend/scripts/` | 批量按当前存储配置刷新壁纸 URL |
| `migrate_to_oss.py` | `scripts/` | 存量文件迁移到 OSS |
| `backup_db.sh` / `restore_db.sh` | `scripts/` | 数据库备份/恢复 |

---

## 5. 常见问题与注意事项

### 5.1 前端

1. **签名问题**：真机部署必须使用 release 签名；模拟器可用 default 自动签名
2. **包名变更**：从 `com.iwallpaper.app` 改为 `com.ddwallpaper.app` 后，需同步更新证书与 `AppScope/app.json5`
3. **API 废弃警告**：SDK 6.0.2 编译器对 `@ohos.router`、`promptAction`、`PhotoViewPicker` 等标记废弃，API 12 设备仍可运行
4. **multipart 上传**：`api.ets` 中 `uploadWallpaper()` 手动拼装 multipart body，文本字段与图片二进制必须按 CRLF 分隔
5. **离线兜底**：协议/隐私/儿童声明使用 rawfile 内置 HTML；首页/收藏使用内置壁纸兜底

### 5.2 后端

1. **管理员密码**：lifespan 启动会强制把 id=1 的管理员密码重置为 `YOUR_ADMIN_PASSWORD`
2. **OSS 签名 URL**：私有 Bucket 必须开启 `signed_url`，URL 7 天有效，需定期运行 `regenerate_urls.py`
3. **URL 提取**：`_extract_key_from_url()` 必须正确剥离 `path_prefix`，否则会出现 `wallpapers/wallpapers/xxx.jpg` 404
4. **pending 清理**：启动 + 每小时自动清理超过 24h 的 pending 壁纸
5. **WAF 拦截**：管理后台登录接口 `/api/v1/users/login` 可能被服务器防火墙拦截，需配置白名单
6. **API 文档**：`/docs`、`/redoc`、`/openapi.json` 仅管理员可访问

---

## 6. 开发纪要

> 记录项目推进过程中的关键决策、踩坑与经验，便于后续维护与复盘。

### 6.1 品牌升级决策

- **时间**：2026-07-28
- **背景**：原名称 `iWallpaper` 与苹果设备壁纸 App 冲突，上架审核要求更名
- **决策**：
  - 品牌名改为 `ddWallpaper`，中文「多点壁纸」
  - 包名从 `com.iwallpaper.app` 改为 `com.ddwallpaper.app`
  - 重新生成 release 签名证书（`20260727-ddWP`）
  - 所有 string.json、rawfile HTML、页面默认值、版权文档同步更新
- **经验**：包名变更涉及证书绑定，必须在 DevEco Studio 中重新配置签名，不能仅替换文本

### 6.2 图标分层与深色模式

- **时间**：2026-07-28
- **决策**：
  - 采用 HarmonyOS 分层图标规范：前景 1024×1024 透明 PNG + 背景 1024×1024 纯色 PNG
  - `AppScope/resources/base/media/foreground.png` 为浅色前景
  - `AppScope/resources/dark/media/foreground.png` 为深色前景，系统自动切换
  - 页面内图标统一使用 `logo_blank.png`
- **踩坑**：`startIcon.png` 未更新时，启动页一直显示默认蓝色方块，需同步替换

### 6.3 协议/隐私页的加载策略演进

- **初期**：直接 Web 组件加载官网页，离线时白等 15 秒超时
- **演进**：
  - v1.5.0：Web 组件 + rawfile 离线兜底
  - v1.6.0：改为原生 Text 组件渲染，官网 HTML 经 `htmlText.ets` 解析为结构化文本
  - 加载顺序：rawfile 立即展示 → 后台联网更新缓存 → 下次启动使用最新内容
- **决策原因**：上架检测反馈协议页加载过慢，且原生渲染更符合审核要求

### 6.4 离线兜底方案

- **时间**：2026-07-28
- **决策**：
  - 内置 3 张壁纸（深海/星河/极光），id 为 `builtin_1/2/3`
  - 无网络且缓存为空时展示内置壁纸
  - 页面顶部显示「📡 当前离线模式」横幅
- **踩坑**：`WallpaperCard.ets` 中 `wallpaper.id.startsWith('builtin_')` 在 API 返回 number 类型 id 时崩溃，修复为 `typeof === 'string'` 先判断类型

### 6.5 后端存储层重构

- **时间**：2026-07-24 ~ 2026-07-26
- **背景**：OSS Bucket 关闭公共读取后，App 下载/预览返回 403/404；`import_wallroom.py` 绕过 OSS 导致 875 张壁纸黑图
- **决策**：
  - `StorageConfig` 新增 `signed_url` 字段，支持私有 Bucket 临时签名 URL
  - 下载接口改为匿名访问，每次请求实时生成 URL
  - 重写 `import_wallroom.py`：下载 → 生成缩略图 → 直传 OSS → DB 写 OSS URL
  - 新增 `regenerate_urls.py` 批量刷新 URL
- **经验**：存储配置必须支持运行时动态切换，不能写死在代码中；URL 提取必须正确剥离 `path_prefix`

### 6.6 分页加载实现

- **时间**：2026-07-26
- **决策**：
  - 首页/收藏 Grid 每页 20 张，距底部 5 张时预加载
  - 我的投稿 List 使用 `onReachEnd` 触底加载
  - 缓存增加 TTL，24h 过期自动失效
- **原因**：壁纸数量增长后一次性加载导致内存与性能问题

### 6.7 登录态与权限

- **关键修复**：
  - `Login.ets` 中 `saveUserSession()` 添加 `await`，避免登录后 token 未持久化就返回首页
  - `api.ets` 收到 401 时调用 `clearUserSession()`，同步清除 Preferences
  - `WallpaperDetail.ets` 下载/收藏前校验 token
- **决策**：收藏与点赞拆分为独立接口，前端收藏按钮必须调用 `/users/me/favorites/{id}`，而非 `/wallpapers/{id}/like`

### 6.8 反馈系统

- **时间**：2026-07-28
- **决策**：
  - 后端新增 `Feedback` 表 + `POST /api/v1/feedback` 接口
  - 网站 `feedback.php` 作为统一入口，PHP 校验后 curl 转发到后端
  - 提交后通过 webhook 推送企业微信通知
- **踩坑**：App 端 URL 多写 `/`（`/feedback/` vs `/feedback`），后端补加兼容路由

### 6.9 API 文档权限

- **时间**：2026-07-28
- **决策**：
  - FastAPI `docs_url/redoc_url/openapi_url` 始终启用
  - 自定义 `AdminDocsMiddleware` 拦截 `/docs`、`/redoc`、`/openapi.json`
  - 校验 Cookie `admin_token` 或 Header `Authorization` 中的 JWT，且 `is_admin=true`
  - 非管理员返回 403 HTML，管理员放行
- **原因**：之前 `ENABLE_API_DOCS=false` 全局关闭，无区分能力

### 6.10 双服务器部署

- **时间**：2026-07-28
- **决策**：
  - 主服务器 `SERVER_IP_MAIN` 跑 API + Website
  - 从服务器 `SERVER_IP_SLAVE` 仅跑 API
  - 本地通过 `sync.py` 一键同步 9 个核心文件并重建容器
- **踩坑**：
  - `kay` 用户不在 docker 组，所有 docker 命令加 `sudo`
  - 网站目录属主为 www，SFTP 上传需先传到 `/home/<USER>/` 再 `sudo cp`
  - PowerShell 与 Python 嵌套引号复杂，改为写入远程脚本文件再执行

### 6.11 重要待办/后续方向

- [ ] 前端 v1.6.0 未提交变更尽快 commit
- [ ] 将 `sync.py` 升级为 Git Hook 或 GitHub Actions CI/CD
- [ ] OSS 签名 URL 7 天过期，配置定时任务运行 `regenerate_urls.py`
- [ ] 长期迁移废弃 API：`@ohos.router` → `NavPathStack`，`PhotoViewPicker` → `PhotoPickerComponent`
- [ ] 华为账号一键登录（预留接口已存在）
- [ ] 儿童隐私保护声明入口完善

### 6.12 项目目录整合（2026-08-07）

- **背景**：iWallpaper 包名被占用后，发布构建统一在 ddWallpaper（v1.1.1）进行，本地同时存在 `iWallpaper/`（旧版 v1.1.0 副本）与 `ddWallpaper-backend/` 两套目录，且后端在本地/主服/从服三方出现文件漂移。
- **决策**：
  - 整合为单目录：`ddWallpaper/frontend`（HarmonyOS App，含原 git 历史）、`ddWallpaper/backend`（FastAPI 后端）、`ddWallpaper/docs`
  - 删除 `iWallpaper/` 旧副本与 `ddWallpaper-backend-deploy.tar.gz`（留存 `ddWallpaper-backup-<DATE>.tar.gz`）
  - 后端以服务器最新代码为准回收本地：`webhook.py`/`database.py`（uniPush 通知格式）、`config.py`（CORS 扩展）、`Dockerfile`（阿里云镜像 + COPY scripts）
  - `backend/admin.py`、`backend/admin_web.py` 与 `routers/` 下同名文件保持一致（服务器惯例）
  - `sync.py` 同步清单补全为全量核心文件，避免再次漂移
  - 清理前端构建缓存/截图/旧证书与后端一次性调试脚本
- **注意**：发布签名证书在 `<CERT_DIR>\iWallpaper\20260727-ddWP\`，与项目目录解耦，不受整理影响（2026-08-11 起已迁入项目内 `ddWallpaper/frontend/证书/`）

### 6.13 API 域名迁移 api.ddbz.art（2026-08-10）

- **背景**：后端 API 主域名从 `api.ddbz.cn` 切换到 `api.ddbz.art`（主服 SERVER_IP_MAIN）
- **决策**：
  - 后端 `main.py` TrustedHost、`config.py` CORS_ORIGINS 同时保留 `.art`（新）与 `.cn`（旧，兼容已安装 App）
  - nginx 站点 + SSL 证书（1Panel 申请）+ 反代 `<IP_ADDRESS>:8082` 在主服配置完成
  - 前端 `ApiConfig.ets` / `api_config.json` / 协议页链接同步切到 `.art`
  - 旧域名 `api.ddbz.cn` 解析在从服 SERVER_IP_SLAVE，继续服役
- **踩坑**：后端未加新 Host 前，反代通了但请求被 `TrustedHostMiddleware` 拦截返回 400；期间主服容器曾被面板侧误删，数据卷（`backend_mysql_data`/`backend_uploads`）未受影响，`docker-compose up -d` 挂载原卷即恢复

### 6.14 新品牌图标素材 + 签名证书入库（2026-08-11）

- **背景**：2026-08-10 设计产出新品牌图标素材，本次统一替换；签名证书此前散落在项目外 `<CERT_DIR>\`，构建配置不可移植
- **决策**：
  - 图标素材（logo/logo_blank/foreground base+dark/startIcon/button）同步 4 处（项目根、AppScope、entry base、entry dark）
  - `Avatar.ets`、`Index.ets` 设备栏默认图标改用新 `button.png`
  - 证书统一收进 `frontend/证书/`（正式 ddWP + 调试 ddWallpaper_debug_260810），`build-profile.json5` 迁移路径
  - `.gitignore` 增加 `/证书` 防止签名私钥入库
- **注意事项**：调试签名更换后真机需先卸载旧包；`ddWallpaper_debug_260810` 含日期后缀，注意有效期；release 证书 .p7b 与 .cer/.p12 配套性以发版签名结果为准

---

## 附录：版本变更快照

| 日期 | 前端版本 | 后端版本 | 主要变更 |
|------|----------|----------|----------|
| 2026-07-22 | v1.0.0 | v1.2.0 | 项目初始化、后端搭建 |
| 2026-07-22 | v1.2.0 | v1.3.0 | 首页重构、协议页、上传功能 |
| 2026-07-23 | v1.3.1~v1.3.3 | v1.4.1~v1.4.4 | 下载/上传修复、登录态加固、缩略图、Webhook 配置 |
| 2026-07-24 | v1.4.0~v1.5.0 | v1.5.0 | 国际化、域名切换、收藏修复、协议官网化、离线缓存 |
| 2026-07-26 | - | v1.6.0 | 前端分页加载、后端 OSS 存储修复 |
| 2026-07-28 | v1.6.0 | v1.5.0 | 品牌升级 ddWallpaper、分层图标、离线兜底、反馈系统、批量壁纸管理、API 文档权限、双服同步 |
| 2026-08-10 | v1.6.0→ | v1.5.0→ | API 域名迁移 `api.ddbz.art`（前后端同步，旧 `.cn` 兼容保留） |
| 2026-08-11 | v1.7.0 | - | 新品牌图标素材、签名证书收进项目 `frontend/证书/`（release+debugs）、Avatar/Index 页面微调 |

---

> 本文档由 AI CODING 于 2026-07-29 整理生成，后续代码变更请及时同步更新。
