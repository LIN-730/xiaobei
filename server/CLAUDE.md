# 教务智能助手（小北）— 后端 CLAUDE.md

> **⚡ 新会话第一件事：任务分解 → 派发 OpenClaw 并行任务。不要自己全干完再想起来。**

## 🔺 产品定位（影响所有技术决策）

**目标产品**: React Native 移动端 App → Apple App Store / Google Play 上架
**用户群体**: 北京化工大学在校学生（万人级）
**后端职责**: 为移动端提供全部 API，包括认证/教务数据/AI对话/学业规划

### 🔺 原型参考：D:\buct-edu-web

**原型是功能蓝图，不是实现标准。** 开发时：
- ✅ 原型有的功能 → 移动端必须有（API/Screen/Tool），不可遗漏
- ✅ 原型的设计/实现不好 → 自行升级优化，不需要照搬
- ✅ 原型不合理的地方 → 直接去掉或替换为更好的方案
- ✅ 原型没有但移动端需要 → 自行设计添加

**每次新 Phase 开始前，先查原型对应功能，确保不遗漏、不盲目照搬。**

### 🔺 BUCT 教务系统领域知识（禁止随意修改）

以下模块包含对**北化正方 V9.0 教务系统**的深度逆向知识，**修改必须谨慎**：

| 模块 | 知识内容 | 修改风险 |
|------|----------|----------|
| `crawlers/` | 17 个爬虫的 GNMKDM 代码、URL 路径、RSA 加密、JS 正则提取、AJAX 拦截 | 🔴 爬虫会失效 |
| `agent/edu_knowledge.py` | 38 个模块位置 + 24 条 FAQ + xqm 编码 | 🟡 AI 回答不准 |
| `agent/user_profile.py` | 学期推算 (9月→xqm=3, 2月→xqm=12, 7月→xqm=16) | 🔴 数据查询错学期 |
| `knowledge/classifier.py` | 7 分类 + 关键词体系（含北化课程名称正则） | 🟡 文档分类错误 |
| `agent/tools/edu_guide_tool.py` | 24 条教务操作指南（选课/缓考/补考/评教时间窗口等） | 🟡 AI 指引不准 |

**规则**：
- 🚫 **不得修改** GNMKDM 代码、URL 路径、RSA 加密逻辑
- 🚫 **不得删除** edu_knowledge.py 中的任何条目
- 🚫 **不得修改** 学期推算中的月份→xqm 映射
- ✅ 可以升级架构（同步→异步、参数化）、改进代码质量、补充注释
- ✅ 发现教务系统变动（北化升级系统）时及时更新上述模块

### 移动端对后端的强制要求（所有 Phase 必须遵守）

| 要求 | 后端实现 |
|------|----------|
| **消息持久化** | 服务端存全部对话历史（换手机/重装可恢复） |
| **SSE 可靠性** | 心跳保活(30s) + `id`字段 + `Last-Event-ID` 断线重连 |
| **多设备同步** | 同一用户多设备共享会话列表和消息 |
| **响应精简** | 避免冗余字段，列表接口分页，移动流量敏感 |
| **Token 静默刷新** | access(30min)+refresh(7d)，客户端无感续期 |
| **后台同步** | Celery 异步爬取，完成后客户端拉取最新数据 |
| **错误处理** | 所有端点返回明确的状态码和错误信息，不暴露内部细节 |

## 项目目标
北京化工大学教务系统智能助手（小北）— 应用市场上线级移动端后端：
1. 多用户注册/登录，教务凭证绑定（AES-256-GCM 加密）
2. 全维度教务数据爬取与智能查询（课表/成绩/考试/培养方案/学业预警等）
3. 文件上传 → 分类 → 向量化 → RAG 知识库检索
4. AI 对话（SSE 流式，移动网络韧性）+ 学业规划引擎
5. React Native 客户端 API（iOS + Android 双端）

## 核心约束（绝对不能违反）
- **绝对禁止**任何写操作（选课/退课/重修/信息修改/评教/奖学金/缓考等）
- 所有爬虫和 Agent 工具只能做**只读查询**
- **不做任何兜底/fallback**，有问题直接暴露追根究底
- 多用户数据严格隔离（user_id FK + Repository 自动过滤）
- **移动端流量敏感**：响应紧凑、分页必做、不返回冗余数据

## 技术栈
- Web: FastAPI 0.115 + Uvicorn + Gunicorn
- DB: PostgreSQL 16 + SQLAlchemy 2.0 (async) + Alembic（替代原 SQLite）
- Cache: Redis 7（Session 缓存 + Celery Broker）
- Auth: JWT (python-jose) + bcrypt (passlib) + AES-256-GCM (cryptography/Fernet)
- AI: LangChain 0.3 + LangGraph + 豆包 API (OpenAI 兼容)
- 爬虫: Requests + BeautifulSoup + Playwright（100% 复用原项目）
- 文档解析: PyMuPDF + python-docx + openpyxl
- 部署: Docker Compose + Nginx

## 目录结构
```
edu-assistant-server/
├── app/
│   ├── main.py                # FastAPI 入口
│   ├── config.py              # 环境变量配置 (pydantic-settings)
│   ├── database/
│   │   ├── session.py         # asyncpg 连接池
│   │   ├── models.py          # SQLAlchemy ORM (18表: 3用户 + 13教务 + 2Agent)
│   │   └── repositories/      # 数据访问层 (15个Repo, 自动 user_id 隔离)
│   ├── api/v1/
│   │   ├── auth.py            # 注册/登录/刷新Token
│   │   ├── credentials.py     # 教务凭证绑定/管理
│   │   ├── courses.py         # 课表
│   │   ├── scores.py          # 成绩
│   │   ├── exams.py           # 考试
│   │   ├── dashboard.py       # 仪表盘聚合
│   │   ├── agent.py           # AI对话 (SSE流式 + 会话管理)
│   │   ├── planning.py        # 学业规划 (4端点)
│   │   └── sync.py            # 同步触发/状态
│   ├── auth/
│   │   ├── jwt.py             # JWT 生成/验证
│   │   ├── security.py        # bcrypt + AES凭证加密
│   │   ├── schemas.py         # Pydantic 请求/响应模型
│   │   └── dependencies.py    # FastAPI 依赖注入 (get_current_user)
│   ├── agent/
│   │   ├── schemas.py         # Agent请求/响应 + SSE事件模型
│   │   ├── planning_engine.py # 学业规划引擎 (async Repository)
│   │   ├── agent_manager.py   # per-user AgentExecutor 池 (30min TTL)
│   │   ├── user_profile.py    # 学期推算 (无DB依赖)
│   │   ├── edu_knowledge.py   # 教务系统知识库
│   │   └── tools/             # 17个Agent Tool (异步 + Repository)
│   ├── knowledge/             # RAG 知识库 (ChromaDB多租户)
│   │   ├── vectordb.py        # 向量存储 (per-user collection)
│   │   ├── rag.py             # 检索增强生成
│   │   ├── parser.py          # 文档解析
│   │   └── classifier.py      # 文档分类
│   ├── crawlers/              # 14个爬虫 (100%复用)
│   └── sync/                  # Celery异步同步
├── alembic/                   # 数据库迁移
├── nginx/nginx.conf
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── .gitignore
```

## 代码来源

| 模块 | 来源 | 改造程度 |
|------|------|----------|
| crawlers/ (14个爬虫) | D:\buct-edu-web\crawlers\ | 100%复用 |
| agent/tools/ (17个Tool) | D:\buct-edu-web\tools\ | SQLite→async Repository |
| knowledge/ (RAG) | D:\buct-edu-web\knowledge\ | +多租户隔离 |
| sync/ (Celery) | 原项目 scheduler.py | 单Session→池 |

---

## 🔺 Claude Code + OpenClaw 三Agent协作体系（永久框架）

> **核心原则：一任务一会话。任务完成 → 会话结束 → 新任务新会话。保持上下文清洁健康。**
> 每个新会话、每个新 Phase 开始时必须执行此框架。

### Agent 矩阵

| Agent | 角色 | 模型 | 会话命名 | Owns |
|-------|------|------|----------|------|
| **Claude Code** | Architect | Opus/Pro | — | 架构/核心代码/DB/Auth/复杂重构/集成 |
| **edu-config** | Config Worker | Haiku级 | `agent:edu-config:{phase}-{task}` | Docker/Nginx/.env/CI/纯复制/静态文件 |
| **edu-review** | Reviewer | Sonnet级 | `agent:edu-review:{phase}-{round}` | 只读审查（正确性/安全/性能/规范/异步） |

### 会话策略：一任务一会话

每个 Phase 按任务粒度拆分 session key：
```
agent:edu-config:{phase}-{task}     ← 如 p4-docker, p4-static-files
agent:edu-review:{phase}-round{N}   ← 如 p4-round1, p4-final
```

**规则**：
| 原则 | 说明 |
|------|------|
| **一任务一会话** | 每派发一个独立任务 → 新建 session key |
| **任务粒度** | 任务 = 一组相关文件改动（如"创建 knowledge/ 下 4 个文件"） |
| **任务内可多轮** | 同一任务内的 review-fix 循环共享会话 |
| **完成后归档** | 任务完成即结束会话，不销毁（审计追溯） |
| **上下文预算** | OpenClaw 200K 自动管理。按任务拆分天然不会超标 |

### Phase 协作流程（6 步）

```
Phase 开始
│
├── ① [Claude] 任务分解
│     输出: 任务列表 {🔴核心 🟢可并行 🔵审查}
│     为每个🟢任务定义 session key
│
├── ② [并行推进] 全 Phase 持续:
│     ┌───────────────────────────────────────────────┐
│     │ Claude Code       │ edu-config   │ edu-review │
│     │ 🔴逐批实现         │ 🟢收到任务    │ 🔵收到审查  │
│     │ 每批 commit        │ 创建文件→完成 │ 逐文件检查  │
│     │                   │ →会话结束     │ →报告→结束  │
│     └───────────────────────────────────────────────┘
│     每完成一个🟢任务 = 新会话做下一个🟢任务
│
├── ③ [集成] Claude Code 审查 edu-config 产物:
│     逐文件校验(命名/导入/风格) → 修正 → merge → commit
│
├── ④ [审查] edu-review 审查 Claude 变更:
│     新会话: agent:edu-review:{phase}-round{N}
│     Claude 处理发现 → 修复 → 同会话内确认
│
├── ⑤ [终审] 全部修复后，新会话做最终审查:
│     agent:edu-review:{phase}-final
│
└── ⑥ [验证] 语法检查 → docker compose up → curl → commit
```

### 派发方式

```bash
# 1. 派发独立任务（同步，等结果）
openclaw agent --agent edu-config \
  --session-key agent:edu-config:{phase}-{task} \
  --message "任务: <具体任务描述>" \
  --json --timeout 120

# 2. 审查任务
openclaw agent --agent edu-review \
  --session-key agent:edu-review:{phase}-round{N} \
  --message "审查: <文件列表>. 检查: 正确性/安全/性能/异步/命名" \
  --json --timeout 120
```

### Fallback: OpenClaw 不可用时

如果 CLI/Gateway 不可用，用 Agent tool 替代（同职责、同模型）：
```
Agent(subagent_type="general-purpose", model="haiku",
      prompt="你是 edu-config。<任务描述>")
```

---

## 工作规则（复用自原项目 + 新增协作规则）

### 三阶工作流（不得跳过）
1. **Explore** — 派 Explore agent (model=haiku) 做只读探索，从子目录启动
2. **Plan** — 派 Plan agent (默认模型) 设计方案，人工确认后执行
3. **Implement** — 按方案逐步实现，每批改动后立即 CLI 验证

> **⚡ 进入 Implement 前必做：分解任务，把可并行的（Docker/复制/配置/静态文件）立刻派给 edu-config，不要自己全干。**

### 模型分层（新增 OpenClaw 协作）
| 任务 | Agent | 模型 |
|------|-------|------|
| 架构设计/方案 | Claude Code (主) | Pro/Opus |
| 核心代码实现 | Claude Code (主) | Pro |
| Docker/Nginx/配置 | OpenClaw edu-config | Haiku |
| 代码审查 | OpenClaw edu-review | Sonnet |
| 代码探索/搜索 | Explore sub-agent | Haiku |
| 独立子任务 | general-purpose | Haiku |

### 并行与批量
- **🔺 实现前先分解：可并行的立刻 `openclaw agent --agent edu-config` 派发，不要等**
- 独立探索任务：同时派多个 Explore agent，互不阻塞
- 独立配置任务：派发 OpenClaw edu-config，与核心开发并行
- 同类型独立改动：批量并行 Edit，减少往返
- 改完立即 `python -c "from app.xxx import yyy"` 验证

### 上下文管理
- 探索代码从子目录启动，让上下文聚焦
- 不重复读取同一文件（Read 结果在上下文中直接复用）
- 跳过噪音文件：`__pycache__/`、`build/`、`dist/`、`*.spec`、`*.pyc`
- 代码审查结果不读全文，只看摘要后决定是否深入

### 会话拆分
- 每个 Phase 完成时更新 TASK_STATUS.md，下一个会话可无缝衔接
- 上下文达 ~25万 token 时主动提醒用户切换（留缓冲）
- **切换前必须完成**（缺一不可）：
  1. 将当前进度写入 `TASK_STATUS.md`（D:\xiaobei\server\），包含：已完成工作、已修改文件、下一步、注意事项、新会话需读取的最少文件
  2. 确保所有改动已 git commit
  3. 告诉用户新会话只需说"继续"即可衔接
- 如果用户选择继续，尊重选择，后续适当节点再次提醒

### 其他
- 不改不相关文件，不做过度抽象
- 文件操作在 D:\xiaobei\server\
- 每完成一批改动就 commit
