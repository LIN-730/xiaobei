# 教务智能助手（小北）— 前端 CLAUDE.md

> **Expo SDK 56 专用：写代码前先查 https://docs.expo.dev/versions/v56.0.0/**

## 🔺 原型参考：D:\buct-edu-web

**原型是功能蓝图，不是实现标准。** 开发时：
- ✅ 原型有的功能 → 移动端必须有对应 Screen，不可遗漏
- ✅ 原型的设计/实现不好 → 自行升级优化，不需要照搬
- ✅ 原型不合理的地方 → 直接去掉或替换为更好的方案
- ✅ 原型没有但移动端需要 → 自行设计添加

**每次新 Phase 开始前，先查原型对应功能，确保不遗漏、不盲目照搬。**

> **注意**：后端 `crawlers/`、`agent/edu_knowledge.py`、`agent/user_profile.py` 等模块包含北化正方 V9.0 教务系统的深度领域知识（GNMKDM 代码、学期推算等），前端开发时不要假设数据结构会随意变化——API 响应格式由这些底层知识决定。

## 技术栈
- Expo SDK 56 + React Native 0.85 + TypeScript 6
- React Navigation 7 (Native Stack + Bottom Tabs)
- TanStack Query 5 (服务端状态) + Zustand 5 (客户端状态)
- NativeWind v4 + Tailwind CSS 3（暂未启用 className，统一用 StyleSheet）
- React Hook Form 7 + Zod 4（表单验证）
- Axios（HTTP 客户端，Token 自动刷新）
- date-fns（日期处理）

## 样式方案
**当前阶段使用 StyleSheet.create()，待 P5+ 统一迁移 NativeWind。**

## OpenClaw 协作（全局规则，不得跳过）
- 每批改动完成后发送 `openclaw system event --text "app: <阶段> — <摘要>" --mode now`
- 后端任务可并行派发给 `edu-config` agent

## 工作流
1. Explore → Plan → Implement（不得跳过）
2. 每批改动后 `npx tsc --noEmit` 验证
3. 每 Phase 完成后 commit

## 目录结构
```
src/
├── api/          # Axios 实例 + 14 个 API 服务
├── app/          # RootNavigator + AuthStack + MainTabs
├── components/   # ui/ + chat/ + sync/ + course/ + score/
├── screens/      # auth/ home/ courses/ scores/ exams/ chat/ settings/
├── stores/       # authStore + chatStore (Zustand)
├── types/        # API 类型 + 导航类型
└── utils/        # constants + jwt + storage
```
