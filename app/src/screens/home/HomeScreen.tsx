// ============================================================
// 首页 — 仪表盘聚合
// ============================================================
import React from 'react';
import { View, Text, ScrollView, StyleSheet, RefreshControl, TouchableOpacity } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import { useAuthStore } from '../../stores/authStore';
import { dashboardApi } from '../../api/dashboard';
import { Card } from '../../components/ui/Card';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { SyncBanner } from '../../components/sync/SyncBanner';

export function HomeScreen() {
  const navigation = useNavigation<any>();
  const user = useAuthStore((s) => s.user);

  const {
    data: dashboard,
    isLoading,
    isError,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboardApi.getDashboard(),
  });

  if (isLoading) {
    return <LoadingSpinner fullScreen />;
  }

  if (isError || !dashboard) {
    return (
      <EmptyState
        icon="⚠️"
        title="数据加载失败"
        description="请检查网络连接后重试"
        actionLabel="重试"
        onAction={() => refetch()}
      />
    );
  }

  // 新用户：无教务数据，显示引导而非白屏
  if (!dashboard.student || !dashboard.academic_status) {
    return (
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
      >
        <SyncBanner />
        <Card style={styles.welcomeCard}>
          <Text style={styles.greeting}>欢迎使用小北 🎓</Text>
          <Text style={styles.collegeInfo}>教务智能助手 — 你的学业伙伴</Text>
          {!user?.has_credential && (
            <View style={styles.bindHint}>
              <Text style={styles.bindHintText}>⚠️ 尚未绑定教务凭证，请前往「我的」→「绑定教务凭证」完成绑定</Text>
            </View>
          )}
        </Card>
        <Card style={styles.section}>
          <Text style={styles.sectionTitle}>开始使用</Text>
          <Text style={{ fontSize: 14, color: '#6B7280', lineHeight: 22 }}>
            1. 前往「我的」页面绑定教务凭证{'\n'}
            2. 触发数据同步，获取课表/成绩/考试{'\n'}
            3. 返回首页查看你的学业数据
          </Text>
        </Card>
      </ScrollView>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
    >
      {/* 同步状态横幅 */}
      <SyncBanner />

      {/* 欢迎卡片 */}
      <Card style={styles.welcomeCard}>
        <Text style={styles.greeting}>你好，{dashboard.student?.name || '同学'} 👋</Text>
        <Text style={styles.collegeInfo}>
          {dashboard.student?.college || ''} {dashboard.student?.major ? '· ' + dashboard.student.major : ''}
        </Text>
        {!user?.has_credential && (
          <View style={styles.bindHint}>
            <Text style={styles.bindHintText}>⚠️ 尚未绑定教务凭证，请前往「我的」页面绑定</Text>
          </View>
        )}
      </Card>

      {/* KPI 指标 */}
      <View style={styles.kpiGrid}>
        <KpiCard label="本学期课程" value={dashboard.kpi?.course_count ?? 0} unit="门" color="#0880D7" />
        <KpiCard label="近期考试" value={dashboard.kpi?.exam_count ?? 0} unit="场" color="#F59E0B" />
        <KpiCard label="已修学分" value={dashboard.kpi?.total_credits ?? 0} unit="分" color="#22C55E" />
        <KpiCard label="平均绩点" value={dashboard.kpi?.avg_gpa ?? 0} unit="" color="#7C3AED" />
      </View>

      {/* 快捷入口 */}
      <View style={styles.quickActions}>
        <TouchableOpacity
          style={styles.quickBtn}
          activeOpacity={0.7}
          onPress={() => navigation.navigate('AcademicTab', { screen: 'NotificationList' })}
        >
          <Text style={styles.quickIcon}>📢</Text>
          <Text style={styles.quickLabel}>教务通知</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.quickBtn}
          activeOpacity={0.7}
          onPress={() => navigation.navigate('AcademicTab', { screen: 'KnowledgeHome' })}
        >
          <Text style={styles.quickIcon}>📚</Text>
          <Text style={styles.quickLabel}>知识库</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.quickBtn}
          activeOpacity={0.7}
          onPress={() => navigation.navigate('AcademicTab', { screen: 'PlanningHome' })}
        >
          <Text style={styles.quickIcon}>📊</Text>
          <Text style={styles.quickLabel}>学业规划</Text>
        </TouchableOpacity>
      </View>

      {/* 学业状态 */}
      <Card style={styles.section}>
        <Text style={styles.sectionTitle}>学业状态</Text>
        <View style={styles.progressRow}>
          <Text style={styles.progressLabel}>必修课完成</Text>
          <Text style={styles.progressValue}>
            {dashboard.academic_status.required_done} / {dashboard.academic_status.required_total}
          </Text>
        </View>
        <View style={styles.progressBar}>
          <View
            style={[
              styles.progressFill,
              {
                width: `${dashboard.academic_status.required_total > 0
                  ? (dashboard.academic_status.required_done / dashboard.academic_status.required_total) * 100
                  : 0}%`,
              },
            ]}
          />
        </View>

        <View style={styles.progressRow}>
          <Text style={styles.progressLabel}>学分完成</Text>
          <Text style={styles.progressValue}>
            {dashboard.academic_status.earned_credits} / {dashboard.academic_status.total_credits}
          </Text>
        </View>
        <View style={styles.progressBar}>
          <View
            style={[
              styles.progressFill,
              styles.progressFillGreen,
              {
                width: `${dashboard.academic_status.total_credits > 0
                  ? (dashboard.academic_status.earned_credits / dashboard.academic_status.total_credits) * 100
                  : 0}%`,
              },
            ]}
          />
        </View>
      </Card>
    </ScrollView>
  );
}

function KpiCard({
  label,
  value,
  unit,
  color,
}: {
  label: string;
  value: number;
  unit: string;
  color: string;
}) {
  return (
    <Card style={styles.kpiCard}>
      <Text style={styles.kpiLabel}>{label}</Text>
      <View style={styles.kpiValueRow}>
        <Text style={[styles.kpiValue, { color }]}>{value}</Text>
        {unit ? <Text style={styles.kpiUnit}>{unit}</Text> : null}
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  welcomeCard: {
    marginBottom: 16,
  },
  greeting: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  collegeInfo: {
    fontSize: 14,
    color: '#6B7280',
  },
  bindHint: {
    marginTop: 12,
    backgroundColor: '#FEF3C7',
    borderRadius: 8,
    padding: 10,
  },
  bindHintText: {
    fontSize: 13,
    color: '#92400E',
  },
  kpiGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  kpiCard: {
    width: '47%',
    flexGrow: 1,
  },
  kpiLabel: {
    fontSize: 13,
    color: '#6B7280',
    marginBottom: 8,
  },
  kpiValueRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  kpiValue: {
    fontSize: 28,
    fontWeight: '700',
  },
  kpiUnit: {
    fontSize: 14,
    color: '#9CA3AF',
    marginLeft: 4,
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  progressRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  progressLabel: {
    fontSize: 14,
    color: '#374151',
  },
  progressValue: {
    fontSize: 14,
    fontWeight: '500',
    color: '#111827',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#E5E7EB',
    borderRadius: 4,
    marginBottom: 16,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#0880D7',
    borderRadius: 4,
  },
  progressFillGreen: {
    backgroundColor: '#22C55E',
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
    gap: 10,
  },
  quickBtn: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  quickIcon: { fontSize: 24, marginBottom: 6 },
  quickLabel: { fontSize: 13, color: '#374151', fontWeight: '500' },
});
