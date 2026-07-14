// ============================================================
// 必修课完成情况页面
// ============================================================
import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import { planningApi } from '../../api/planning';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import type { RequiredCourseStatus, RequiredCoursesResponse } from '../../types';

export function RequiredCoursesScreen() {
  const [data, setData] = useState<RequiredCoursesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);
      const res = await planningApi.getRequiredCourses();
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  if (loading) return <LoadingSpinner message="加载必修课数据..." fullScreen />;
  if (error && !data) return <EmptyState icon="⚠️" title="加载失败" description={error} actionLabel="重试" onAction={() => fetch()} />;
  if (!data || data.courses.length === 0) return <EmptyState icon="✅" title="暂无数据" description="请先同步教务数据" />;

  const pct = data.total_count > 0
    ? Math.round((data.completed_count / data.total_count) * 100)
    : 0;

  return (
    <View style={styles.container}>
      {/* ── 头部统计 ── */}
      <View style={styles.header}>
        <View style={styles.statBadge}>
          <Text style={styles.statValue}>{data.completed_count}/{data.total_count}</Text>
          <Text style={styles.statLabel}>已修读</Text>
        </View>
        <View style={styles.progressBarBg}>
          <View style={[styles.progressBarFill, { width: `${Math.min(pct, 100)}%` as any }]} />
        </View>
        <Text style={styles.pct}>{pct}% 完成</Text>
      </View>

      {/* ── 课程列表 ── */}
      <FlatList
        data={data.courses}
        keyExtractor={(item) => item.course_code}
        renderItem={({ item }) => <CourseRow course={item} />}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => fetch(true)} tintColor="#0880D7" colors={['#0880D7']} />}
        ItemSeparatorComponent={() => <View style={styles.separator} />}
      />
    </View>
  );
}

// ============================================================
// 课程行
// ============================================================

function CourseRow({ course: c }: { course: RequiredCourseStatus }) {
  return (
    <View style={[styles.row, c.is_completed && styles.rowDone]}>
      <View style={[styles.statusDot, c.is_completed ? styles.dotDone : styles.dotPending]} />
      <View style={styles.rowBody}>
        <Text style={styles.courseName} numberOfLines={1}>{c.course_name}</Text>
        <Text style={styles.courseCode}>{c.course_code}</Text>
      </View>
      <View style={styles.rowRight}>
        {c.is_completed ? (
          <>
            {c.grade && <Text style={styles.grade}>{c.grade}</Text>}
            {c.term && <Text style={styles.term}>{c.term}</Text>}
          </>
        ) : (
          <Text style={styles.pending}>待修读</Text>
        )}
      </View>
    </View>
  );
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  header: {
    backgroundColor: '#FFFFFF',
    padding: 20,
    margin: 16,
    borderRadius: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.06, shadowRadius: 4, elevation: 2,
  },
  statBadge: { flexDirection: 'row', alignItems: 'baseline', marginBottom: 12 },
  statValue: { fontSize: 28, fontWeight: '700', color: '#111827' },
  statLabel: { fontSize: 14, color: '#9CA3AF', marginLeft: 6 },
  progressBarBg: { height: 8, backgroundColor: '#F3F4F6', borderRadius: 4, marginBottom: 8, overflow: 'hidden' },
  progressBarFill: { height: '100%', backgroundColor: '#059669', borderRadius: 4 },
  pct: { fontSize: 13, color: '#059669', fontWeight: '600', textAlign: 'right' },
  list: { paddingHorizontal: 16, paddingBottom: 24 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.03, shadowRadius: 2, elevation: 1,
  },
  rowDone: { opacity: 0.65 },
  statusDot: { width: 10, height: 10, borderRadius: 5, marginRight: 12 },
  dotDone: { backgroundColor: '#059669' },
  dotPending: { backgroundColor: '#F59E0B' },
  rowBody: { flex: 1 },
  courseName: { fontSize: 15, fontWeight: '600', color: '#111827', marginBottom: 2 },
  courseCode: { fontSize: 12, color: '#9CA3AF' },
  rowRight: { alignItems: 'flex-end', marginLeft: 8 },
  grade: { fontSize: 14, fontWeight: '600', color: '#0880D7' },
  term: { fontSize: 11, color: '#9CA3AF', marginTop: 2 },
  pending: { fontSize: 13, color: '#F59E0B', fontWeight: '500' },
  separator: { height: 8 },
});
