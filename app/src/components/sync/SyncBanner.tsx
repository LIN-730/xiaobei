// ============================================================
// 同步状态横幅 — 自包含组件 (无 props)
// 使用 @tanstack/react-query 管理同步状态轮询
// ============================================================
import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  ActivityIndicator,
  TouchableOpacity,
  StyleSheet,
  Animated,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { syncApi } from '../../api/sync';
import type { SyncStatusResponse } from '../../types/api';

// ============================================================
// 状态 → UI 配置映射
// ============================================================

const STATUS_CONFIG: Record<
  SyncStatusResponse['status'],
  { bg: string; text: string; icon: string }
> = {
  never_synced: {
    bg: '#FEF3C8',
    text: '#92400E',
    icon: '⚠️',
  },
  running: {
    bg: '#DBEAFE',
    text: '#1E40AF',
    icon: '🔄',
  },
  success: {
    bg: '#D1FAE5',
    text: '#065F46',
    icon: '✅',
  },
  failed: {
    bg: '#FEE2E2',
    text: '#991B1B',
    icon: '❌',
  },
};

// ============================================================
// SyncBanner 组件
// ============================================================

export function SyncBanner() {
  const queryClient = useQueryClient();
  const [isVisible, setIsVisible] = useState(true);
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 查询同步状态 — running 时每 2s 轮询
  const {
    data: status,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['syncStatus'],
    queryFn: () => syncApi.getStatus(),
    refetchInterval: (query) =>
      query.state.data?.status === 'running' ? 2000 : false,
    staleTime: 5000,
  });

  // 触发同步 mutation
  const triggerMutation = useMutation({
    mutationFn: () => syncApi.trigger(),
    onSuccess: () => {
      refetch();
    },
    onError: (error: unknown) => {
      // 409 → 已有同步在执行中
      if (isHttpError(error, 409)) {
        refetch();
      }
    },
    onSettled: () => {
      // 同步完成后刷新仪表盘
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });

  // success → 3s 后自动消失；其他状态 → 立即显示
  useEffect(() => {
    if (status?.status === 'success') {
      setIsVisible(true);
      fadeAnim.setValue(1);
      timerRef.current = setTimeout(() => {
        Animated.timing(fadeAnim, {
          toValue: 0,
          duration: 300,
          useNativeDriver: true,
        }).start(() => setIsVisible(false));
      }, 3000);
    } else {
      setIsVisible(true);
      fadeAnim.setValue(1);
    }

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [status?.status, fadeAnim]);

  // 首次查询未返回或出错 → 不显示
  if (isError || !status) return null;
  if (!isVisible) return null;

  const config = STATUS_CONFIG[status.status];
  const showButton = status.status === 'never_synced' || status.status === 'failed';
  const showSpinner = triggerMutation.isPending || status.status === 'running';

  const message =
    status.status === 'failed' && status.error_msg
      ? `同步失败: ${status.error_msg}`
      : status.status === 'never_synced'
        ? '尚未同步教务数据，请立即同步以获取最新课表与成绩'
        : status.status === 'running'
          ? '正在同步教务数据...'
          : '同步成功';

  return (
    <Animated.View
      style={[
        styles.banner,
        { backgroundColor: config.bg, opacity: fadeAnim },
      ]}
    >
      <View style={styles.content}>
        {showSpinner ? (
          <ActivityIndicator
            size="small"
            color={config.text}
            style={styles.spinner}
          />
        ) : (
          <Text style={styles.icon}>{config.icon}</Text>
        )}
        <Text
          style={[styles.message, { color: config.text }]}
          numberOfLines={2}
        >
          {message}
        </Text>
      </View>
      {showButton && (
        <TouchableOpacity
          style={[styles.actionButton, { borderColor: config.text }]}
          onPress={() => triggerMutation.mutate()}
          disabled={triggerMutation.isPending}
          activeOpacity={0.7}
        >
          <Text style={[styles.actionText, { color: config.text }]}>
            {status.status === 'never_synced' ? '立即同步' : '重试'}
          </Text>
        </TouchableOpacity>
      )}
    </Animated.View>
  );
}

// ============================================================
// Helpers
// ============================================================

function isHttpError(err: unknown, status: number): boolean {
  return (
    typeof err === 'object' &&
    err !== null &&
    'response' in err &&
    typeof (err as { response?: { status?: number } }).response?.status ===
      'number' &&
    (err as { response: { status: number } }).response.status === status
  );
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 12,
    marginBottom: 12,
    minHeight: 44,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginRight: 8,
  },
  icon: {
    fontSize: 14,
    marginRight: 8,
  },
  spinner: {
    marginRight: 8,
  },
  message: {
    fontSize: 13,
    lineHeight: 18,
    flex: 1,
  },
  actionButton: {
    borderWidth: 1,
    borderRadius: 8,
    paddingVertical: 5,
    paddingHorizontal: 12,
    flexShrink: 0,
  },
  actionText: {
    fontSize: 13,
    fontWeight: '600',
  },
});
