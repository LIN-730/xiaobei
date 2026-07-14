// ============================================================
// 选课推荐页面
// ============================================================
import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import { planningApi } from '../../api/planning';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';
import type { CourseRecommendation, RecommendResponse } from '../../types';

export function RecommendScreen() {
  const [data, setData] = useState<RecommendResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [semester, setSemester] = useState<string | undefined>(undefined);

  const fetch = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);
      const res = await planningApi.getRecommend(semester);
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [semester]);

  useEffect(() => { fetch(); }, [fetch]);

  if (loading) return <LoadingSpinner message="生成推荐..." fullScreen />;
  if (error && !data) return <EmptyState icon="⚠️" title="加载失败" description={error} actionLabel="重试" onAction={() => fetch()} />;
  if (!data || data.recommendations.length === 0) {
    return (
      <EmptyState
        icon="💡"
        title="暂无推荐"
        description="请先同步教务数据，AI 将基于你的学业进度推荐课程"
        actionLabel="刷新"
        onAction={() => fetch()}
      />
    );
  }

  return (
    <View style={styles.container}>
      {/* ── 目标学期 ── */}
      {data.target_semester && (
        <View style={styles.semesterBar}>
          <Text style={styles.semesterLabel}>推荐学期</Text>
          <Text style={styles.semesterValue}>{data.target_semester}</Text>
        </View>
      )}

      {/* ── 推荐列表 ── */}
      <FlatList
        data={data.recommendations}
        keyExtractor={(item) => item.course_code}
        renderItem={({ item }) => <RecommendCard course={item} />}
        contentContainerStyle={styles.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => fetch(true)} tintColor="#0880D7" colors={['#0880D7']} />}
        ItemSeparatorComponent={() => <View style={styles.sep} />}
      />
    </View>
  );
}

// ============================================================
// 推荐卡片
// ============================================================

const TYPE_COLORS: Record<string, string> = {
  '必修': '#059669',
  '选修': '#7C3AED',
  '通识': '#D97706',
};

function RecommendCard({ course: c }: { course: CourseRecommendation }) {
  const typeColor = TYPE_COLORS[c.course_type] || '#6B7280';

  return (
    <View style={styles.card}>
      <View style={styles.cardTop}>
        <View style={styles.cardInfo}>
          <Text style={styles.courseName} numberOfLines={1}>{c.course_name}</Text>
          <Text style={styles.courseCode}>{c.course_code}</Text>
        </View>
        <View style={styles.badges}>
          <View style={[styles.typeBadge, { backgroundColor: typeColor + '15' }]}>
            <Text style={[styles.typeText, { color: typeColor }]}>{c.course_type}</Text>
          </View>
          <View style={styles.creditBadge}>
            <Text style={styles.creditText}>{c.credit} 学分</Text>
          </View>
        </View>
      </View>
      {c.teacher && <Text style={styles.teacher}>👨‍🏫 {c.teacher}</Text>}
      {c.reason && <Text style={styles.reason}>💬 {c.reason}</Text>}
    </View>
  );
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  semesterBar: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    backgroundColor: '#FFFFFF', paddingHorizontal: 20, paddingVertical: 14,
    borderBottomWidth: 0.5, borderBottomColor: '#E5E7EB',
  },
  semesterLabel: { fontSize: 14, color: '#6B7280' },
  semesterValue: { fontSize: 15, fontWeight: '700', color: '#0880D7' },
  list: { padding: 16, paddingBottom: 24 },
  card: {
    backgroundColor: '#FFFFFF', borderRadius: 14, padding: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3, elevation: 1,
  },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  cardInfo: { flex: 1, marginRight: 12 },
  courseName: { fontSize: 16, fontWeight: '600', color: '#111827', marginBottom: 2 },
  courseCode: { fontSize: 12, color: '#9CA3AF' },
  badges: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  typeBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  typeText: { fontSize: 11, fontWeight: '600' },
  creditBadge: { backgroundColor: '#F3F4F6', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  creditText: { fontSize: 11, color: '#6B7280', fontWeight: '500' },
  teacher: { fontSize: 13, color: '#6B7280', marginBottom: 4 },
  reason: { fontSize: 13, color: '#9CA3AF', lineHeight: 18 },
  sep: { height: 10 },
});
