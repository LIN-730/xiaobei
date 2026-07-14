// ============================================================
// 考试列表页 — 考试安排展示
// ============================================================
import React, { useMemo } from 'react';
import { View, Text, ScrollView, StyleSheet, RefreshControl } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { format, isAfter, isBefore, addDays, isToday, isTomorrow } from 'date-fns';
import { examsApi } from '../../api/exams';
import type { Exam } from '../../types/exam';
import { Card } from '../../components/ui/Card';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';

// ============================================================
// 日期分组
// ============================================================

interface ExamGroup {
  label: string;
  exams: Exam[];
}

function groupExams(exams: Exam[]): ExamGroup[] {
  const now = new Date();
  const weekLater = addDays(now, 7);

  const groups: ExamGroup[] = [
    { label: '今天', exams: [] },
    { label: '明天', exams: [] },
    { label: '本周', exams: [] },
    { label: '之后', exams: [] },
  ];

  for (const exam of exams) {
    const date = new Date(exam.exam_date);
    if (isToday(date)) {
      groups[0].exams.push(exam);
    } else if (isTomorrow(date)) {
      groups[1].exams.push(exam);
    } else if (isBefore(date, weekLater) && isAfter(date, now)) {
      groups[2].exams.push(exam);
    } else {
      groups[3].exams.push(exam);
    }
  }

  return groups.filter((g) => g.exams.length > 0);
}

// ============================================================
// ExamListScreen
// ============================================================

export function ExamListScreen() {
  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ['exams'],
    queryFn: () => examsApi.getExams(),
  });

  const exams = data?.data ?? [];
  const groups = useMemo(() => groupExams(exams), [exams]);

  if (isLoading) return <LoadingSpinner fullScreen />;

  if (isError) {
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

  if (exams.length === 0) {
    return (
      <EmptyState
        icon="📝"
        title="暂无考试安排"
        description="同步教务数据后将展示考试信息"
      />
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
    >
      <Text style={styles.header}>共 {exams.length} 场考试</Text>

      {groups.map((group) => (
        <View key={group.label} style={styles.group}>
          <Text style={styles.groupLabel}>{group.label}</Text>
          {group.exams.map((exam, idx) => (
            <ExamCard key={`${exam.course_name}-${idx}`} exam={exam} />
          ))}
        </View>
      ))}
    </ScrollView>
  );
}

// ============================================================
// 考试卡片
// ============================================================

function ExamCard({ exam }: { exam: Exam }) {
  const date = new Date(exam.exam_date);
  const dateStr = format(date, 'MM/dd');
  const weekdayStr = format(date, 'EEE');

  return (
    <Card style={styles.examCard}>
      <View style={styles.examRow}>
        {/* 日期 */}
        <View style={styles.dateCol}>
          <Text style={styles.dateText}>{dateStr}</Text>
          <Text style={styles.weekdayText}>{weekdayStr}</Text>
        </View>

        {/* 分隔线 */}
        <View style={styles.divider} />

        {/* 信息 */}
        <View style={styles.infoCol}>
          <Text style={styles.examName} numberOfLines={1}>
            {exam.course_name}
          </Text>
          <View style={styles.examMetaRow}>
            <MetaTag icon="🕐" text={exam.exam_time || '待定'} />
            <MetaTag icon="📍" text={exam.classroom || '待定'} />
          </View>
          <View style={styles.examMetaRow}>
            {exam.seat_no ? (
              <MetaTag icon="💺" text={`座位 ${exam.seat_no}`} />
            ) : null}
            {exam.exam_type ? (
              <MetaTag icon="📋" text={exam.exam_type} />
            ) : null}
            {exam.campus ? (
              <MetaTag icon="🏫" text={exam.campus} />
            ) : null}
          </View>
        </View>
      </View>
    </Card>
  );
}

function MetaTag({ icon, text }: { icon: string; text: string }) {
  return (
    <View style={styles.metaTag}>
      <Text style={styles.metaIcon}>{icon}</Text>
      <Text style={styles.metaText}>{text}</Text>
    </View>
  );
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    fontSize: 13,
    color: '#9CA3AF',
    marginBottom: 16,
  },

  // 日期分组
  group: {
    marginBottom: 20,
  },
  groupLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 10,
    paddingLeft: 4,
  },

  // 考试卡片
  examCard: {
    marginBottom: 10,
    padding: 14,
  },
  examRow: {
    flexDirection: 'row',
    alignItems: 'stretch',
  },
  dateCol: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 52,
  },
  dateText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  weekdayText: {
    fontSize: 11,
    color: '#9CA3AF',
    marginTop: 2,
  },
  divider: {
    width: 1,
    backgroundColor: '#E5E7EB',
    marginHorizontal: 12,
  },
  infoCol: {
    flex: 1,
  },
  examName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 8,
  },
  examMetaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 4,
  },
  metaTag: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  metaIcon: {
    fontSize: 12,
    marginRight: 3,
  },
  metaText: {
    fontSize: 12,
    color: '#6B7280',
  },
});
