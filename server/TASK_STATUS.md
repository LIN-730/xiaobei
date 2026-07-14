# TASK_STATUS.md — 教务智能助手 后端

> 最后更新: 2026-06-15 | P6 ✅ 完成 | 模拟器 GUI + App 已交付用户

## 新会话启动指令
```
继续。先读 CLAUDE.md、TASK_STATUS.md。
当前状态: 用户正在模拟器 GUI 上体验 App，后端 Docker 全栈运行中。
下一步: 根据用户反馈修复问题 / 优化体验。
```

---

## 🔴 当前上下文 (下次会话重要) — 2026-06-15

### 运行状态
- **后端**: Docker Compose 全栈运行中 (edu-api/nginx/postgres/redis/chromadb/celery)
- **Metro bundler**: 端口 8081 运行中
- **Android 模拟器**: `pixel_api36_a` (pixel 设备 + android-36.1 + x86_64 + WHPX) — GUI 模式 ✅
- **App**: `com.buct.xiaobei` 已安装并运行 ✅
- **ADB 端口转发**: tcp:8000 (API) + tcp:8081 (Metro)
- **模拟器启动命令** (带 GUI，无头模式加 `-no-window`):
  ```
  $env:ANDROID_SDK_ROOT = "$env:LOCALAPPDATA\Android\Sdk"
  emulator -avd pixel_api36_a -no-snapshot -gpu swiftshader_indirect
  ```

### 已解决：Gradle 构建问题 ✅

**问题1**: `JvmVendorSpec IBM_SEMERU` — Gradle 9.3.1 不识别 IBM Semeru/JBR vendor
- **解决方案**: 下载 Eclipse Temurin JDK 17 到 `D:\Java\jdk17\jdk-17.0.19+10`
- **JAVA_HOME**: `D:\Java\jdk17\jdk-17.0.19+10`

**问题2**: Google Maven 仓库被墙 (dl.google.com 连接超时)
- **解决方案**:
  1. 全局 Gradle init 脚本: `~/.gradle/init.d/aliyun-mirrors.gradle` (阿里云镜像)
  2. `android/build.gradle` 添加阿里云 mirror repositories
  3. `android/gradle.properties` 禁用 JVM auto-detect + 指定 JDK 路径

**构建结果**: BUILD SUCCESSFUL in 23m 23s, 319 tasks

### 新增/修改文件

**系统环境**:
- `D:\Java\jdk17\jdk-17.0.19+10` — Eclipse Temurin JDK 17
- `~/.gradle/init.d/aliyun-mirrors.gradle` — 全局阿里云镜像配置

**App 项目 (D:\xiaobei\app\)**:
- `android/gradle.properties` — +JVM auto-detect=false + JDK路径
- `android/build.gradle` — +阿里云 mirror repositories

### API 验证结果 (2026-06-15)
| 端点 | 结果 |
|------|------|
| GET /health | ✅ `{"status":"ok"}` |
| POST /api/v1/auth/register | ✅ 注册+直接返回token |
| POST /api/v1/auth/login | ✅ 登录成功 |
| GET /api/v1/agent/sessions | ✅ 200 (空列表) |
| GET /api/v1/dashboard | ✅ 200 (默认数据) |
| GET /api/v1/courses | ✅ 200 (空列表) |

### 下次继续
1. 根据用户实际体验反馈修复问题
2. 注册/登录 → 绑定教务凭证 → 触发同步（如用户尚未完成）
3. 测试 AI 对话（需配置 DOUBAO_DEFAULT_API_KEY）
4. 收集 UI/UX 问题 → 修复 → 迭代

---

## 项目结构 (当前)

```
D:\xiaobei\
├── server\              ← FastAPI 后端 (本项目, git repo)
│   ├── app/
│   │   ├── main.py      ← FastAPI 入口
│   │   ├── config.py    ← 环境变量
│   │   ├── database/    ← models(18表) + repositories(15) + session
│   │   ├── api/v1/      ← auth/credentials/courses/scores/exams/dashboard/sync/agent/planning
│   │   ├── auth/        ← jwt/security/schemas/dependencies
│   │   ├── crawlers/    ← 14个爬虫
│   │   ├── sync/        ← Celery + session_pool
│   │   ├── agent/       ← agent_manager + planning_engine + schemas + tools(9文件)
│   │   └── knowledge/   ← vectordb/rag/parser/classifier (多租户)
│   ├── tests/
│   ├── alembic/
│   ├── nginx/  ssl/
│   ├── docker-compose.yml  Dockerfile  requirements.txt
│   └── CLAUDE.md  TASK_STATUS.md
```

---

## P3 完成情况

| Step | 内容 | 状态 |
|------|------|------|
| 1 | `models.py` +AgentMessage 表 | ✅ |
| 2 | `repos.py` +AgentSessionRepo +AgentMessageRepo | ✅ |
| 3 | `app/agent/schemas.py` 新建 | ✅ |
| 4 | `app/agent/planning_engine.py` 异步重构 | ✅ |
| 5 | `knowledge/` 包复制+多租户 (edu-config) | ✅ |
| 6 | 14核心Tool + 3静态Tool + 工厂 (Claude + edu-config) | ✅ |
| 7 | `app/agent/agent_manager.py` (per-user池) | ✅ |
| 8 | `app/api/v1/agent.py` (SSE聊天+会话管理) | ✅ |
| 9 | `app/api/v1/planning.py` (4规划端点) | ✅ |
| 10 | docker-compose chromadb (edu-config) | ✅ |
| 11 | edu-review 审查 | ⬜ (跳过) |
| 12 | 集成验证 (docker compose + curl) | ✅ 8/8 通过 |

---

## 新增文件清单

### Claude 创建
- `app/agent/schemas.py` — Pydantic 请求/响应 + SSEEvent
- `app/agent/planning_engine.py` — SQLite→async Repository (500行)
- `app/agent/agent_manager.py` — per-user AgentExecutor 池 (30min TTL)
- `app/agent/tools/course_tools.py` — 课表查询
- `app/agent/tools/score_tools.py` — 成绩查询
- `app/agent/tools/exam_tools.py` — 考试查询
- `app/agent/tools/student_tools.py` — 学生信息/学业/预警 (3 tools)
- `app/agent/tools/training_tools.py` — 培养方案/选课/教室 (3 tools)
- `app/agent/tools/planning_tools.py` — 学业规划 (4 tools)
- `app/agent/tools/knowledge_tools.py` — RAG知识库 (2 tools, 工厂模式)
- `app/agent/tools/__init__.py` — Tool 工厂
- `app/api/v1/agent.py` — SSE流式对话 + 会话CRUD
- `app/api/v1/planning.py` — 4规划端点

### edu-config 创建
- `app/agent/tools/edu_guide_tool.py` — 教务指南搜索 (纯静态)
- `app/agent/tools/notification_tools.py` — 通知搜索
- `app/knowledge/__init__.py` — 知识库包
- `app/knowledge/classifier.py` — 文档分类器
- `app/knowledge/parser.py` — 文档解析器
- `app/knowledge/vectordb.py` — ChromaDB 向量存储 (多租户)
- `app/knowledge/rag.py` — RAG 检索管理器 (多租户)

### 修改文件
- `app/database/models.py` — +AgentMessage 表
- `app/database/repositories/repos.py` — +AgentSessionRepo +AgentMessageRepo
- `app/api/v1/__init__.py` — +agent +planning 路由
- `docker-compose.yml` — +chromadb 服务
- `.env.example` — +CHROMADB 配置

---

## 集成测试结果 (2026-06-13)

| 端点 | 方法 | 结果 | 说明 |
|------|------|------|------|
| `/api/v1/agent/sessions` | GET | ✅ | 会话列表正常 |
| `/api/v1/agent/chat` | POST | ✅ | SSE流式框架正常，会话自动创建，消息持久化 |
| `/api/v1/agent/sessions/{key}/messages` | GET | ✅ | 消息历史分页正常 (event_id, role, content) |
| `/api/v1/agent/sessions/{key}` | DELETE | ✅ | 会话+消息级联删除正常 |
| `/api/v1/planning/credit-gap` | GET | ✅ | 返回200 (数据依赖同步) |
| `/api/v1/planning/required-courses` | GET | ✅ | 返回200 |
| `/api/v1/planning/recommend` | GET | ✅ | 返回200 |
| `/api/v1/planning/path` | GET | ✅ | 返回200 |

**注意**: SSE 聊天完整响应需配置 `DOUBAO_DEFAULT_API_KEY` 环境变量。

### 已知问题
- Celery worker/beat 容器启动失败（`celery` 可执行文件未在 PATH）— 需检查 Dockerfile
- ChromaDB 镜像拉取需国内镜像源（`docker.m.daocloud.io`）

---

## P4 React Native 前端

> 项目位置: `D:\xiaobei\app\` (独立 git repo)

### P4.1 完成情况 ✅

| Step | 内容 | 状态 |
|------|------|------|
| 1 | Expo SDK 56 项目初始化 + 49 依赖安装 | ✅ |
| 2 | NativeWind v4 + Tailwind CSS 配置 | ✅ |
| 3 | TypeScript 类型定义 (8 文件) | ✅ |
| 4 | API 层: Axios 实例 + TokenManager + 401 刷新队列 | ✅ |
| 5 | 基础 UI 组件 (Button/Input/Card/Loading/EmptyState) | ✅ |
| 6 | Zustand authStore + chatStore | ✅ |
| 7 | 导航: AuthStack + MainTabs(5Tab) + RootNavigator | ✅ |
| 8 | LoginScreen + RegisterScreen (React Hook Form + Zod) | ✅ |
| 9 | HomeScreen 仪表盘 (KPI 卡片 + 学业进度) | ✅ |
| 10 | SettingsScreen 设置页 + 登出 | ✅ |
| 11 | 13 个 API 服务文件覆盖全部后端端点 | ✅ |
| 12 | edu-review 审查 + 阻断/高风险修复 | ✅ |
| 13 | TypeScript 编译零错误 | ✅ |

### P4.1 审查修复记录
- **阻断**: Token 初始化网络异常误删凭证 → 仅 401 才清除
- **阻断**: 刷新队列请求永久挂起 → resolve/reject 双回调
- **高风险**: localStorage Token 明文存储 → 移除 Web fallback
- **高风险**: atob 不兼容 Hermes → 自实现 base64 解码
- **高风险**: 刷新请求无超时 → 独立 10s 超时
- **高风险**: 规划模块无类型 → 定义 7 个 interface

### P4.1 新增文件 (49个)
```
D:\xiaobei\app\
├── App.tsx, app.json, package.json, tsconfig.json
├── global.css, tailwind.config.js, metro.config.js
└── src/
    ├── api/ (11 文件)
    ├── app/ (3 导航)
    ├── components/ui/ (5 组件)
    ├── screens/ (7 页面 + 4 占位)
    ├── stores/ (2 Zustand)
    ├── types/ (9 类型 + 2 .d.ts)
    └── utils/ (3 工具)
```

### 下一步 P4.2 → ✅ 已完成

---

## P4.2 完成情况 ✅

| Step | 内容 | 状态 |
|------|------|------|
| 0 | 排查 + 修正凭空编造数据 (NODE_TIMES + SSEEventType) | ✅ |
| 1 | `types/course.ts` + CourseColor + getCourseColor() | ✅ |
| 2 | `components/sync/SyncBanner.tsx` 同步状态横幅 | ✅ |
| 3 | `screens/courses/CourseDetailScreen.tsx` 课程详情 | ✅ |
| 4 | `screens/courses/ScheduleScreen.tsx` 课表周视图 | ✅ |
| 5 | `app/MainTabs.tsx` ScheduleTab → Stack Navigator | ✅ |
| 6 | `screens/home/HomeScreen.tsx` 引入 SyncBanner | ✅ |
| 7 | TypeScript 编译验证 | ✅ 零错误 |

### P4.2 新增文件
- `src/components/sync/SyncBanner.tsx` — 同步横幅（4 状态 + 2s 轮询 + 3s 自动消失）
- `src/screens/courses/CourseDetailScreen.tsx` — 课程详情卡片

### P4.2 修改文件
- `src/types/course.ts` — +CourseColor + getCourseColor() + 修正 NODE_TIMES (北化官方13节)
- `src/types/chat.ts` — +heartbeat SSE 事件类型
- `src/screens/courses/ScheduleScreen.tsx` — 完整重写（6列×13行网格 + 手势滑动 + 重叠检测）
- `src/app/MainTabs.tsx` — ScheduleTab Stack Navigator
- `src/screens/home/HomeScreen.tsx` — +SyncBanner

### 排查结果（凭空编造数据修正）
- **NODE_TIMES**: 原12节→13节，第4节起全部时间错误，已修正为北化官方作息表
- **SSEEventType**: 漏了 `heartbeat` 类型，已补上
- 其余所有类型定义、API层、组件均与后端一致，无编造数据

### 下一步 P4.3 → ✅ 已完成

---

## P4.3 完成情况 ✅

| Step | 内容 | 状态 |
|------|------|------|
| 1 | ScoreListScreen 成绩列表（学期筛选 + GPA卡片 + 成绩列表） | ✅ |
| 2 | ScoreTrendScreen 成绩趋势（按学期GPA柱状图） | ✅ |
| 3 | ExamListScreen 考试列表（日期分组 + 考试卡片） | ✅ |
| 4 | AcademicTab → Stack Navigator（ScoreList/ScoreTrend/ExamList） | ✅ |
| 5 | TypeScript 编译验证 | ✅ 零错误 |

### P4.3 新增文件
- `src/screens/scores/ScoreTrendScreen.tsx` — GPA 趋势页（学期分组 + 柱状图 + 累计GPA概览）
- `src/screens/exams/ExamListScreen.tsx` — 考试列表（今天/明天/本周/之后 分组 + 日期卡片）

### P4.3 修改文件
- `src/screens/scores/ScoreListScreen.tsx` — 完整重写（学期横向筛选 + GPA统计卡片 + 成绩列表含绩点颜色）
- `src/app/MainTabs.tsx` — AcademicTab 改为 Stack Navigator

## P4.4 完成情况 ✅

| Step | 内容 | 状态 |
|------|------|------|
| 1 | SSE 传输层 (`src/api/sse.ts`) — XHR + onprogress 解析 | ✅ |
| 2 | SessionListScreen 重写 — 会话列表 + 长按删除 + 下拉刷新 | ✅ |
| 3 | ChatScreen 新建 — 消息气泡 + SSE流式 + 工具调用展示 | ✅ |
| 4 | ChatTab → Stack Navigator (SessionList → Chat) | ✅ |
| 5 | TypeScript 编译验证 | ✅ 零错误 |
| 6 | edu-review 审查 + 修复 (onStartReached/onabort/catch清理/时间负值) | ✅ |

### P4.4 审查修复记录

### P4.4 新增文件
- `src/api/sse.ts` — SSE 传输层（XHR 流式解析 + Last-Event-ID + 心跳 + AbortSignal）
- `src/screens/chat/ChatScreen.tsx` — 聊天界面（消息气泡 用户/AI/工具 + SSE 流式接收 + 历史加载 + 自动滚动）
- `src/screens/chat/SessionListScreen.tsx` — 重写（真实数据 + 长按删除 + 下拉刷新 + 聚焦刷新 + 新对话按钮）

### P4.4 修改文件
- `src/app/MainTabs.tsx` — ChatTab 改为 Stack Navigator（SessionList → ChatScreen）

### 技术细节
- **SSE 实现**: React Native 不支持浏览器 EventSource，后端用 POST /chat，因此用 XMLHttpRequest + onprogress 增量解析
- **事件类型**: meta → token → (tool_start → tool_end) → done | error | heartbeat
- **消息气泡**: 用户蓝色右对齐 / AI灰色左对齐 / 工具黄色居中芯片
- **流式光标**: 流式接收期间显示闪烁光标 ▍
- **会话管理**: 新对话自动创建 session_key，已存在会话加载历史消息

## P4.5 完成情况 ✅

| Step | 内容 | 状态 |
|------|------|------|
| 1 | PlanningHomeScreen — 4 模块入口卡片 | ✅ |
| 2 | CreditGapScreen — 学分缺口分析（总览进度条 + 模块明细） | ✅ |
| 3 | RequiredCoursesScreen — 必修课完成检查（进度条 + 状态列表） | ✅ |
| 4 | RecommendScreen — 选课推荐（课程卡片 含学分/类型/理由） | ✅ |
| 5 | PathPlanScreen — 学业路径规划（学期卡片 含课程明细） | ✅ |
| 6 | AcademicStack +5 规划页面 + ScoreList 规划入口 | ✅ |
| 7 | TypeScript 编译验证 | ✅ 零错误 |

### P4.5 新增文件
- `src/screens/planning/PlanningHomeScreen.tsx` — 4 模块入口（学分缺口/必修课/选课推荐/学业路径）
- `src/screens/planning/CreditGapScreen.tsx` — 总览进度条 + 模块明细进度
- `src/screens/planning/RequiredCoursesScreen.tsx` — 统计进度条 + 课程完成状态列表
- `src/screens/planning/RecommendScreen.tsx` — 推荐课程卡片（类型色标 + 学分 + 理由）
- `src/screens/planning/PathPlanScreen.tsx` — 学期路径卡片（彩色标题 + 课程明细）

### P4.5 修改文件
- `src/app/MainTabs.tsx` — AcademicStack +5 规划页面
- `src/screens/scores/ScoreListScreen.tsx` — headerRight "规划" 入口按钮

### ⚠️ P4.5 遗留（D:\buct-edu-web 对照发现）
- **BindCredentialScreen** — SettingsScreen 有"绑定教务凭证"按钮跳转，导航类型已定义，但页面未实现（原 TODO）

### D:\buct-edu-web 对照发现的其他偏离
| # | 问题 | 状态 |
|---|------|------|
| 1 | 知识库上传/管理无 REST API | P4.6 解决 |
| 2 | score_detail/selected_courses/classrooms 缺直查API | P4.6 补充 |
| 3 | graduation_audit 爬虫已标记"不再考虑" | 跳过 |
| 4 | 通知列表页前端缺失 | 后续 Phase |

### 下一步 P4.6 (范围扩展) → ✅ 已完成

## P4.6 完成情况 ✅

| Step | 内容 | 状态 |
|------|------|------|
| 1 | BindCredentialScreen (P4.5遗留) | ✅ |
| 2 | 后端 knowledge.py API (5端点: upload/files/delete/stats/search) | ✅ |
| 3 | 后端补充 classrooms.py + scores/detail + courses/selected | ✅ |
| 4 | 前端 types/knowledge.ts + api/knowledge.ts | ✅ |
| 5 | KnowledgeHomeScreen — 入口（统计摘要+3入口卡片） | ✅ |
| 6 | KnowledgeListScreen — 文件列表（分类标签+长按删除） | ✅ |
| 7 | KnowledgeUploadScreen — 文件上传（DocumentPicker+进度条） | ✅ |
| 8 | KnowledgeSearchScreen — 语义搜索（分类筛选+结果卡片） | ✅ |
| 9 | AcademicStack +4 知识库页面 + SettingsStack(BindCredential) | ✅ |
| 10 | ScoreListScreen headerRight "知识库" 入口按钮 | ✅ |
| 11 | TypeScript 编译验证 | ✅ 零错误 |

### P4.6 新增文件

**后端**:
- `app/api/v1/knowledge.py` — 5端点 (POST upload/GET files/DELETE files/GET stats/POST search)
- `app/api/v1/classrooms.py` — 空闲教室查询

**前端**:
- `src/types/knowledge.ts` — 6 类型定义
- `src/api/knowledge.ts` — 知识库 API 封装
- `src/screens/knowledge/KnowledgeHomeScreen.tsx` — 知识库主页
- `src/screens/knowledge/KnowledgeListScreen.tsx` — 文件列表
- `src/screens/knowledge/KnowledgeUploadScreen.tsx` — 文件上传
- `src/screens/knowledge/KnowledgeSearchScreen.tsx` — 语义搜索
- `src/screens/settings/BindCredentialScreen.tsx` — 凭证绑定 (P4.5遗留)

### P4.6 修改文件

**后端**:
- `app/api/v1/__init__.py` — +knowledge +classrooms 路由
- `app/api/v1/scores.py` — +GET /detail
- `app/api/v1/courses.py` — +GET /selected

**前端**:
- `src/types/index.ts` — +knowledge 导出
- `src/types/navigation.ts` — AcademicStackParamList +4 知识库路由
- `src/app/MainTabs.tsx` — +知识库页面 +SettingsStack +BindCredential
- `src/screens/settings/SettingsScreen.tsx` — TODO→导航跳转
- `src/screens/scores/ScoreListScreen.tsx` — headerRight "知识库" 按钮

### D:\buct-edu-web 对照结果
| 偏离 | 状态 |
|------|------|
| BindCredentialScreen 缺失 | ✅ 已修复 |
| 知识库 REST API | ✅ 已实现 |
| score_detail/selected_courses/classrooms API | ✅ 已补充 |
| graduation_audit (爬虫占位) | ⏭️ 跳过 |
| 通知列表页 | ✅ P4.7 已实现 |
| GPA模拟器/ICS日历/课程冲突 | 后续 Phase 评估 |

## P4.7 完成情况 ✅

| Step | 内容 | 状态 |
|------|------|------|
| 1 | 后端 notifications.py API (GET /notifications + 分类筛选) | ✅ |
| 2 | 前端 api/notifications.ts | ✅ |
| 3 | NotificationListScreen — 分类筛选 + 通知卡片 + link跳转 | ✅ |
| 4 | AcademicStack +NotificationList 路由 | ✅ |
| 5 | HomeScreen 快捷入口（教务通知/知识库/学业规划） | ✅ |
| 6 | TypeScript 编译验证 | ✅ 零错误 |

### P4.7 新增文件
- `app/api/v1/notifications.py` — 通知 REST API
- `src/api/notifications.ts` — 通知 API 封装
- `src/screens/notifications/NotificationListScreen.tsx` — 通知列表页

### P4.7 修改文件
- `app/api/v1/__init__.py` — +notifications 路由
- `src/types/navigation.ts` — AcademicStackParamList +NotificationList
- `src/app/MainTabs.tsx` — +NotificationListScreen
- `src/screens/home/HomeScreen.tsx` — +快捷入口（通知/知识库/规划）

## P4.8 完成情况 ✅

| Step | 内容 | 状态 |
|------|------|------|
| 1 | api/classrooms.ts + ClassroomsScreen（星期+教学楼筛选） | ✅ |
| 2 | ScoreDetailScreen（成绩明细钻取，分数/绩点/学分卡片） | ✅ |
| 3 | ScoreListScreen 成绩行可点击→ScoreDetail 钻取 | ✅ |
| 4 | api/scores.ts +getScoreDetail / api/courses.ts +getSelectedCourses | ✅ |
| 5 | types/score.ts +ScoreDetailItem / navigation.ts +2路由 | ✅ |
| 6 | MainTabs.tsx 注册 Classrooms + ScoreDetail | ✅ |
| 7 | TypeScript 编译验证 | ✅ 零错误 |

### P4.8 新增文件
- `src/api/classrooms.ts` — 空闲教室 API
- `src/screens/courses/ClassroomsScreen.tsx` — 空闲教室查询页
- `src/screens/scores/ScoreDetailScreen.tsx` — 成绩明细页

### P4.8 修改文件
- `src/types/score.ts` — +ScoreDetailItem
- `src/types/navigation.ts` — ScheduleStack +Classrooms, AcademicStack +ScoreDetail
- `src/api/scores.ts` — +getScoreDetail
- `src/api/courses.ts` — +getSelectedCourses
- `src/app/MainTabs.tsx` — +ClassroomsScreen +ScoreDetailScreen
- `src/screens/scores/ScoreListScreen.tsx` — ScoreRow 可点击钻取

### P4 完整成果
| Phase | 内容 | 状态 |
|-------|------|------|
| P4.1 | 项目初始化 + 导航 + 登录 + 首页 | ✅ |
| P4.2 | 课表 + 同步横幅 | ✅ |
| P4.3 | 成绩列表 + GPA趋势 + 考试列表 | ✅ |
| P4.4 | SSE聊天 + 会话管理 | ✅ |
| P4.5 | 学业规划 4 模块 | ✅ |
| P4.6 | 知识库前后端 + 缺失API补充 + BindCredential | ✅ |
| P4.7 | 通知列表 + 首页快捷入口 | ✅ |
| P4.8 | 空闲教室 + 成绩明细钻取 | ✅ |

**前端总计**: 24 个 Screen | **后端总计**: 12 个 API 模块

### 下一步 P5 ⏳ 进行中

P5 进度: Step 1-5 完成, Step 6 进行中

## P5 完成情况

| Step | 内容 | 状态 |
|------|------|------|
| 1 | 阻塞修复 (celery/playwright/nginx/chromadb/config) | ✅ |
| 2 | Alembic 迁移初始化 | ✅ |
| 3 | 后端测试 (pytest + conftest + 32 tests) | ✅ |
| 4 | 前端错误处理 Review + 修复 | ✅ |
| 5 | 生产环境配置 (.env.production + DEPLOY.md) | ✅ |
| 6 | Docker Compose 端到端验证 | ✅ 21/21 通过 |

### P5 修复的生产 Bug
- **`functools.partial` + LangChain 崩溃**: `tools/__init__.py` 和 `knowledge_tools.py` 中用 `functools.partial` 绑定参数后传给 `tool()` 装饰器，`get_type_hints()` 无法检查 partial 对象 → 改用闭包 + `StructuredTool.from_function(infer_schema=False)`
- **config.py 拒绝 .env 外部变量**: `CELERY_BROKER_URL`、`CHROMADB_HOST` 等变量不在 Settings 类中 → 添加 `extra="ignore"`
- **Redis URL 测试**: 旧测试硬编码 localhost，.env 中是 Docker 内部地址 → 改为格式验证
- **requirements.txt 缺 celery**: celery-worker/beat 容器无法启动
- **Dockerfile 缺 Playwright Chromium**: 爬虫需要浏览器二进制
- **Nginx 强制 HTTPS 但无证书**: 容器 crash → 改为 HTTP 模式，HTTPS 注释待用

### P5 新增文件
- `pytest.ini` — pytest 配置 (asyncio + markers)
- `tests/conftest.py` — async DB/client/auth fixtures
- `tests/test_auth_api.py` — 认证集成测试 (13 tests)
- `tests/test_credentials_api.py` — 凭证管理测试 (7 tests)
- `tests/test_agent_tools.py` — Agent 工具单元测试 (9 tests)
- `tests/test_planning.py` — 规划/仪表盘/健康检查 (5 tests)
- `alembic.ini` + `alembic/env.py` — 数据库迁移
- `scripts/generate_self_signed_cert.sh` — SSL 证书生成
- `.env.production` — 生产环境配置模板
- `DEPLOY.md` — 部署指南

### P5 修改文件
- `requirements.txt` — +celery==5.4.0
- `Dockerfile` — +playwright install chromium
- `docker-compose.yml` — chromadb 版本锁定
- `nginx/nginx.conf` — HTTP 模式 + HTTPS 注释
- `app/config.py` — extra="ignore"
- `app/agent/tools/__init__.py` — partial→闭包
- `app/agent/tools/knowledge_tools.py` — partial→闭包
- `tests/test_p1_standalone.py` — Redis URL 测试修正
- `D:\xiaobei\app\src\screens\chat\ChatScreen.tsx` — 历史加载错误修复
- `D:\xiaobei\app\src\stores\authStore.ts` — refreshProfile 注释

### P5 Step 6: Docker Compose 端到端验证详情

| 问题 | 修复 | 状态 |
|------|------|------|
| nginx.conf 裸 upstream/server 块 → `"upstream" directive not allowed` | 添加 `events{}` + `http{}` 包装 | ✅ |
| nginx 代理 SSE 可能缓冲 | `proxy_buffering off; proxy_cache off;` | ✅ |
| `docker-compose.yml` `version: "3.8"` 废弃警告 | 移除 version 字段 | ✅ |
| chromadb `0.5.23` 镜像无法拉取 (Docker Hub 被墙) | 改用本地 `latest` | ✅ |
| celery 容器 `exec: celery not found` | 重建镜像 (pip 层含 celery) | ✅ |
| API 镜像缺 P4.6+ 路由 (classrooms/notifications/knowledge) | 全量重建 (COPY app/) | ✅ |
| Playwright `--with-deps` 在 Debian Trixie 失败 (`ttf-unifont`) | 手动安装 Trixie 兼容系统库 + `playwright install chromium` | ✅ |

**测试结果: 21/21 端点全部 200** (含之前 404 的 classrooms/notifications/knowledge/files/stats/scores-detail/courses-selected)

**修改文件**: `Dockerfile`, `docker-compose.yml`, `nginx/nginx.conf`

---

## P6 完成情况 ✅

| Step | 内容 | 状态 |
|------|------|------|
| 1 | 后端 GPA模拟器 API + Agent Tool | ✅ |
| 2 | 后端 ICS日历导出 API (无第三方依赖) | ✅ |
| 3 | 后端 课程冲突检测 API + Agent Tool | ✅ |
| 4 | 前端 types + api 层 (GPA/冲突) | ✅ |
| 5 | 前端 GpaSimulatorScreen 交互页面 | ✅ |
| 6 | 前端 ICS导出按钮 + 导航集成 + TS编译 | ✅ |

### P6 新增文件

**后端**:
- `app/agent/tools/gpa_tools.py` — GPA模拟器 Agent Tool (北化绩点映射 + 模拟计算)
- `app/agent/tools/conflict_tools.py` — 课程冲突检测 Agent Tool

**前端**:
- `src/types/gpa.ts` — GPA模拟器类型定义 (5 接口)
- `src/api/gpa.ts` — GPA模拟 API 封装
- `src/screens/scores/GpaSimulatorScreen.tsx` — GPA模拟器交互页 (动态添加课程 + 实时计算 + 绩点对照表)

### P6 修改文件

**后端**:
- `app/api/v1/scores.py` — +POST /gpa-simulate (GPA模拟器端点, Pydantic 校验)
- `app/api/v1/courses.py` — +GET /export/ics (ICS日历导出, 纯文本生成) +GET /conflicts (冲突检测)
- `app/agent/tools/__init__.py` — +simulate_gpa +detect_course_conflicts 注册

**前端**:
- `src/api/courses.ts` — +getIcsExportUrl() +getConflicts()
- `src/types/index.ts` — +gpa 导出
- `src/types/navigation.ts` — AcademicStack +GpaSimulator 路由
- `src/app/MainTabs.tsx` — +GpaSimulatorScreen 注册
- `src/screens/scores/ScoreListScreen.tsx` — headerRight +"模拟" 按钮
- `src/screens/courses/ScheduleScreen.tsx` — headerRight +"导出日历" 按钮

### 技术细节

- **GPA模拟器**: 北化标准绩点映射 (95+→4.33, 90-94→4.0, ... <60→0), 支持1-10门课同时模拟
- **ICS导出**: 纯 Python 生成标准 ICS 文件 (VEVENT + RRULE 周重复), 无第三方依赖, 通过 NODE_START_TIMES/END_TIMES 计算准确上课时间
- **开学日期推算**: 基于 `user_profile.get_current_semester()` 动态推算 (9月→秋季, 3月→春季, 7月→小学期)
- **冲突检测**: O(n²) 遍历所有课程对 → 检查同天+时段重叠+周次重叠

### P6 Commit 记录

| Commit | 内容 |
|--------|------|
| `725b18a` | 后端: GPA模拟器 + ICS导出 + 冲突检测 API + Agent Tools |
| `4bd61ea` | 前端: types + api + screens (GPA模拟器/ICS/冲突) |

---

## 项目完整交付总结

### Phase 总览

| Phase | 内容 | 状态 |
|-------|------|------|
| P1 | 项目骨架 (FastAPI + DB + Auth) | ✅ |
| P2 | 教务数据层 (14爬虫 + 13表 + 15Repo) | ✅ |
| P3 | AI Agent 系统 (17 Tools + SSE + Planning) | ✅ |
| P4 | React Native 前端 (24 Screens + 12 API 模块) | ✅ |
| P5 | 生产环境加固 (测试/Alembic/Docker/部署) | ✅ |
| P6 | 高级功能 (GPA模拟/ICS日历/冲突检测) | ✅ |

### 交付物统计

| 类别 | 数量 |
|------|------|
| 后端 API 端点 | 40+ |
| 后端 Agent Tools | 19 |
| 数据库表 | 18 |
| 爬虫 | 14 |
| 前端 Screen | 25 |
| 前端 API 服务 | 14 |
| TypeScript 类型文件 | 10 |

### 后续方向

- App Store / Google Play 上架准备
- 生产环境部署 + 监控
- 用户反馈迭代
