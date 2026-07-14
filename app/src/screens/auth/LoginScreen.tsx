// ============================================================
// 登录页面
// ============================================================
import React from 'react';
import { View, Text, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { useForm, Controller } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { AuthStackParamList } from '../../types/navigation';
import { useAuthStore } from '../../stores/authStore';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';

// ============================================================
// 表单验证 Schema
// ============================================================
const loginSchema = z.object({
  username: z
    .string()
    .min(3, '用户名至少 3 个字符')
    .max(50, '用户名最多 50 个字符')
    .regex(/^[a-zA-Z0-9_]+$/, '用户名只能包含字母、数字和下划线'),
  password: z
    .string()
    .min(6, '密码至少 6 个字符')
    .max(128, '密码最多 128 个字符'),
});

type LoginFormData = z.infer<typeof loginSchema>;

type Nav = NativeStackNavigationProp<AuthStackParamList, 'Login'>;

export function LoginScreen() {
  const navigation = useNavigation<Nav>();
  const { login, isLoading, error, clearError } = useAuthStore();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' },
  });

  const onSubmit = async (data: LoginFormData) => {
    clearError();
    try {
      await login(data.username, data.password);
      // 登录成功后自动跳转到 MainTabs (由 RootNavigator 控制)
    } catch {
      // 错误已在 store 中设置
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
      >
        {/* Logo 区域 */}
        <View style={styles.logoSection}>
          <Text style={styles.logo}>🎓</Text>
          <Text style={styles.appName}>教务智能助手</Text>
          <Text style={styles.tagline}>小北 — 你的学业伙伴</Text>
        </View>

        {/* 表单 */}
        <View style={styles.formSection}>
          {error && (
            <View style={styles.errorBanner}>
              <Text style={styles.errorBannerText}>{error}</Text>
            </View>
          )}

          <Controller
            control={control}
            name="username"
            render={({ field: { onChange, onBlur, value } }) => (
              <Input
                label="用户名"
                placeholder="请输入用户名"
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                error={errors.username?.message}
                autoCapitalize="none"
                autoCorrect={false}
                returnKeyType="next"
              />
            )}
          />

          <Controller
            control={control}
            name="password"
            render={({ field: { onChange, onBlur, value } }) => (
              <Input
                label="密码"
                placeholder="请输入密码"
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                error={errors.password?.message}
                isPassword
                returnKeyType="done"
                onSubmitEditing={handleSubmit(onSubmit)}
              />
            )}
          />

          <Button
            title="登录"
            onPress={handleSubmit(onSubmit)}
            loading={isLoading}
            size="lg"
            style={styles.loginButton}
          />

          {/* 注册入口 */}
          <View style={styles.registerRow}>
            <Text style={styles.registerText}>还没有账号？</Text>
            <Button
              title="立即注册"
              variant="ghost"
              size="sm"
              onPress={() => navigation.navigate('Register')}
            />
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#FFFFFF' },
  container: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingBottom: 40,
  },
  logoSection: {
    alignItems: 'center',
    marginBottom: 40,
  },
  logo: {
    fontSize: 64,
    marginBottom: 12,
  },
  appName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  tagline: {
    fontSize: 14,
    color: '#6B7280',
  },
  formSection: {
    width: '100%',
  },
  errorBanner: {
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
  },
  errorBannerText: {
    color: '#DC2626',
    fontSize: 14,
    textAlign: 'center',
  },
  loginButton: {
    marginTop: 8,
    width: '100%',
  },
  registerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 20,
  },
  registerText: {
    fontSize: 14,
    color: '#6B7280',
  },
});
