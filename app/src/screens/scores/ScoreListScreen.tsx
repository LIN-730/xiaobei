// ============================================================
// 成绩列表页 — 学期筛选 + GPA 统计卡片 + 成绩列表
// ============================================================
import React, { useCallback, useMemo, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { scoresApi } from '../../api/scores';
import type { Score } from '../../types/score';
import type { AcademicStackParamList } from '../../types/navigation';
import { Card } from '../../components/ui/Card';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';

type Nav = NativeStackNavigationProp<AcademicStackParamList, 'ScoreList'>;

// ============================================================
// 绩点→颜色映射
// ============================================================

function getGradeColor(gradePoint: number): string {
  if (gradePoint >= 3.7) return '#059669';
  if (gradePoint >= 2.7) return '#0880D7';
  if (gradePoint >= 1.7) return '#D97706';
  if (gradePoint > 0) return '#DC2626';
  return '#9CA3AF';
}

function getScoreColor(score: string): string {
  const n = parseFloat(score);
  if (isNaN(n)) return '#6B7280';
  if (n >= 90) return '#059669';
  if (n >= 80) return '#0880D7';
  if (n >= 70) return '#D97706';
  if (n >= 60) return '#DC2626';
  return '#EF4444';
}

// ============================================================
// ScoreListScreen
// ============================================================

export function ScoreListScreen() {
  const navigation = useNavigation<Nav>();
  const [selectedTerm, setSelectedTerm] = useState<string | undefined>();

  // 头部入口按钮（知识库 + 规划）
  useFocusEffect(
    useCallback(() => {
      navigation.setOptions({
        headerRight: () => (
          <View style={{ flexDirection: 'row', alignItems: 'center', marginRight: 4 }}>
            <TouchableOpacity
              onPress={() => navigation.navigate('KnowledgeHome')}
              activeOpacity={0.7}
              style={{ paddingHorizontal: 10, paddingVertical: 5, backgroundColor: '#7C3AED', borderRadius: 8, marginRight: 6 }}
            >
              <Text style={{ color: '#FFFFFF', fontSize: 13, fontWeight: '600' }}>知识库</Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => navigation.navigate('GpaSimulator')}
              activeOpacity={0.7}
              style={{ paddingHorizontal: 10, paddingVertical: 5, backgroundColor: '#059669', borderRadius: 8, marginRight: 6 }}
            >
              <Text style={{ color: '#FFFFFF', fontSize: 13, fontWeight: '600' }}>模拟</Text>
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => navigation.navigate('PlanningHome')}
              activeOpacity={0.7}
              style={{ paddingHorizontal: 10, paddingVertical: 5, backgroundColor: '#0880D7', borderRadius: 8 }}
            >
              <Text style={{ color: '#FFFFFF', fontSize: 13, fontWeight: '600' }}>规划</Text>
            </TouchableOpacity>
          </View>
        ),
      });
    }, [navigation]),
  );

  // 学期列表
  const {
    data: termsData,
    isLoading: termsLoading,
  } = useQuery({
    queryKey: ['scoreTerms'],
    queryFn: () => scoresApi.getTerms(),
    staleTime: 300000,
  });

  // 成绩数据
  const {
    data: scoresData,
    isLoading: scoresLoading,
    isError,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['scores', selectedTerm],
    queryFn: () => scoresApi.getScores(selectedTerm),
  });

  const terms = termsData?.data ?? [];
  const scores = scoresData?.data ?? [];
  const gpa = scoresData?.gpa_stats;

  // 无数据（首次未同步）
  const hasNoData = !scoresLoading && !isError && scores.length === 0;

  if (termsLoading || scoresLoading) {
    return <LoadingSpinner fullScreen />;
  }

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

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={refetch} />}
    >
      {/* 学期筛选 */}
      {terms.length > 0 && (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.filterScroll}
          contentContainerStyle={styles.filterContent}
        >
          <TouchableOpacity
            style={[
              styles.filterChip,
              !selectedTerm && styles.filterChipActive,
            ]}
            onPress={() => setSelectedTerm(undefined)}
            activeOpacity={0.7}
          >
            <Text
              style={[
                styles.filterChipText,
                !selectedTerm && styles.filterChipTextActive,
              ]}
            >
              全部
            </Text>
          </TouchableOpacity>
          {terms.map((term) => (
            <TouchableOpacity
              key={term}
              style={[
                styles.filterChip,
                selectedTerm === term && styles.filterChipActive,
              ]}
              onPress={() =>
                setSelectedTerm(selectedTerm === term ? undefined : term)
              }
              activeOpacity={0.7}
            >
              <Text
                style={[
                  styles.filterChipText,
                  selectedTerm === term && styles.filterChipTextActive,
                ]}
              >
                {term}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      {/* GPA 统计卡片 */}
      {gpa && (
        <View style={styles.gpaRow}>
          <Card style={styles.gpaCard}>
            <Text style={styles.gpaLabel}>总学分</Text>
            <Text style={[styles.gpaValue, { color: '#0880D7' }]}>
              {gpa.total_credits.toFixed(1)}
            </Text>
          </Card>
          <Card style={styles.gpaCard}>
            <Text style={styles.gpaLabel}>平均绩点</Text>
            <Text style={[styles.gpaValue, { color: '#7C3AED' }]}>
              {gpa.avg_gpa.toFixed(2)}
            </Text>
          </Card>
          <Card style={styles.gpaCard}>
            <Text style={styles.gpaLabel}>课程数</Text>
            <Text style={[styles.gpaValue, { color: '#059669' }]}>
              {scoresData?.total ?? scores.length}
            </Text>
          </Card>
          {/* 趋势入口 */}
          <TouchableOpacity
            style={styles.gpaCardTouch}
            onPress={() => navigation.navigate('ScoreTrend')}
            activeOpacity={0.7}
          >
            <Card style={styles.gpaCardInner}>
              <Text style={styles.gpaLabel}>GPA 趋势</Text>
              <Text style={styles.gpaArrow}>📈</Text>
            </Card>
          </TouchableOpacity>
        </View>
      )}

      {/* 成绩列表 */}
      {scores.length > 0 ? (
        <Card style={styles.listCard}>
          <Text style={styles.listTitle}>
            课程成绩 ({scores.length})
          </Text>
          {scores.map((item, idx) => (
            <ScoreRow
              key={`${item.course_code}-${idx}`}
              score={item}
              onPress={() =>
                navigation.navigate('ScoreDetail', { courseName: item.course_name })
              }
            />
          ))}
        </Card>
      ) : hasNoData ? (
        <EmptyState
          icon="📊"
          title="暂无成绩数据"
          description="请先同步教务数据以获取成绩"
        />
      ) : null}
    </ScrollView>
  );
}

// ============================================================
// 成绩行
// ============================================================

function ScoreRow({ score, onPress }: { score: Score; onPress: () => void }) {
  return (
    <TouchableOpacity style={styles.scoreRow} onPress={onPress} activeOpacity={0.6}>
      <View style={styles.scoreLeft}>
        <Text style={styles.courseName} numberOfLines={1}>
          {score.course_name}
        </Text>
        <Text style={styles.courseMeta}>
          {score.course_type} · {score.credit.toFixed(1)}学分
          {score.term ? ` · ${score.term}` : ''}
        </Text>
      </View>
      <View style={styles.scoreRight}>
        <Text style={[styles.scoreValue, { color: getScoreColor(score.score) }]}>
          {score.score}
        </Text>
        {score.grade_point > 0 && (
          <Text style={[styles.gradePoint, { color: getGradeColor(score.grade_point) }]}>
            GPA {score.grade_point.toFixed(1)}
          </Text>
        )}
      </View>
    </TouchableOpacity>
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

  // 学期筛选
  filterScroll: {
    marginBottom: 12,
  },
  filterContent: {
    gap: 8,
    paddingRight: 16,
  },
  filterChip: {
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  filterChipActive: {
    backgroundColor: '#0880D7',
    borderColor: '#0880D7',
  },
  filterChipText: {
    fontSize: 13,
    color: '#374151',
    fontWeight: '500',
  },
  filterChipTextActive: {
    color: '#FFFFFF',
  },

  // GPA 卡片
  gpaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 16,
  },
  gpaCard: {
    flex: 1,
    minWidth: '30%',
    alignItems: 'center',
  },
  gpaLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 6,
  },
  gpaValue: {
    fontSize: 22,
    fontWeight: '700',
  },
  gpaCardTouch: {
    flex: 1,
    minWidth: '30%',
  },
  gpaCardInner: {
    alignItems: 'center',
  },
  gpaArrow: {
    fontSize: 22,
  },

  // 成绩列表
  listCard: {
    marginBottom: 16,
  },
  listTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  scoreRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#F3F4F6',
  },
  scoreLeft: {
    flex: 1,
    marginRight: 12,
  },
  courseName: {
    fontSize: 15,
    fontWeight: '500',
    color: '#111827',
    marginBottom: 3,
  },
  courseMeta: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  scoreRight: {
    alignItems: 'flex-end',
  },
  scoreValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  gradePoint: {
    fontSize: 12,
    fontWeight: '500',
    marginTop: 2,
  },
});
