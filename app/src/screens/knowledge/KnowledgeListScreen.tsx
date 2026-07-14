// ============================================================
// 知识库文件列表
// ============================================================
import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
  RefreshControl,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import type { KnowledgeFile } from '../../types/knowledge';
import { knowledgeApi } from '../../api/knowledge';
import { EmptyState } from '../../components/ui/EmptyState';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';

const CATEGORY_COLORS: Record<string, string> = {
  '培养方案': '#0880D7',
  '课程资料': '#059669',
  '考试资料': '#D97706',
  '通知公告': '#DC2626',
  '个人文件': '#7C3AED',
  '课件PPT': '#0891B2',
  '其他': '#6B7280',
};

export function KnowledgeListScreen() {
  const [files, setFiles] = useState<KnowledgeFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadFiles = useCallback(async (silent?: boolean) => {
    if (!silent) setLoading(true);
    try {
      const res = await knowledgeApi.getFiles();
      setFiles(res.data || []);
    } catch {
      if (!silent) Alert.alert('加载失败', '无法获取文件列表');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadFiles();
    }, [loadFiles]),
  );

  const handleDelete = (filename: string) => {
    Alert.alert('删除文件', `确定删除 "${filename}"？所有相关数据将被移除`, [
      { text: '取消', style: 'cancel' },
      {
        text: '删除',
        style: 'destructive',
        onPress: async () => {
          try {
            await knowledgeApi.deleteFile(filename);
            setFiles((prev) => prev.filter((f) => f.filename !== filename));
          } catch {
            Alert.alert('删除失败', '请稍后重试');
          }
        },
      },
    ]);
  };

  if (loading) return <LoadingSpinner />;

  return (
    <FlatList
      style={styles.container}
      contentContainerStyle={files.length === 0 ? styles.empty : styles.list}
      data={files}
      keyExtractor={(item) => item.filename}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => {
            setRefreshing(true);
            loadFiles(true);
          }}
        />
      }
      ListEmptyComponent={<EmptyState icon="📂" title="暂无文件" description="去上传一个吧" />}
      renderItem={({ item }) => {
        const color = CATEGORY_COLORS[item.category] || CATEGORY_COLORS['其他'];
        return (
          <TouchableOpacity
            style={styles.fileCard}
            onLongPress={() => handleDelete(item.filename)}
            activeOpacity={0.7}
          >
            <View style={styles.fileHeader}>
              <Text style={styles.fileName} numberOfLines={1}>
                {item.filename}
              </Text>
              <View style={[styles.badge, { backgroundColor: color + '18' }]}>
                <Text style={[styles.badgeText, { color }]}>
                  {item.category}
                </Text>
              </View>
            </View>
            <View style={styles.fileMeta}>
              <Text style={styles.metaText}>
                {item.file_type?.toUpperCase()} · {item.chunks ?? item.count ?? 0} 块
              </Text>
              {item.size_kb != null && (
                <Text style={styles.metaText}>
                  {item.size_kb > 1024
                    ? `${(item.size_kb / 1024).toFixed(1)} MB`
                    : `${item.size_kb} KB`}
                </Text>
              )}
            </View>
          </TouchableOpacity>
        );
      }}
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  empty: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  list: { padding: 16 },
  fileCard: {
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
  fileHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  fileName: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    marginRight: 10,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '500',
  },
  fileMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metaText: {
    fontSize: 12,
    color: '#9CA3AF',
  },
});
