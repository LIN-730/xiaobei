// ============================================================
// 根导航 — 鉴权门禁 (AuthStack vs MainTabs)
// ============================================================
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { useAuthStore } from '../stores/authStore';
import { AuthStack } from './AuthStack';
import { MainTabs } from './MainTabs';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';

export function RootNavigator() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isInitialized = useAuthStore((s) => s.isInitialized);

  // 应用启动初始化中
  if (!isInitialized) {
    return <LoadingSpinner message="正在加载..." fullScreen />;
  }

  return (
    <NavigationContainer>
      {isAuthenticated ? <MainTabs /> : <AuthStack />}
    </NavigationContainer>
  );
}
