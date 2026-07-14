// ============================================================
// 已登录底部 Tab 导航
// ============================================================
import React from 'react';
import { Platform, Text, StyleSheet } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import type { MainTabParamList } from '../types/navigation';

// Placeholder screens — 后续各 Phase 替换为真实实现
import { HomeScreen } from '../screens/home/HomeScreen';
import { ScheduleScreen } from '../screens/courses/ScheduleScreen';
import { CourseDetailScreen } from '../screens/courses/CourseDetailScreen';
import { ScoreListScreen } from '../screens/scores/ScoreListScreen';
import { ScoreTrendScreen } from '../screens/scores/ScoreTrendScreen';
import { ExamListScreen } from '../screens/exams/ExamListScreen';
import { PlanningHomeScreen } from '../screens/planning/PlanningHomeScreen';
import { CreditGapScreen } from '../screens/planning/CreditGapScreen';
import { RequiredCoursesScreen } from '../screens/planning/RequiredCoursesScreen';
import { RecommendScreen } from '../screens/planning/RecommendScreen';
import { PathPlanScreen } from '../screens/planning/PathPlanScreen';
import { KnowledgeHomeScreen } from '../screens/knowledge/KnowledgeHomeScreen';
import { KnowledgeListScreen } from '../screens/knowledge/KnowledgeListScreen';
import { KnowledgeUploadScreen } from '../screens/knowledge/KnowledgeUploadScreen';
import { KnowledgeSearchScreen } from '../screens/knowledge/KnowledgeSearchScreen';
import { SessionListScreen } from '../screens/chat/SessionListScreen';
import { ChatScreen } from '../screens/chat/ChatScreen';
import { SettingsScreen } from '../screens/settings/SettingsScreen';
import { BindCredentialScreen } from '../screens/settings/BindCredentialScreen';
import { NotificationListScreen } from '../screens/notifications/NotificationListScreen';
import { ClassroomsScreen } from '../screens/courses/ClassroomsScreen';
import { ScoreDetailScreen } from '../screens/scores/ScoreDetailScreen';
import { GpaSimulatorScreen } from '../screens/scores/GpaSimulatorScreen';
import type { ScheduleStackParamList, AcademicStackParamList, ChatStackParamList, SettingsStackParamList } from '../types/navigation';

const Tab = createBottomTabNavigator<MainTabParamList>();
const ScheduleStack = createNativeStackNavigator<ScheduleStackParamList>();
const AcademicStack = createNativeStackNavigator<AcademicStackParamList>();
const ChatStack = createNativeStackNavigator<ChatStackParamList>();
const SettingsStack = createNativeStackNavigator<SettingsStackParamList>();

// Emoji 图标映射 (后续替换为 @expo/vector-icons)
const TAB_ICONS: Record<string, string> = {
  HomeTab: '🏠',
  ScheduleTab: '📅',
  AcademicTab: '📊',
  ChatTab: '🤖',
  SettingsTab: '👤',
};

// ============================================================
// 课表 Stack 导航器 — Schedule → CourseDetail
// ============================================================

function ScheduleStackNavigator() {
  return (
    <ScheduleStack.Navigator>
      <ScheduleStack.Screen
        name="Schedule"
        component={ScheduleScreen}
        options={{ title: '课表' }}
      />
      <ScheduleStack.Screen
        name="CourseDetail"
        component={CourseDetailScreen}
        options={{ title: '课程详情' }}
      />
      <ScheduleStack.Screen
        name="Classrooms"
        component={ClassroomsScreen}
        options={{ title: '空闲教室' }}
      />
    </ScheduleStack.Navigator>
  );
}

// ============================================================
// 学业 Stack 导航器 — ScoreList → ScoreTrend/ExamList/PlanningHome → 规划子页
// ============================================================

function AcademicStackNavigator() {
  return (
    <AcademicStack.Navigator>
      <AcademicStack.Screen
        name="ScoreList"
        component={ScoreListScreen}
        options={{ title: '学业' }}
      />
      <AcademicStack.Screen
        name="ScoreTrend"
        component={ScoreTrendScreen}
        options={{ title: 'GPA 趋势' }}
      />
      <AcademicStack.Screen
        name="ExamList"
        component={ExamListScreen}
        options={{ title: '考试安排' }}
      />
      <AcademicStack.Screen
        name="PlanningHome"
        component={PlanningHomeScreen}
        options={{ title: '学业规划' }}
      />
      <AcademicStack.Screen
        name="CreditGap"
        component={CreditGapScreen}
        options={{ title: '学分缺口' }}
      />
      <AcademicStack.Screen
        name="RequiredCourses"
        component={RequiredCoursesScreen}
        options={{ title: '必修课检查' }}
      />
      <AcademicStack.Screen
        name="Recommend"
        component={RecommendScreen}
        options={{ title: '选课推荐' }}
      />
      <AcademicStack.Screen
        name="PathPlan"
        component={PathPlanScreen}
        options={{ title: '学业路径' }}
      />
      <AcademicStack.Screen
        name="KnowledgeHome"
        component={KnowledgeHomeScreen}
        options={{ title: '知识库' }}
      />
      <AcademicStack.Screen
        name="KnowledgeList"
        component={KnowledgeListScreen}
        options={{ title: '我的文件' }}
      />
      <AcademicStack.Screen
        name="KnowledgeUpload"
        component={KnowledgeUploadScreen}
        options={{ title: '上传文件' }}
      />
      <AcademicStack.Screen
        name="KnowledgeSearch"
        component={KnowledgeSearchScreen}
        options={{ title: '知识搜索' }}
      />
      <AcademicStack.Screen
        name="NotificationList"
        component={NotificationListScreen}
        options={{ title: '教务通知' }}
      />
      <AcademicStack.Screen
        name="ScoreDetail"
        component={ScoreDetailScreen}
        options={{ title: '成绩明细' }}
      />
      <AcademicStack.Screen
        name="GpaSimulator"
        component={GpaSimulatorScreen}
        options={{ title: 'GPA 模拟器' }}
      />
    </AcademicStack.Navigator>
  );
}

// ============================================================
// AI 对话 Stack 导航器 — SessionList → Chat
// ============================================================

function ChatStackNavigator() {
  return (
    <ChatStack.Navigator>
      <ChatStack.Screen
        name="SessionList"
        component={SessionListScreen}
        options={{ headerShown: false }}
      />
      <ChatStack.Screen
        name="Chat"
        component={ChatScreen}
        options={{ title: 'AI 助手' }}
      />
    </ChatStack.Navigator>
  );
}

// ============================================================
// 设置 Stack 导航器 — Settings → BindCredential
// ============================================================

function SettingsStackNavigator() {
  return (
    <SettingsStack.Navigator>
      <SettingsStack.Screen
        name="Settings"
        component={SettingsScreen}
        options={{ title: '我的' }}
      />
      <SettingsStack.Screen
        name="BindCredential"
        component={BindCredentialScreen}
        options={{ title: '绑定教务凭证' }}
      />
    </SettingsStack.Navigator>
  );
}

export function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: '#FFFFFF' },
        headerTitleStyle: { fontSize: 17, fontWeight: '600', color: '#111827' },
        tabBarStyle: styles.tabBar,
        tabBarActiveTintColor: '#0880D7',
        tabBarInactiveTintColor: '#9CA3AF',
        tabBarLabelStyle: { fontSize: 11, fontWeight: '500' },
      }}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeScreen}
        options={{
          title: '小北',
          tabBarLabel: '首页',
          tabBarIcon: () => <Text style={styles.tabIcon}>{TAB_ICONS.HomeTab}</Text>,
          headerTitle: '教务智能助手',
        }}
      />
      <Tab.Screen
        name="ScheduleTab"
        component={ScheduleStackNavigator}
        options={{
          headerShown: false,
          tabBarLabel: '课表',
          tabBarIcon: () => <Text style={styles.tabIcon}>{TAB_ICONS.ScheduleTab}</Text>,
        }}
      />
      <Tab.Screen
        name="AcademicTab"
        component={AcademicStackNavigator}
        options={{
          headerShown: false,
          title: '学业',
          tabBarLabel: '学业',
          tabBarIcon: () => <Text style={styles.tabIcon}>{TAB_ICONS.AcademicTab}</Text>,
        }}
      />
      <Tab.Screen
        name="ChatTab"
        component={ChatStackNavigator}
        options={{
          headerShown: false,
          title: 'AI 助手',
          tabBarLabel: 'AI',
          tabBarIcon: () => <Text style={styles.tabIcon}>{TAB_ICONS.ChatTab}</Text>,
        }}
      />
      <Tab.Screen
        name="SettingsTab"
        component={SettingsStackNavigator}
        options={{
          headerShown: false,
          title: '我的',
          tabBarLabel: '我的',
          tabBarIcon: () => <Text style={styles.tabIcon}>{TAB_ICONS.SettingsTab}</Text>,
        }}
      />
    </Tab.Navigator>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: '#FFFFFF',
    borderTopWidth: 0.5,
    borderTopColor: '#E5E7EB',
    paddingBottom: Platform.OS === 'ios' ? 20 : 8,
    paddingTop: 8,
    height: Platform.OS === 'ios' ? 85 : 65,
  },
  tabIcon: {
    fontSize: 20,
  },
});
