// ============================================================
// App 入口 — 教务智能助手 (小北)
// ============================================================
import './global.css';
import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RootNavigator } from './src/app/RootNavigator';
import { useAuthStore } from './src/stores/authStore';

// TanStack Query 客户端配置
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 分钟内视为新鲜
      gcTime: 30 * 60 * 1000, // 30 分钟后回收缓存 (v5: gcTime 替代 cacheTime)
      refetchOnWindowFocus: false, // RN 不适用
    },
    mutations: {
      retry: 0,
    },
  },
});

function AppContent() {
  const initialize = useAuthStore((s) => s.initialize);

  useEffect(() => {
    initialize();
  }, [initialize]);

  return <RootNavigator />;
}

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <StatusBar style="dark" />
        <AppContent />
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
