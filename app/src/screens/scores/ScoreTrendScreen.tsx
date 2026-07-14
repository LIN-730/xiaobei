// ============================================================
// 成绩趋势页 — 按学期展示 GPA 变化
// ============================================================
import React, { useMemo } from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { scoresApi } from '../../api/scores';
import type { Score } from '../../types/score';
import { Card } from '../../components/ui/Card';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';

// ============================================================
// 工具
// ============================================================

interface TermStats {
  term: string;
  count: number;
  totalCredits: number;
  avgGpa: number;
}

function computeTermStats(scores: Score[]): TermStats[] {
  const map = new Map<string, Score[]>();
  for (const s of scores) {
    const key = s.term || '未知学期';
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(s);
  }
  return Array.from(map.entries())
    .map(([term, items]) => {
      const valid = items.filter((s) => s.grade_point > 0);
      const totalGP = valid.reduce((sum, s) => sum + s.grade_point * s.credit, 0);
      const totalCredits = valid.reduce((sum, s) => sum + s.credit, 0);
      return {
        term,
        count: items.length,
        totalCredits,
        avgGpa: totalCredits > 0 ? totalGP / totalCredits : 0,
      };
    })
    .sort((a, b) => a.term.localeCompare(b.term));
}

function getGpaColor(gpa: number): string {
  if (gpa >= 3.5) return '#059669';
  if (gpa >= 3.0) return '#0880D7';
  if (gpa >= 2.5) return '#D97706';
  if (gpa >= 2.0) return '#DC2626';
  return '#EF4444';
}

// ============================================================
// ScoreTrendScreen
// ============================================================

export function ScoreTrendScreen() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['scores'],
    queryFn: () => scoresApi.getScores(),
  });

  const stats = useMemo(() => {
    if (!data?.data) return [];
    return computeTermStats(data.data);
  }, [data]);

  const maxGpa = Math.max(...stats.map((s) => s.avgGpa), 4.0);

  if (isLoading) return <LoadingSpinner fullScreen />;

  if (isError || !data) {
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

  if (stats.length === 0) {
    return (
      <EmptyState
        icon="📈"
        title="暂无成绩数据"
        description="同步教务数据后将展示 GPA 趋势"
      />
    );
  }

  const overallGpa = data.gpa_stats?.avg_gpa ?? 0;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* 总览 */}
      <Card style={styles.overviewCard}>
        <Text style={styles.overviewTitle}>累计平均绩点</Text>
        <Text style={[styles.overviewGpa, { color: getGpaColor(overallGpa) }]}>
          {overallGpa.toFixed(2)}
        </Text>
        <Text style={styles.overviewMeta}>
          {stats.length} 个学期 · {data.gpa_stats?.total_credits.toFixed(1) ?? 0} 学分
        </Text>
      </Card>

      {/* 趋势列表 */}
      <Card style={styles.trendCard}>
        <Text style={styles.sectionTitle}>学期 GPA 趋势</Text>
        {stats.map((item, idx) => {
          const barWidth = Math.max((item.avgGpa / maxGpa) * 100, 4);
          const isLast = idx === stats.length - 1;
          return (
            <View
              key={item.term}
              style={[styles.trendRow, isLast && styles.trendRowLast]}
            >
              <View style={styles.trendHeader}>
                <Text style={styles.trendTerm}>{item.term}</Text>
                <Text style={[styles.trendGpa, { color: getGpaColor(item.avgGpa) }]}>
                  {item.avgGpa.toFixed(2)}
                </Text>
              </View>
              <View style={styles.barTrack}>
                <View
                  style={[
                    styles.barFill,
                    {
                      width: `${barWidth}%`,
                      backgroundColor: getGpaColor(item.avgGpa),
                    },
                  ]}
                />
              </View>
              <Text style={styles.trendMeta}>
                {item.count} 门课 · {item.totalCredits.toFixed(1)} 学分
              </Text>
            </View>
          );
        })}
      </Card>
    </ScrollView>
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
  overviewCard: {
    alignItems: 'center',
    marginBottom: 16,
    paddingVertical: 24,
  },
  overviewTitle: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 8,
  },
  overviewGpa: {
    fontSize: 40,
    fontWeight: '800',
    marginBottom: 8,
  },
  overviewMeta: {
    fontSize: 13,
    color: '#9CA3AF',
  },
  trendCard: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  trendRow: {
    paddingBottom: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#F3F4F6',
    marginBottom: 16,
  },
  trendRowLast: {
    borderBottomWidth: 0,
    marginBottom: 0,
    paddingBottom: 0,
  },
  trendHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  trendTerm: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  trendGpa: {
    fontSize: 17,
    fontWeight: '700',
  },
  barTrack: {
    height: 6,
    backgroundColor: '#E5E7EB',
    borderRadius: 3,
    marginBottom: 6,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 3,
  },
  trendMeta: {
    fontSize: 12,
    color: '#9CA3AF',
  },
});
