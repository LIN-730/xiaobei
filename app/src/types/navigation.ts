// ============================================================
// 导航路由参数类型
// ============================================================

import type { Course } from './course';

/** Auth Stack 路由参数 */
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
};

/** 首页 Stack 路由参数 */
export type HomeStackParamList = {
  Home: undefined;
};

/** 课表 Stack 路由参数 */
export type ScheduleStackParamList = {
  Schedule: undefined;
  CourseDetail: { course: Course };
  Classrooms: undefined;
};

/** 学业 Stack 路由参数 */
export type AcademicStackParamList = {
  ScoreList: undefined;
  ScoreTrend: undefined;
  ExamList: undefined;
  PlanningHome: undefined;
  CreditGap: undefined;
  RequiredCourses: undefined;
  Recommend: undefined;
  PathPlan: undefined;
  KnowledgeHome: undefined;
  KnowledgeList: undefined;
  KnowledgeUpload: undefined;
  KnowledgeSearch: undefined;
  NotificationList: undefined;
  ScoreDetail: { courseName: string };
  GpaSimulator: undefined;
};

/** AI 对话 Stack 路由参数 */
export type ChatStackParamList = {
  SessionList: undefined;
  Chat: { sessionKey?: string; title?: string };
};

/** 我的 Stack 路由参数 */
export type SettingsStackParamList = {
  Settings: undefined;
  Profile: undefined;
  BindCredential: undefined;
};

/** 主 Tab 路由参数 */
export type MainTabParamList = {
  HomeTab: undefined;
  ScheduleTab: undefined;
  AcademicTab: undefined;
  ChatTab: undefined;
  SettingsTab: undefined;
};
