// ============================================================
// 注册页面
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
const registerSchema = z
  .object({
    username: z
      .string()
      .min(3, '用户名至少 3 个字符')
      .max(50, '用户名最多 50 个字符')
      .regex(/^[a-zA-Z0-9_]+$/, '用户名只能包含字母、数字和下划线'),
    password: z
      .string()
      .min(6, '密码至少 6 个字符')
      .max(128, '密码最多 128 个字符'),
    confirmPassword: z.string(),
    email: z
      .string()
      .email('邮箱格式不正确')
      .max(255, '邮箱最多 255 个字符')
      .optional()
      .or(z.literal('')),
    phone: z
      .string()
      .max(20, '手机号最多 20 个字符')
      .regex(/^[0-9]*$/, '手机号只能包含数字')
      .optional()
      .or(z.literal('')),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: '两次输入的密码不一致',
    path: ['confirmPassword'],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

type Nav = NativeStackNavigationProp<AuthStackParamList, 'Register'>;

export function RegisterScreen() {
  const navigation = useNavigation<Nav>();
  const { register, isLoading, error, clearError } = useAuthStore();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: { username: '', password: '', confirmPassword: '', email: '', phone: '' },
  });

  const onSubmit = async (data: RegisterFormData) => {
    clearError();
    try {
      await register(
        data.username,
        data.password,
        data.email || undefined,
        data.phone || undefined,
      );
      // 注册成功后自动跳转到 MainTabs
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
        {/* 标题 */}
        <View style={styles.headerSection}>
          <Text style={styles.title}>创建账号</Text>
          <Text style={styles.subtitle}>注册后即可使用全部功能</Text>
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
                label="用户名 *"
                placeholder="3-50 个字符，字母数字下划线"
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
                label="密码 *"
                placeholder="6-128 个字符"
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                error={errors.password?.message}
                isPassword
                returnKeyType="next"
              />
            )}
          />

          <Controller
            control={control}
            name="confirmPassword"
            render={({ field: { onChange, onBlur, value } }) => (
              <Input
                label="确认密码 *"
                placeholder="再次输入密码"
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                error={errors.confirmPassword?.message}
                isPassword
                returnKeyType="next"
              />
            )}
          />

          <Controller
            control={control}
            name="email"
            render={({ field: { onChange, onBlur, value } }) => (
              <Input
                label="邮箱 (选填)"
                placeholder="example@mail.com"
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                error={errors.email?.message}
                keyboardType="email-address"
                autoCapitalize="none"
                returnKeyType="next"
              />
            )}
          />

          <Controller
            control={control}
            name="phone"
            render={({ field: { onChange, onBlur, value } }) => (
              <Input
                label="手机号 (选填)"
                placeholder="请输入手机号"
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                error={errors.phone?.message}
                keyboardType="phone-pad"
                returnKeyType="done"
                onSubmitEditing={handleSubmit(onSubmit)}
              />
            )}
          />

          <Button
            title="注册"
            onPress={handleSubmit(onSubmit)}
            loading={isLoading}
            size="lg"
            style={styles.registerButton}
          />

          {/* 返回登录 */}
          <View style={styles.loginRow}>
            <Text style={styles.loginText}>已有账号？</Text>
            <Button
              title="返回登录"
              variant="ghost"
              size="sm"
              onPress={() => navigation.goBack()}
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
    paddingHorizontal: 24,
    paddingTop: 60,
    paddingBottom: 40,
  },
  headerSection: {
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
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
  registerButton: {
    marginTop: 8,
    width: '100%',
  },
  loginRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 20,
  },
  loginText: {
    fontSize: 14,
    color: '#6B7280',
  },
});
