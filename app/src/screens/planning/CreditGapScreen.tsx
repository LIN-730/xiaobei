// ============================================================
// 学分缺口分析页面
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
import type { CreditGapModule, CreditGapResponse } from '../../types';

export function CreditGapScreen() {
  const [data, setData] = useState<CreditGapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);
      const res = await planningApi.getCreditGap();
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  if (loading) return <LoadingSpinner message="加载学分数据..." fullScreen />;
  if (error && !data) return <EmptyState icon="⚠️" title="加载失败" description={error} actionLabel="重试" onAction={() => fetch()} />;
  if (!data || data.modules.length === 0) return <EmptyState icon="📊" title="暂无数据" description="请先同步教务数据" />;

  const percentage = data.total_required > 0
    ? Math.round((data.total_earned / data.total_required) * 100)
    : 0;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => fetch(true)} tintColor="#0880D7" colors={['#0880D7']} />}
    >
      {/* ── 总览卡片 ── */}
      <View style={styles.overviewCard}>
        <Text style={styles.overviewTitle}>总学分进度</Text>
        <View style={styles.progressBarBg}>
          <View style={[styles.progressBarFill, { width: `${Math.min(percentage, 100)}%` as any }]} />
        </View>
        <View style={styles.overviewRow}>
          <View style={styles.overviewItem}>
            <Text style={styles.overviewValue}>{data.total_earned}</Text>
            <Text style={styles.overviewLabel}>已修</Text>
          </View>
          <View style={styles.overviewItem}>
            <Text style={[styles.overviewValue, { color: '#EF4444' }]}>{data.total_remaining}</Text>
            <Text style={styles.overviewLabel}>剩余</Text>
          </View>
          <View style={styles.overviewItem}>
            <Text style={styles.overviewValue}>{data.total_required}</Text>
            <Text style={styles.overviewLabel}>要求</Text>
          </View>
        </View>
        <Text style={styles.percentage}>{percentage}% 完成</Text>
      </View>

      {/* ── 各模块明细 ── */}
      <Text style={styles.sectionTitle}>模块明细</Text>
      {data.modules.map((mod: CreditGapModule) => (
        <ModuleCard key={mod.module_name} module={mod} />
      ))}
    </ScrollView>
  );
}

// ============================================================
// 模块卡片
// ============================================================

function ModuleCard({ module: m }: { module: CreditGapModule }) {
  const pct = m.required > 0 ? Math.round((m.earned / m.required) * 100) : 0;
  const done = m.remaining <= 0;

  return (
    <View style={[styles.moduleCard, done && styles.moduleCardDone]}>
      <View style={styles.moduleHeader}>
        <Text style={styles.moduleName}>{m.module_name}</Text>
        <Text style={[styles.moduleStatus, done && styles.moduleStatusDone]}>
          {done ? '✅ 已完成' : `${m.remaining} 学分待修`}
        </Text>
      </View>
      <View style={styles.moduleProgressBg}>
        <View
          style={[
            styles.moduleProgressFill,
            { width: `${Math.min(pct, 100)}%` as any },
            done && styles.moduleProgressFillDone,
          ]}
        />
      </View>
      <View style={styles.moduleFooter}>
        <Text style={styles.moduleDetail}>已修: {m.earned}</Text>
        <Text style={styles.moduleDetail}>要求: {m.required}</Text>
        {!done && <Text style={styles.moduleDetail}>剩余: {m.remaining}</Text>}
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
  overviewCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.06, shadowRadius: 4, elevation: 2,
  },
  overviewTitle: { fontSize: 17, fontWeight: '700', color: '#111827', marginBottom: 16 },
  progressBarBg: { height: 10, backgroundColor: '#F3F4F6', borderRadius: 5, marginBottom: 16, overflow: 'hidden' },
  progressBarFill: { height: '100%', backgroundColor: '#0880D7', borderRadius: 5 },
  overviewRow: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 12 },
  overviewItem: { alignItems: 'center' },
  overviewValue: { fontSize: 22, fontWeight: '700', color: '#111827' },
  overviewLabel: { fontSize: 12, color: '#9CA3AF', marginTop: 2 },
  percentage: { textAlign: 'center', fontSize: 14, color: '#0880D7', fontWeight: '600' },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#111827', marginBottom: 12 },
  // 模块卡片
  moduleCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 16,
    marginBottom: 10,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.04, shadowRadius: 3, elevation: 1,
  },
  moduleCardDone: { opacity: 0.7 },
  moduleHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  moduleName: { fontSize: 15, fontWeight: '600', color: '#111827' },
  moduleStatus: { fontSize: 12, color: '#EF4444', fontWeight: '500' },
  moduleStatusDone: { color: '#059669' },
  moduleProgressBg: { height: 6, backgroundColor: '#F3F4F6', borderRadius: 3, marginBottom: 10, overflow: 'hidden' },
  moduleProgressFill: { height: '100%', backgroundColor: '#0880D7', borderRadius: 3 },
  moduleProgressFillDone: { backgroundColor: '#059669' },
  moduleFooter: { flexDirection: 'row', gap: 16 },
  moduleDetail: { fontSize: 12, color: '#6B7280' },
});
