# 教务智能助手（小北）— 部署指南

## 环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Docker | 24.0+ | 含 Docker Compose v2 |
| CPU | 2 核+ | 建议 4 核 |
| 内存 | 4 GB+ | 建议 8 GB（含 ChromaDB） |
| 磁盘 | 20 GB+ | PostgreSQL + ChromaDB 数据持久化 |
| 域名 | 1 个 | 用于 HTTPS（可选） |

## 快速开始（开发/测试）

```bash
# 1. 克隆项目
git clone <repo-url> edu-assistant-server
cd edu-assistant-server

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，至少设置 DOUBAO_DEFAULT_API_KEY

# 3. 启动所有服务
docker compose up -d

# 4. 检查健康状态
curl http://localhost:8000/health
# → {"status":"ok","app":"教务智能助手"}

# 5. 查看日志
docker compose logs -f api
```

## 生产部署

### 1. 环境变量配置

```bash
cp .env.production .env
# 编辑 .env，修改以下必填项：
# - POSTGRES_PASSWORD (强随机密码)
# - JWT_SECRET_KEY (强随机密钥)
# - CREDENTIAL_ENCRYPTION_KEY (Fernet 密钥)
# - DOUBAO_DEFAULT_API_KEY (豆包 API Key)
# - CORS_ORIGINS (限制为你的域名)
```

生成强密钥：
```bash
# PostgreSQL 密码
openssl rand -base64 32

# JWT 密钥
openssl rand -base64 64

# Fernet 加密密钥
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. SSL 证书（生产必需）

**方案 A: Let's Encrypt（推荐）**
```bash
# 安装 certbot
apt install certbot python3-certbot-nginx

# 获取证书
certbot certonly --standalone -d your-domain.com

# 复制证书到 ssl/ 目录
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/server.crt
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/server.key

# 取消 nginx/nginx.conf 中 HTTPS server 块的注释
# 重启 nginx
docker compose restart nginx
```

**方案 B: 自签名证书（仅测试）**
```bash
bash scripts/generate_self_signed_cert.sh
```

### 3. 安全加固

编辑 `docker-compose.yml`，生产环境移除不必要的端口暴露：

```yaml
# postgres — 移除 ports 映射（仅内部访问）
# redis — 移除 ports 映射（仅内部访问）
# api — 移除 ports 映射（仅 nginx 代理）
```

或使用注释标记的生产配置段。

### 4. 启动

```bash
docker compose up -d
```

### 5. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# 全服务状态
docker compose ps
# 所有服务应为 Up / healthy

# API 可用性
curl http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test1234"}'
```

## 服务架构

```
                   ┌──────────┐
                   │  Nginx   │ :80/:443
                   └────┬─────┘
                        │ /api/* → api:8000
                   ┌────▼─────┐
                   │   API    │ :8000 (FastAPI)
                   └─┬──┬──┬─┘
                     │  │  └──────────────┐
              ┌──────▼┐ │             ┌───▼──────┐
              │PostgreSQL│ │             │ChromaDB │ :8001
              │  :5432  │ │             └──────────┘
              └─────────┘ │
                    ┌─────▼──────┐
                    │   Redis    │ :6379
                    └─────┬──────┘
                          │
              ┌───────────▼──────────┐
              │ Celery Worker + Beat │
              └──────────────────────┘
```

## 数据库迁移

```bash
# 生成迁移（models.py 变更后）
docker compose exec api alembic revision --autogenerate -m "describe_change"

# 执行迁移
docker compose exec api alembic upgrade head

# 回滚
docker compose exec api alembic downgrade -1
```

## 常用运维命令

```bash
# 查看日志
docker compose logs -f --tail=100 api

# 重启单个服务
docker compose restart api

# 进入容器调试
docker compose exec api bash

# 数据库备份
docker compose exec postgres pg_dump -U edu_user edu_assistant > backup.sql

# 数据库恢复
docker compose exec -T postgres psql -U edu_user edu_assistant < backup.sql

# 清理并重建（⚠️ 数据丢失）
docker compose down -v
docker compose up -d
```

## 故障排查

### API 容器无法启动
```bash
docker compose logs api
# 常见: .env 配置缺失 / 数据库连接失败
```

### Celery Worker 无法启动
```bash
docker compose logs celery-worker
# 常见: Redis 未就绪 / 缺少 celery 包
docker compose restart celery-worker
```

### Nginx 无法启动
```bash
docker compose logs nginx
# 常见: ssl/server.crt 缺失（开发环境注释 HTTPS 块）
```

### ChromaDB 持久化失败
```bash
# 确认挂载卷权限
docker compose exec chromadb ls -la /chroma/chroma
```

## 监控建议

- 配置 Uptime Robot/Prometheus 监控 `/health` 端点
- 设置 PostgreSQL 连接数告警（默认 pool_size=20）
- 监控磁盘空间（ChromaDB 向量数据持续增长）
- 配置日志轮转（docker 默认日志驱动可能占满磁盘）
