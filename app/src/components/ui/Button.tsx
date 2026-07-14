// ============================================================
// 通用按钮组件
// ============================================================
import React from 'react';
import {
  TouchableOpacity,
  Text,
  ActivityIndicator,
  StyleSheet,
  type TouchableOpacityProps,
  type StyleProp,
  type ViewStyle,
  type TextStyle,
} from 'react-native';

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends TouchableOpacityProps {
  title: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  disabled?: boolean;
  style?: StyleProp<ViewStyle>;
  textStyle?: StyleProp<TextStyle>;
}

export function Button({
  title,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  style,
  textStyle,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <TouchableOpacity
      style={[
        baseStyles.button,
        variantStyles[variant],
        sizeStyles[size],
        isDisabled && baseStyles.disabled,
        style,
      ]}
      disabled={isDisabled}
      activeOpacity={0.7}
      {...props}
    >
      {loading ? (
        <ActivityIndicator
          size="small"
          color={variant === 'outline' || variant === 'ghost' ? '#0880D7' : '#FFFFFF'}
        />
      ) : (
        <Text
          style={[
            baseStyles.text,
            variantTextStyles[variant],
            sizeTextStyles[size],
            isDisabled && baseStyles.disabledText,
            textStyle,
          ]}
        >
          {title}
        </Text>
      )}
    </TouchableOpacity>
  );
}

// ============================================================
// Styles
// ============================================================
const baseStyles = StyleSheet.create({
  button: {
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  text: {
    fontWeight: '600',
  },
  disabled: {
    opacity: 0.5,
  },
  disabledText: {
    opacity: 0.5,
  },
});

const variantStyles: Record<ButtonVariant, ViewStyle> = {
  primary: {
    backgroundColor: '#0880D7',
  },
  secondary: {
    backgroundColor: '#E6F4FE',
  },
  outline: {
    backgroundColor: 'transparent',
    borderWidth: 1.5,
    borderColor: '#0880D7',
  },
  ghost: {
    backgroundColor: 'transparent',
  },
  danger: {
    backgroundColor: '#EF4444',
  },
};

const variantTextStyles: Record<ButtonVariant, TextStyle> = {
  primary: { color: '#FFFFFF' },
  secondary: { color: '#0880D7' },
  outline: { color: '#0880D7' },
  ghost: { color: '#0880D7' },
  danger: { color: '#FFFFFF' },
};

const sizeStyles: Record<ButtonSize, ViewStyle> = {
  sm: { paddingVertical: 8, paddingHorizontal: 16 },
  md: { paddingVertical: 12, paddingHorizontal: 24 },
  lg: { paddingVertical: 16, paddingHorizontal: 32 },
};

const sizeTextStyles: Record<ButtonSize, TextStyle> = {
  sm: { fontSize: 13 },
  md: { fontSize: 15 },
  lg: { fontSize: 17 },
};
