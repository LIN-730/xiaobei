// ============================================================
// 学业规划主页 — 4 个规划模块入口
// ============================================================
import React from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AcademicStackParamList } from '../../types';

type Props = NativeStackScreenProps<AcademicStackParamList, 'PlanningHome'>;

// ============================================================
// 入口卡片
// ============================================================

interface PlanCard {
  key: string;
  icon: string;
  title: string;
  description: string;
  screen: keyof AcademicStackParamList;
  color: string;
}

const PLAN_CARDS: PlanCard[] = [
  {
    key: 'credit-gap',
    icon: '📊',
    title: '学分缺口',
    description: '查看各模块学分完成情况与剩余学分',
    screen: 'CreditGap',
    color: '#0880D7',
  },
  {
    key: 'required',
    icon: '✅',
    title: '必修课检查',
    description: '核对培养方案中必修课的完成状态',
    screen: 'RequiredCourses',
    color: '#059669',
  },
  {
    key: 'recommend',
    icon: '💡',
    title: '选课推荐',
    description: '基于学业进度智能推荐下期课程',
    screen: 'Recommend',
    color: '#D97706',
  },
  {
    key: 'path',
    icon: '🗺️',
    title: '学业路径',
    description: '按学期规划剩余学业的修读路径',
    screen: 'PathPlan',
    color: '#7C3AED',
  },
];

// ============================================================
// 主组件
// ============================================================

export function PlanningHomeScreen({ navigation }: Props) {
  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
    >
      <Text style={styles.subtitle}>选择一项规划工具，开始分析你的学业进度</Text>

      {PLAN_CARDS.map((card) => (
        <TouchableOpacity
          key={card.key}
          style={[styles.card, styles.cardShadow]}
          onPress={() =>
            navigation.navigate(card.screen as any)
          }
          activeOpacity={0.7}
        >
          <View style={[styles.iconWrap, { backgroundColor: card.color + '15' }]}>
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

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  content: {
    padding: 16,
    paddingTop: 12,
  },
  subtitle: {
    fontSize: 14,
    color: '#9CA3AF',
    marginBottom: 20,
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
  icon: {
    fontSize: 22,
  },
  cardBody: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  cardDesc: {
    fontSize: 13,
    color: '#9CA3AF',
    lineHeight: 18,
  },
  arrow: {
    fontSize: 24,
    color: '#D1D5DB',
    fontWeight: '300',
    marginLeft: 8,
  },
});
