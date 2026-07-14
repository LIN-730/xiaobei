# P1 基础设施代码审查报告

> 审查日期: 2026-06-12  
> 审查人: edu-review agent  
> 技术栈: FastAPI + PostgreSQL (asyncpg) + Redis + JWT + bcrypt + Fernet (AES-256-GCM)  
> 审查模式: 只读审查，不修改代码

---

## 总览

| 审查维度 | 文件数 | 问题数 | 严重 | 中等 | 建议 |
|---------|-------|-------|------|------|------|
| 安全性 | 5 | 5 | 2 | 2 | 1 |
| 正确性 | 10 | 8 | 2 | 4 | 2 |
| 性能 | 4 | 3 | 0 | 1 | 2 |
| 代码规范 | 12 | 6 | 0 | 2 | 4 |
| **合计** | **13** | **22** | **4** | **9** | **9** |

---

## 一、安全性 (Security)

### 1.1 [严重] `config.py:27` — 默认密钥为硬编码 `change_me`

**文件**: `app/config.py:27,36,42`  
**问题**: `JWT_SECRET_KEY`, `POSTGRES_PASSWORD`, `CREDENTIAL_ENCRYPTION_KEY` 全部默认 `"change_me"`。生产环境一旦忘记覆盖 `.env`，将导致：
- JWT 可被任意伪造签名
- 数据库可直接连接
- AES 凭证加密等同于明文

**建议**: 
- 删除所有默认值改为 `Optional[str] = None`，在启动时检测 `None` 并抛出配置错误
- 或使用 `pydantic.Field(validation_alias=...)` + `Field(validate_default=True)` 拒绝默认值
- 至少添加 `@validator` 在生产模式下拒绝 `"change_me"`

### 1.2 [严重] `security.py:10` — Fernet 密钥未做 Base64 校验，解密必然崩溃

**文件**: `app/auth/security.py:10`  
**代码**: `_fernet = Fernet(settings.CREDENTIAL_ENCRYPTION_KEY.encode())`  
**问题**: Fernet 构造函数要求 **32 字节 URL-safe Base64 编码的密钥**。而配置中 `CREDENTIAL_ENCRYPTION_KEY: str = "change_me"` 只是一个普通字符串。运行时必定抛出 `ValueError: Fernet key must be 32 url-safe base64-encoded bytes`。

**建议**: 
- 方案 A: 配置中直接存放 Base64 密钥，并在 settings 中验证 `len(base64.b64decode(key)) == 32`
- 方案 B: 在 `security.py` 中通过 `base64.urlsafe_b64encode(base64.urlsafe_b64decode(key_bytes))` 标准化
- 方案 C: 参考做法 — 使用 `from cryptography.fernet import Fernet; Fernet.generate_key()` 生成，存入 `.env` 作为 `CREDENTIAL_ENCRYPTION_KEY=...` 整段 Base64 字符串

### 1.3 [中等] `config.py:2` — JWT 使用 HS256，未配置 RS256/ES256

**文件**: `app/config.py:27-28`  
**问题**: `JWT_SECRET_KEY` + `HS256` 是对称签名。如果密钥泄露（如通过日志、调试输出、Git 提交），攻击者可伪造任意 Token。

**建议**: 生产环境建议切换到 RS256（非对称密钥）:
- JWT 签名用私钥，验证用公钥
- 公钥可安全暴露给认证中间件
- 降低密钥泄露时的危害范围

### 1.4 [中等] `config.py:11` — CORS_ORIGINS 默认为 `*`

**文件**: `app/config.py:11`  
**代码**: `CORS_ORIGINS: str = "*"`  
**问题**: 生产环境设置 `allow_origins="*"` 允许任意跨域请求，适合开发但不利于生产安全。

**建议**: 
- 添加环境验证：若 `DEBUG=False` 且 `CORS_ORIGINS="*"`，输出警告或拒绝启动
- 或默认值设为 `"http://localhost:3000"`，由生产 `.env` 覆盖

### 1.5 [建议] `dependencies.py:22` — 异常捕获过于宽泛

**文件**: `app/auth/dependencies.py:19-23`  
**代码**: 
```python
try:
    payload = verify_token(token, expected_type="access")
    user_id = payload["sub"]
except Exception:
    raise HTTPException(status_code=401, detail="Token 无效或已过期")
```

**问题**: `except Exception` 会捕获所有异常，包括 `JWTError`、`KeyError`、数据库连接错误等。应仅捕获预期的异常类型，以免掩盖非 Token 相关错误。

**建议**: 改为:
```python
from jose import JWTError
try:
    payload = verify_token(token, expected_type="access")
    user_id = payload["sub"]
except JWTError:
    raise HTTPException(status_code=401, detail="Token 无效或已过期")
```

---

## 二、正确性 (Correctness)

### 2.1 [严重] `models.py:295` — `User.id` 使用 `UUID(as_uuid=False)` 返回 `str`，但主键类型不一致

**文件**: `app/database/models.py:13,18,295`  
**问题**:
- `User.id`: `Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)` → 返回 `str`
- `EduCredential.user_id`: `Column(UUID(as_uuid=False), ...)` → 也是 `str`
- `ForeignKey("users.id", ondelete="CASCADE")` 引用 `.id` 字段，类型匹配

但实际上 `UUID(as_uuid=False)` 存储是数据库的 `uuid` 类型，Python 端返回 `str`。问题在于 PostgreSQL 的 UUID 列与 `default=new_uuid()` 函数产生的 `str` 对比没有问题，但：
- SQLAlchemy 内部对 UUID 列的默认处理会期望 `uuid.UUID` 对象
- 如果 `default=new_uuid()` 返回 `str`，而 `as_uuid=False` 是 Python 层映射，两者应当一致（都返回 str）
- 但如果数据库引擎层面有严格的 UUID 类型校验，某些驱动可能报错

**建议**: 
- 统一风格：要么全部 `UUID(as_uuid=True)` + `default=uuid.uuid4`（推荐）
- 要么全部 `UUID(as_uuid=False)` + `default=new_uuid`，确保所有外键引用一致

### 2.2 [严重] `jwt.py:11,21` / `models.py:16` — `datetime.utcnow()` 弃用警告

**文件**: `app/auth/jwt.py:11,12,14,23,24,25` + `app/database/models.py:16`
**问题**: Python 3.12+ 已弃用 `datetime.utcnow()`。使用该函数会收到 `DeprecationWarning`，且返回的 `datetime` 对象不含时区信息（naive datetime），跨时区部署时可能导致 Token 过期判断偏差。

**建议**: 全部替换为:
```python
from datetime import datetime, timezone
datetime.now(timezone.utc)
```
并同步修改 `exp`、`iat`、`created_at`、`updated_at` 等所有时间戳字段。

### 2.3 [中等] `auth.py:76-76` — Token 刷新未验证用户是否仍然有效

**文件**: `app/api/v1/auth.py` → `refresh_token` 端点  
**代码**:
```python
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: TokenRefreshRequest):
    try:
        payload = verify_token(req.refresh_token, expected_type="refresh")
        user_id = payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Refresh Token 无效或已过期")
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
```

**问题**: 
1. 未查询数据库验证用户是否仍然有效（是否被禁用/删除）
2. 用户被管理员禁用后，持有有效 Refresh Token 仍可继续刷新 Access Token

**建议**: 注入 `db` 依赖并查询 `User`，检查 `user.is_active`:
```python
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one_or_none()
if user is None or not user.is_active:
    raise HTTPException(status_code=403, detail="用户不可用")
```

### 2.4 [中等] `auth.py:41-44` — 邮箱唯一性检查存在 TOCTOU

**文件**: `app/api/v1/auth.py:41-44`  
**代码**:
```python
if req.email:
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="邮箱已被使用")
```

**问题**:
1. 先 SELECT 再 INSERT，并发时两个请求同时 SELECT 得到 None，都会 INSERT，导致 `email` 唯一索引（已在模型中定义 `unique=True`）冲突
2. PostgreSQL 最后会抛出 IntegrityError，但错误处理不够优雅

**建议**: 
- 移除 SELECT 预检查，直接依赖数据库唯一约束
- 在 commit 时捕获 `IntegrityError` 并转为 409

### 2.5 [中等] `credentials.py:89` — 解绑 API 使用 404 而非合适的 409/410

**文件**: `app/api/v1/credentials.py:89`  
**代码**: 
```python
if cred is None or not cred.is_valid:
    raise HTTPException(status_code=404, detail="未找到有效凭证")
```

**问题**: 未绑定时业务含义是"资源不存在但之前可能绑定过"。使用 404 可接受，但文档建议区分：
- 从未绑定 → 404  
- 已绑定但已标记无效（软删除）→ 410 Gone 更准确

**建议**: 统一用 404 或区分 410。当前实现中 `cred is None` 和 `not cred.is_valid` 共用一个分支，可以做更精细的区分。

### 2.6 [中等] `models.py:17` — `onupdate=utcnow` 在更新时不会重新计算

**文件**: `app/database/models.py` (所有 `onupdate=utcnow` 字段)  
**代码**:
```python
updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
# where utcnow = lambda: datetime.utcnow()  — 函数定义在 models.py:16
```

**问题**: `onupdate=utcnow` 传入的是 `utcnow` **函数引用**，这写在 `models.py` 中而不是 `session.py` 或混入类中。虽然技术上正确，但 `utcnow` 函数如果在 `models.py` 之外被覆盖或 `from app.database.models import utcnow` 被误用，可能引入风险。

**建议**: 更安全的做法是使用 `func.now()` 或 `text("(now() at time zone 'utc')")`，让数据库维护时间戳而非 Python 层。但当前方式在功能上正确。

### 2.7 [建议] `jwt.py:11` — `create_access_token` `exp` 使用 `timedelta(minutes=...)` 类型正确

**确认**: 无问题。`ACCESS_TOKEN_EXPIRE_MINUTES: int = 30` 配置正确，`timedelta(minutes=30)` 正确。✅

### 2.8 [建议] `models.py:59` — `SyncLog.duration_ms` 的 `nullable=True` 合理

**确认**: 同步任务进行中时 `duration_ms` 为空，完成后再填充，设计合理。✅

---

## 三、性能 (Performance)

### 3.1 [中等] `session.py:8-13` — 连接池配置未考虑 asyncpg 的默认限制

**文件**: `app/database/session.py:8-13`  
**代码**:
```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)
```

**问题**:
- PostgreSQL 的 `max_connections` 默认通常为 100
- `pool_size=20 + max_overflow=10 = 30` 个并发连接
- 如果启动多个 API 副本（K8s/K8s 扩容），总连接数会迅速耗尽数据库连接池
- 未配置 `pool_recycle`（连接最大存活时间），某些 PG 版本在空闲超时后可能断开连接

**建议**:
- 添加 `pool_recycle=3600`（1 小时回收）
- 考虑从环境变量读取 `pool_size`，生产环境设置为数据库 `max_connections` 的 `1/副本数/2`
- 添加 `pool_timeout=30`（等待池连接的超时）

### 3.2 [建议] `models.py:36` — `User.email` 和 `phone` 使用 `unique=True` 但可空

**文件**: `app/database/models.py:36,37`  
**代码**: 
```python
email = Column(String(255), unique=True, nullable=True)
phone = Column(String(20), unique=True, nullable=True)
```

**问题**: PostgreSQL 允许多个 `NULL` 值通过 `unique` 约束（在 PG 中 NULL 不等于 NULL），所以技术上是安全的。但在一些 ORM 或业务代码中，多 `NULL` 的 `unique` 列可能引发混淆。

**建议**: 无紧急问题，但建议添加注释说明 PG 允许 `unique + nullable` 中有多个 NULL。

### 3.3 [建议] `models.py:13` — `UUID(as_uuid=False)` 字符串比较效率低于 UUID 类型

**文件**: `app/database/models.py:13, 37` 等  
**问题**: 使用 `as_uuid=False` 意味着 Python 端拿到的是 `str`，所有 WHERE 比较都是字符串比较。虽然 PostgreSQL 内部仍用 `uuid` 类型存储和索引，但 Python ↔ DB 的编解码开销略高于 `as_uuid=True`。

**建议**: 如果无需在 Python 层处理 UUID 字符串，推荐 `as_uuid=True` + `default=uuid.uuid4`。

### 3.4 [建议] 未使用 `selectinload` / `joinedload` — 但当前尚无 N+1 查询风险

**确认**: 当前 P1 的两个 API 端点（`/me`, `/status`）都只做单表查询，没有关联加载，无 N+1 问题。✅  
但在未来功能扩展时（如遍历用户所有同步日志），需要注意使用 `selectinload`。

---

## 四、代码规范 (Code Style & Convention)

### 4.1 [中等] `models.py:296` — `AgentSession` 位于教务数据表区域，但有 13 张表的注释

**文件**: `app/database/models.py:296`  
**问题**: 类顶注释写 `# 教务数据表 (13张)`，但实际只有 12 张教务表 + 1 张 `AgentSession` = 13 张。注释混乱：
- `# 新增表 (3张)` → User, EduCredential, SyncLog ✅
- `# 教务数据表 (13张)` → 实际 12 张教务 + 1 张 AgentSession，共 13 张

**建议**: 修正注释为 `# 教务数据表 + Agent会话 (共13张)` 或精确统计。

### 4.2 [中等] `schemas.py:34` — `BindCredentialRequest` 中的 `base_url` 字段命名歧义

**文件**: `app/auth/schemas.py:54`  
**代码**: 
```python
base_url: str = Field("https://jwglxt.buct.edu.cn", description="教务系统地址")
```

**问题**: 字段名 `base_url` 过于通用，全局可能有多个 `base_url` 概念。在配置文件中已使用 `EDU_BASE_URL`，与 API 模型命名不一致。

**建议**: 改名为 `edu_base_url` 以保持一致性。

### 4.3 [建议] `auth.py` 中 `me` 端点路径应为 `/me` 但前缀会导致 `/api/v1/auth/me`

**文件**: `app/api/v1/auth.py`  
**确认路径**: 
- `__init__.py`: `v1_router = APIRouter(prefix="/v1")` 
- `auth.py` 路由: `router = APIRouter()` + `v1_router.include_router(auth_router, prefix="/auth")`
- 最终路径: `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/v1/auth/me`

**问题**: `/me` 挂载在 `/auth` 下，语义上 `/api/v1/auth/me` 表示"当前认证用户的认证信息"，逻辑正确但路径略显冗余。部分 RESTful 风格更偏好 `/api/v1/users/me`。

**建议**: 保留当前方案（业务逻辑上合理），未来如需用户管理端点可以考虑拆分。

### 4.4 [建议] `security.py:10` — Fernet 实例建议有生命周期管理

**文件**: `app/auth/security.py:10`  
**代码**:
```python
_fernet = Fernet(settings.CREDENTIAL_ENCRYPTION_KEY.encode())
```

**问题**: 模块级单例 `_fernet` 在模块导入时初始化。如果配置热重载或测试场景下更换密钥，不会自动更新。

**建议**: 考虑封装在类中或提供 `get_fernet()` 函数，以便在密钥轮换场景下使用。

### 4.5 [建议] `credentials.py:9` — `router` 无 `prefix` 一致性问题

**文件**: `app/api/v1/credentials.py` vs `auth.py`  
**代码**:
```python
# credentials.py
router = APIRouter()
# auth.py
router = APIRouter()
```

**问题**: 两者都在 `__init__.py` 中被 `include_router(..., prefix="/...")` 指定前缀，风格一致 ✅。

### 4.6 [建议] 类型注解一致性 — `get_current_user` 返回 `User` ORM 实例

**文件**: `app/auth/dependencies.py:39`  
**确认**: 返回类型声明为 `-> User`，实际返回 SQLAlchemy ORM 对象。在 `auth.py` 的 `get_me` 中注入后直接访问 `.id`, `.username` 等属性。✅  
但在 `<schemas>.UserResponse` 中的 `model_config = {"from_attributes": True}` 支持 ORM 到 Pydantic 转换。✅

---

## 五、配置与基础设施

### 5.1 [中等] `Dockerfile:9` — 缺少 `.env` 文件处理

**文件**: `Dockerfile`  
**问题**: 
```
COPY app/ ./app/
```
但 `.env` 文件需要外部挂载或通过 docker-compose 的 `env_file` 注入。当前代码未处理。

**确认**: docker-compose.yml:46 `env_file: .env` 已正确处理 ✅。

### 5.2 [中等] `nginx/nginx.conf:10-11` — 证书路径未挂载

**文件**: `nginx/nginx.conf:23-24`  
**代码**:
```nginx
ssl_certificate     /etc/nginx/ssl/server.crt;
ssl_certificate_key /etc/nginx/ssl/server.key;
```

**问题**: docker-compose.yml 中 nginx 服务的 `volumes` 仅挂载了 `./nginx/nginx.conf:/etc/nginx/nginx.conf:ro`，**没有挂载 SSL 证书**。Nginx 启动后检查 SSL 配置时会报错并拒绝启动。

**建议**: 在 `docker-compose.yml` 中添加证书卷挂载:
```yaml
volumes:
  - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
  - ./ssl:/etc/nginx/ssl:ro
```

### 5.3 [建议] `docker-compose.yml:44` — API 服务缺少健康检查

**文件**: `docker-compose.yml:42-47` (api 服务)  
**问题**: 虽然 `main.py` 提供了 `/health` 端点，但 docker-compose 中未配置 `healthcheck`。

**建议**: 添加:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

## 六、总结

### 必须修复 (Severity: 🔴 Critical — 4 项)

| # | 文件 | 行号 | 说明 |
|---|------|------|------|
| 1 | `config.py` | 27,36,42 | 默认密钥 `"change_me"` 生产环境危险 |
| 2 | `security.py` | 10 | Fernet 密钥必须是 32 字节 Base64 编码，直接 `.encode("change_me")` 必定崩溃 |
| 3 | `jwt.py` | 11,21 | `datetime.utcnow()` 已弃用，应使用 `datetime.now(timezone.utc)` |
| 4 | `auth.py` /me 端点 | 76 | Token 刷新未验证用户有效性（禁用/删除用户可无限刷新） |

### 建议尽快修复 (Severity: 🟡 Medium — 9 项)

| # | 文件 | 行号 | 说明 |
|---|------|------|------|
| 5 | `config.py` | 2 | 建议 JWT 切换到 RS256 非对称签名 |
| 6 | `config.py` | 11 | CORS `*` 在生产环境应当受限 |
| 7 | `dependencies.py` | 22 | `except Exception` 过于宽泛，应只捕获 `JWTError` |
| 8 | `auth.py` | 41 | 邮箱唯一性预检查有 TOCTOU 问题，应依赖 DB 约束 |
| 9 | `credentials.py` | 89 | 解绑时 404/410 区分可以更精细 |
| 10 | `session.py` | 8 | 连接池缺少 `pool_recycle` 和可配置化 |
| 11 | `nginx.conf` | 23 | SSL 证书未在 docker-compose 中挂载，Nginx 会拒绝启动 |
| 12 | `models.py` | 注释 | 表计数注释不准确（13 → 实际 16 表但注释说 13） |
| 13 | `main.py` | 1 | 缺少 `app/api/v1/__init__.py` 的路由加载完整性检查 |

### 代码亮点 ✨

- **分离清晰的 JWT token type** — `access` vs `refresh` 在 payload 中区分，`verify_token` 校验 type ✅
- **ORM 参数化查询** — 全部使用 SQLAlchemy `select()` 构造，无原始 SQL，杜绝 SQL 注入 ✅
- **多用户数据隔离** — 13 张教务表全部增加 `user_id` 外键，查询条件包含 `user_id` ✅
- **合理的索引设计** — `idx_synclog_user_module`, `idx_course_user_wd` 等复合索引覆盖了常用查询条件 ✅
- **bcrypt 密码哈希** — 使用 passlib + bcrypt，配置正确 ✅
- **凭证软删除** — 解绑不删历史数据，仅设 `is_valid=False` ✅
- **CASCADE 外键** — `ondelete="CASCADE"` 确保删除用户时级联清理相关数据 ✅

---

*审查结束。以上发现全部基于只读代码分析，未执行任何代码修改。*
