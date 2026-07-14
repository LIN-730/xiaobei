// ============================================================
// 通知列表页 — 分类筛选 + 通知卡片
// ============================================================
import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  Linking,
  Alert,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import {
  notificationsApi,
  type NotificationItem,
} from '../../api/notifications';
import { EmptyState } from '../../components/ui/EmptyState';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';

const CATEGORIES = [
  { key: '', label: '全部', color: '#6B7280' },
  { key: '通知', label: '通知', color: '#0880D7' },
  { key: '文件', label: '文件', color: '#D97706' },
  { key: '消息', label: '消息', color: '#059669' },
];

function getCategoryColor(cat: string): string {
  return CATEGORIES.find((c) => c.key === cat)?.color || '#6B7280';
}

export function NotificationListScreen() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadNotifications = useCallback(
    async (silent?: boolean) => {
      if (!silent) setLoading(true);
      try {
        const res = await notificationsApi.getNotifications(
          category || undefined,
          100,
        );
        setNotifications(res.data || []);
      } catch {
        if (!silent) Alert.alert('加载失败', '无法获取通知列表');
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [category],
  );

  useFocusEffect(
    useCallback(() => {
      loadNotifications();
    }, [loadNotifications]),
  );

  const handlePress = (item: NotificationItem) => {
    if (item.link) {
      Linking.canOpenURL(item.link)
        .then((ok) => {
          if (ok) Linking.openURL(item.link);
        })
        .catch(() => {});
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <View style={styles.container}>
      {/* 分类筛选 */}
      <FlatList
        horizontal
        style={styles.filterRow}
        contentContainerStyle={styles.filterContent}
        showsHorizontalScrollIndicator={false}
        data={CATEGORIES}
        keyExtractor={(item) => item.key}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[
              styles.filterChip,
              category === item.key && styles.filterChipActive,
            ]}
            onPress={() => setCategory(item.key)}
          >
            <Text
              style={[
                styles.filterText,
                category === item.key && styles.filterTextActive,
              ]}
            >
              {item.label}
            </Text>
          </TouchableOpacity>
        )}
      />

      {/* 通知列表 */}
      <FlatList
        style={styles.list}
        contentContainerStyle={
          notifications.length === 0 ? styles.empty : styles.listContent
        }
        data={notifications}
        keyExtractor={(item) => item.id.toString()}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              loadNotifications(true);
            }}
          />
        }
        ListEmptyComponent={
          <EmptyState
            icon="📭"
            title="暂无通知"
            description={category ? `${category}分类暂无内容` : '下拉刷新试试'}
          />
        }
        renderItem={({ item }) => {
          const color = getCategoryColor(item.category);
          return (
            <TouchableOpacity
              style={styles.card}
              activeOpacity={item.link ? 0.7 : 1}
              onPress={() => handlePress(item)}
            >
              <View style={styles.cardHeader}>
                <View style={[styles.badge, { backgroundColor: color + '15' }]}>
                  <Text style={[styles.badgeText, { color }]}>
                    {item.category || '通知'}
                  </Text>
                </View>
                {item.tag ? (
                  <Text style={styles.tag}>{item.tag}</Text>
                ) : null}
                <Text style={styles.date}>{item.date}</Text>
              </View>
              <Text style={styles.title} numberOfLines={2}>
                {item.title}
              </Text>
              {item.content ? (
                <Text style={styles.content} numberOfLines={3}>
                  {item.content}
                </Text>
              ) : null}
              {item.link ? (
                <Text style={styles.linkHint}>点击查看详情 →</Text>
              ) : null}
            </TouchableOpacity>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  filterRow: {
    maxHeight: 44,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 0.5,
    borderBottomColor: '#E5E7EB',
  },
  filterContent: { paddingHorizontal: 12, alignItems: 'center' },
  filterChip: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F3F4F6',
    marginRight: 8,
  },
  filterChipActive: { backgroundColor: '#0880D7' },
  filterText: { fontSize: 13, color: '#6B7280' },
  filterTextActive: { color: '#FFFFFF', fontWeight: '500' },
  list: { flex: 1 },
  empty: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  listContent: { padding: 16 },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    marginRight: 8,
  },
  badgeText: { fontSize: 11, fontWeight: '600' },
  tag: {
    fontSize: 11,
    color: '#9CA3AF',
    flex: 1,
  },
  date: { fontSize: 11, color: '#D1D5DB' },
  title: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    lineHeight: 21,
    marginBottom: 4,
  },
  content: {
    fontSize: 13,
    color: '#6B7280',
    lineHeight: 19,
    marginTop: 4,
  },
  linkHint: {
    fontSize: 12,
    color: '#0880D7',
    marginTop: 8,
  },
});
