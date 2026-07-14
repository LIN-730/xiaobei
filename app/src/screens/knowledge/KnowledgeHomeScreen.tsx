// ============================================================
// 知识库主页 — 入口卡片（类似 PlanningHomeScreen）
// ============================================================
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AcademicStackParamList } from '../../types';
import { knowledgeApi } from '../../api/knowledge';
import type { KnowledgeStats } from '../../types/knowledge';

type Props = NativeStackScreenProps<AcademicStackParamList, 'KnowledgeHome'>;

interface KnowledgeCard {
  key: string;
  icon: string;
  title: string;
  description: string;
  screen: keyof AcademicStackParamList;
  color: string;
}

const CARDS: KnowledgeCard[] = [
  {
    key: 'files',
    icon: '📁',
    title: '我的文件',
    description: '查看和管理已上传的知识库文件',
    screen: 'KnowledgeList',
    color: '#0880D7',
  },
  {
    key: 'upload',
    icon: '⬆️',
    title: '上传文件',
    description: '上传 PDF/Word/PPT 等文档到知识库',
    screen: 'KnowledgeUpload',
    color: '#059669',
  },
  {
    key: 'search',
    icon: '🔍',
    title: '知识搜索',
    description: '语义搜索已索引的文档内容',
    screen: 'KnowledgeSearch',
    color: '#7C3AED',
  },
];

export function KnowledgeHomeScreen({ navigation }: Props) {
  const [stats, setStats] = useState<KnowledgeStats | null>(null);

  useEffect(() => {
    knowledgeApi.getStats().then(setStats).catch(() => {});
  }, []);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
    >
      {/* 统计摘要 */}
      {stats && (
        <View style={[styles.statsCard, styles.cardShadow]}>
          <Text style={styles.statsTitle}>知识库概览</Text>
          <View style={styles.statsRow}>
            <StatItem label="文件数" value={`${stats.total_sources}`} />
            <StatItem label="文本块" value={`${stats.total_chunks}`} />
            <StatItem label="分类" value={`${Object.keys(stats.categories).length}`} />
          </View>
        </View>
      )}

      <Text style={styles.subtitle}>选择一项操作管理你的知识库</Text>

      {CARDS.map((card) => (
        <TouchableOpacity
          key={card.key}
          style={[styles.card, styles.cardShadow]}
          onPress={() => navigation.navigate(card.screen as any)}
          activeOpacity={0.7}
        >
          <View
            style={[styles.iconWrap, { backgroundColor: card.color + '15' }]}
          >
            <Text style={styles.icon}>{card.icon}</Text>
          </View>
          <View style={styles.cardBody}>
            <Text style={styles.cardTitle}>{card.title}</Text>
            <Text style={styles.cardDesc}>{card.description}</Text>
          </View>
          <Text style={styles.arrow}>›</Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

function StatItem({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.statItem}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  content: { padding: 16, paddingTop: 12 },
  statsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  statsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: { alignItems: 'center' },
  statValue: { fontSize: 22, fontWeight: '700', color: '#0880D7' },
  statLabel: { fontSize: 12, color: '#9CA3AF', marginTop: 4 },
  subtitle: {
    fontSize: 14,
    color: '#9CA3AF',
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  cardShadow: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  iconWrap: {
    width: 48,
    height: 48,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  icon: { fontSize: 22 },
  cardBody: { flex: 1 },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  cardDesc: { fontSize: 13, color: '#9CA3AF', lineHeight: 18 },
  arrow: {
    fontSize: 24,
    color: '#D1D5DB',
    fontWeight: '300',
    marginLeft: 8,
  },
});
