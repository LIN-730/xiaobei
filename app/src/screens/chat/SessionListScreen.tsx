// ============================================================
// AI 会话列表页面
// ============================================================
import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  Alert,
  RefreshControl,
  StyleSheet,
  Platform,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { agentApi } from '../../api/agent';
import { EmptyState } from '../../components/ui/EmptyState';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import type { AgentSession, ChatStackParamList } from '../../types';

type Props = NativeStackScreenProps<ChatStackParamList, 'SessionList'>;

// ============================================================
// 相对时间格式化
// ============================================================

function formatRelativeTime(isoStr: string): string {
  const date = new Date(isoStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  // 客户端时间可能快于服务器，负值视为"刚刚"
  if (diffMs < 0) return '刚刚';
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMs / 3600000);
  const diffDay = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return '刚刚';
  if (diffMin < 60) return `${diffMin}分钟前`;
  if (diffHour < 24) return `${diffHour}小时前`;
  if (diffDay < 7) return `${diffDay}天前`;

  const month = date.getMonth() + 1;
  const day = date.getDate();
  return `${month}/${day}`;
}

// ============================================================
// 会话卡片
// ============================================================

interface SessionCardProps {
  session: AgentSession;
  onPress: () => void;
  onDelete: () => void;
}

function SessionCard({ session, onPress, onDelete }: SessionCardProps) {
  const handleLongPress = () => {
    Alert.alert(
      '删除会话',
      `确定要删除「${session.title || '新对话'}」吗？\n消息记录将一并删除。`,
      [
        { text: '取消', style: 'cancel' },
        { text: '删除', style: 'destructive', onPress: onDelete },
      ],
    );
  };

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      onLongPress={handleLongPress}
      activeOpacity={0.6}
    >
      <View style={styles.cardContent}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle} numberOfLines={1}>
            {session.title || '新对话'}
          </Text>
          <Text style={styles.cardTime}>
            {formatRelativeTime(session.updated_at)}
          </Text>
        </View>
        {session.last_message_preview ? (
          <Text style={styles.cardPreview} numberOfLines={2}>
            {session.last_message_preview}
          </Text>
        ) : null}
        <View style={styles.cardFooter}>
          <View style={styles.countBadge}>
            <Text style={styles.countText}>
              {session.message_count} 条消息
            </Text>
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

// ============================================================
// 会话列表主组件
// ============================================================

export function SessionListScreen({ navigation }: Props) {
  const [sessions, setSessions] = useState<AgentSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const data = await agentApi.getSessions(100, 0);
      setSessions(data.sessions);
    } catch (err) {
      const msg = err instanceof Error ? err.message : '加载失败';
      setError(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // 每次 tab 聚焦时刷新列表
  useFocusEffect(
    useCallback(() => {
      fetchSessions();
    }, [fetchSessions]),
  );

  const handleDelete = useCallback(
    async (sessionKey: string) => {
      try {
        await agentApi.deleteSession(sessionKey);
        setSessions((prev) => prev.filter((s) => s.session_key !== sessionKey));
      } catch (err) {
        Alert.alert('删除失败', '请稍后重试');
      }
    },
    [],
  );

  const handleNewChat = useCallback(() => {
    navigation.navigate('Chat', {});
  }, [navigation]);

  const handleOpenChat = useCallback(
    (session: AgentSession) => {
      navigation.navigate('Chat', {
        sessionKey: session.session_key,
        title: session.title,
      });
    },
    [navigation],
  );

  // ── 错误状态 ──
  if (error && sessions.length === 0) {
    return (
      <View style={styles.container}>
        <EmptyState
          icon="⚠️"
          title="加载失败"
          description={error}
          actionLabel="重试"
          onAction={() => fetchSessions()}
        />
      </View>
    );
  }

  // ── 加载中 ──
  if (loading && sessions.length === 0) {
    return (
      <View style={styles.container}>
        <LoadingSpinner message="加载会话列表..." fullScreen />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* ── 顶部操作栏 ── */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>AI 助手</Text>
        <TouchableOpacity
          style={styles.newChatBtn}
          onPress={handleNewChat}
          activeOpacity={0.7}
        >
          <Text style={styles.newChatBtnText}>+ 新对话</Text>
        </TouchableOpacity>
      </View>

      {/* ── 列表 ── */}
      {sessions.length === 0 ? (
        <EmptyState
          icon="🤖"
          title="开始与 AI 助手对话"
          description="你可以询问课表、成绩、考试安排，或让 AI 帮你规划学业"
          actionLabel="开始新对话"
          onAction={handleNewChat}
        />
      ) : (
        <FlatList
          data={sessions}
          keyExtractor={(item) => item.session_key}
          renderItem={({ item }) => (
            <SessionCard
              session={item}
              onPress={() => handleOpenChat(item)}
              onDelete={() => handleDelete(item.session_key)}
            />
          )}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => fetchSessions(true)}
              tintColor="#0880D7"
              colors={['#0880D7']}
            />
          }
          ItemSeparatorComponent={() => <View style={styles.separator} />}
        />
      )}
    </View>
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 0.5,
    borderBottomColor: '#E5E7EB',
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: '#111827',
  },
  newChatBtn: {
    backgroundColor: '#0880D7',
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 8,
  },
  newChatBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
  },
  list: {
    paddingVertical: 8,
  },
  card: {
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    borderRadius: 12,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.05,
        shadowRadius: 3,
      },
      android: {
        elevation: 1,
      },
    }),
  },
  cardContent: {
    padding: 16,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    flex: 1,
    marginRight: 12,
  },
  cardTime: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  cardPreview: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 10,
  },
  cardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  countBadge: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  countText: {
    fontSize: 11,
    color: '#9CA3AF',
    fontWeight: '500',
  },
  separator: {
    height: 10,
  },
});
