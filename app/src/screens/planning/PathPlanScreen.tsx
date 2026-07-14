// ============================================================
// 学业路径规划页面 — 按学期展示修读路径
// ============================================================
import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import { planningApi } from '../../api/planning';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import type { SemesterPlan, PathPlanResponse } from '../../types';

export function PathPlanScreen() {
  const [data, setData] = useState<PathPlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);
      const res = await planningApi.getPath();
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  if (loading) return <LoadingSpinner message="生成学业路径..." fullScreen />;
  if (error && !data) return <EmptyState icon="⚠️" title="加载失败" description={error} actionLabel="重试" onAction={() => fetch()} />;
  if (!data || data.semesters.length === 0) return <EmptyState icon="🗺️" title="暂无数据" description="请先同步教务数据，AI 将规划你的学业路径" />;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => fetch(true)} tintColor="#0880D7" colors={['#0880D7']} />}
    >
      {/* ── 总览 ── */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>剩余 {data.remaining_credits} 学分</Text>
        <Text style={styles.headerSub}>预计 {data.semesters.length} 个学期完成</Text>
      </View>

      {/* ── 学期路径 ── */}
      {data.semesters.map((sem: SemesterPlan, idx: number) => (
        <SemesterCard key={sem.semester} semester={sem} index={idx} />
      ))}
    </ScrollView>
  );
}

// ============================================================
// 学期卡片
// ============================================================

const SEMESTER_COLORS = ['#0880D7', '#059669', '#D97706', '#7C3AED', '#DB2777', '#0891B2'];

function SemesterCard({ semester: sem, index }: { semester: SemesterPlan; index: number }) {
  const color = SEMESTER_COLORS[index % SEMESTER_COLORS.length];

  return (
    <View style={styles.card}>
      {/* 学期标题 */}
      <View style={[styles.cardHeader, { backgroundColor: color }]}>
        <Text style={styles.cardTitle}>{sem.semester}</Text>
        <Text style={styles.cardCredits}>{sem.total_credits} 学分</Text>
      </View>

      {/* 课程列表 */}
      <View style={styles.courseList}>
        {sem.courses.map((course) => (
          <View key={course.course_code} style={styles.courseRow}>
            <View style={styles.courseDot} />
            <View style={styles.courseBody}>
              <Text style={styles.courseName} numberOfLines={1}>{course.course_name}</Text>
              <Text style={styles.courseCode}>{course.course_code}</Text>
            </View>
            <Text style={styles.courseCredit}>{course.credit} 学分</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  content: { padding: 16, paddingBottom: 40 },
  header: {
    alignItems: 'center', paddingVertical: 20, marginBottom: 20,
  },
  headerTitle: { fontSize: 24, fontWeight: '700', color: '#111827', marginBottom: 4 },
  headerSub: { fontSize: 14, color: '#9CA3AF' },
  // 学期卡片
  card: {
    backgroundColor: '#FFFFFF', borderRadius: 16, marginBottom: 16, overflow: 'hidden',
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.06, shadowRadius: 6, elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 16, paddingVertical: 12,
  },
  cardTitle: { fontSize: 16, fontWeight: '700', color: '#FFFFFF' },
  cardCredits: { fontSize: 14, fontWeight: '600', color: '#FFFFFF', opacity: 0.9 },
  courseList: { padding: 12 },
  courseRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, paddingHorizontal: 4 },
  courseDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#D1D5DB', marginRight: 12 },
  courseBody: { flex: 1 },
  courseName: { fontSize: 14, fontWeight: '600', color: '#111827', marginBottom: 2 },
  courseCode: { fontSize: 11, color: '#9CA3AF' },
  courseCredit: { fontSize: 13, color: '#6B7280', fontWeight: '500', marginLeft: 8 },
});
