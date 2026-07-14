// ============================================================
// 成绩明细页 — 单课程成绩详情
// ============================================================
import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AcademicStackParamList } from '../../types/navigation';
import { scoresApi } from '../../api/scores';
import { Card } from '../../components/ui/Card';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';

type Props = NativeStackScreenProps<AcademicStackParamList, 'ScoreDetail'>;

function getScoreColor(score: string): string {
  const n = parseFloat(score);
  if (isNaN(n)) return '#6B7280';
  if (n >= 90) return '#059669';
  if (n >= 80) return '#0880D7';
  if (n >= 70) return '#D97706';
  if (n >= 60) return '#DC2626';
  return '#EF4444';
}

function getGradeColor(gp: number): string {
  if (gp >= 3.7) return '#059669';
  if (gp >= 2.7) return '#0880D7';
  if (gp >= 1.7) return '#D97706';
  if (gp > 0) return '#DC2626';
  return '#9CA3AF';
}

export function ScoreDetailScreen({ route }: Props) {
  const { courseName } = route.params;

  const { data, isLoading } = useQuery({
    queryKey: ['scoreDetail', courseName],
    queryFn: () => scoresApi.getScoreDetail(courseName),
  });

  if (isLoading) return <LoadingSpinner />;

  const details = data?.data || [];

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={
        details.length === 0 ? styles.empty : styles.content
      }
    >
      {details.length === 0 ? (
        <EmptyState icon="📋" title="暂无明细数据" description={courseName} />
      ) : (
        <>
          {details.map((d, i) => (
            <Card key={i} style={styles.card}>
              <Text style={styles.courseName}>{d.course_name}</Text>
              <View style={styles.scoreRow}>
                <View style={styles.scoreBlock}>
                  <Text style={[styles.scoreValue, { color: getScoreColor(d.score) }]}>
                    {d.score}
                  </Text>
                  <Text style={styles.scoreLabel}>成绩</Text>
                </View>
                <View style={styles.divider} />
                <View style={styles.scoreBlock}>
                  <Text style={[styles.scoreValue, { color: getGradeColor(d.grade_point) }]}>
                    {d.grade_point.toFixed(1)}
                  </Text>
                  <Text style={styles.scoreLabel}>绩点</Text>
                </View>
                <View style={styles.divider} />
                <View style={styles.scoreBlock}>
                  <Text style={styles.scoreValue}>{d.credit}</Text>
                  <Text style={styles.scoreLabel}>学分</Text>
                </View>
              </View>
              <View style={styles.metaRow}>
                <MetaItem label="学期" value={d.term} />
                <MetaItem label="类型" value={d.course_type} />
                <MetaItem label="考核" value={d.exam_type} />
              </View>
            </Card>
          ))}
        </>
      )}
    </ScrollView>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.metaItem}>
      <Text style={styles.metaLabel}>{label}</Text>
      <Text style={styles.metaValue}>{value || '-'}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  empty: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  content: { padding: 16 },
  card: { marginBottom: 12 },
  courseName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 14,
  },
  scoreRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    marginBottom: 16,
  },
  scoreBlock: { alignItems: 'center', flex: 1 },
  scoreValue: { fontSize: 26, fontWeight: '700' },
  scoreLabel: { fontSize: 12, color: '#9CA3AF', marginTop: 4 },
  divider: {
    width: 1,
    height: 36,
    backgroundColor: '#E5E7EB',
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderTopWidth: 0.5,
    borderTopColor: '#F3F4F6',
    paddingTop: 12,
  },
  metaItem: { alignItems: 'center', flex: 1 },
  metaLabel: { fontSize: 11, color: '#9CA3AF', marginBottom: 2 },
  metaValue: { fontSize: 13, color: '#374151', fontWeight: '500' },
});
