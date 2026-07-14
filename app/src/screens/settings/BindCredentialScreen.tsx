// ============================================================
// 绑定教务凭证页面 (P4.5 遗留)
// ============================================================
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from 'react-native';
import { useForm, Controller } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import type { SettingsStackParamList } from '../../types/navigation';
import { credentialsApi } from '../../api/credentials';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';

// ============================================================
// 表单验证
// ============================================================
const bindSchema = z.object({
  student_no: z
    .string()
    .min(8, '学号至少 8 位')
    .max(20, '学号最多 20 位')
    .regex(/^\d+$/, '学号只能是数字'),
  password: z.string().min(1, '请输入教务密码'),
  doubao_api_key: z.string().optional(),
});

type BindFormData = z.infer<typeof bindSchema>;

type Nav = NativeStackNavigationProp<SettingsStackParamList, 'BindCredential'>;

export function BindCredentialScreen() {
  const navigation = useNavigation<Nav>();
  const [isLoading, setIsLoading] = useState(false);

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<BindFormData>({
    resolver: zodResolver(bindSchema),
    defaultValues: { student_no: '', password: '', doubao_api_key: '' },
  });

  const onSubmit = async (data: BindFormData) => {
    setIsLoading(true);
    try {
      await credentialsApi.bind({
        student_no: data.student_no,
        login_account: data.student_no,
        password: data.password,
        doubao_api_key: data.doubao_api_key || undefined,
      });
      Alert.alert('绑定成功', '教务凭证已安全加密保存，数据将自动同步', [
        { text: '好的', onPress: () => navigation.goBack() },
      ]);
    } catch (e: any) {
      const msg =
        e?.response?.data?.detail || e?.message || '绑定失败，请检查信息后重试';
      Alert.alert('绑定失败', msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.title}>绑定教务凭证</Text>
        <Text style={styles.subtitle}>
          你的密码使用 AES-256-GCM 加密存储，仅用于数据查询，不会用于任何写操作
        </Text>

        <View style={styles.form}>
          <Controller
            control={control}
            name="student_no"
            render={({ field: { onChange, onBlur, value } }) => (
              <Input
                label="学号"
                placeholder="请输入你的学号"
                keyboardType="number-pad"
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                error={errors.student_no?.message}
              />
            )}
          />

          <Controller
            control={control}
            name="password"
            render={({ field: { onChange, onBlur, value } }) => (
              <Input
                label="教务密码"
                placeholder="请输入教务系统密码"
                secureTextEntry
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                error={errors.password?.message}
              />
            )}
          />

          <Controller
            control={control}
            name="doubao_api_key"
            render={({ field: { onChange, onBlur, value } }) => (
              <Input
                label="豆包 API Key (可选)"
                placeholder="留空使用平台默认 Key"
                secureTextEntry
                value={value}
                onChangeText={onChange}
                onBlur={onBlur}
                error={errors.doubao_api_key?.message}
              />
            )}
          />

          <Button
            title={isLoading ? '绑定中...' : '确认绑定'}
            variant="primary"
            size="lg"
            loading={isLoading}
            disabled={isLoading}
            style={styles.submitBtn}
            onPress={handleSubmit(onSubmit)}
          />
        </View>

        <Text style={styles.note}>
          💡 提示：教务凭证仅用于查询课表、成绩、考试等数据，系统不会执行任何写操作（选课/退课/评教等）
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: '#FFFFFF' },
  container: { flex: 1 },
  content: { padding: 24, paddingTop: 16 },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 28,
  },
  form: { gap: 16 },
  submitBtn: { marginTop: 8, width: '100%' },
  note: {
    fontSize: 13,
    color: '#9CA3AF',
    lineHeight: 19,
    textAlign: 'center',
    marginTop: 28,
    paddingHorizontal: 16,
  },
});
