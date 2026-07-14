// ============================================================
// 通用卡片组件
// ============================================================
import React from 'react';
import { View, StyleSheet, type ViewProps, type StyleProp, type ViewStyle } from 'react-native';

interface CardProps extends ViewProps {
  children: React.ReactNode;
  /** 是否显示阴影 */
  elevated?: boolean;
  /** 内边距 */
  padding?: number;
  style?: StyleProp<ViewStyle>;
}

export function Card({
  children,
  elevated = true,
  padding = 16,
  style,
  ...props
}: CardProps) {
  return (
    <View
      style={[
        styles.card,
        elevated && styles.elevated,
        { padding },
        style,
      ]}
      {...props}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
  },
  elevated: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
});
