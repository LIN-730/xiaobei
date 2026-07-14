// ============================================================
// 设置页面
// ============================================================
import React from 'react';
import { View, Text, ScrollView, StyleSheet, Alert } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useAuthStore } from '../../stores/authStore';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import type { SettingsStackParamList } from '../../types/navigation';

type Nav = NativeStackNavigationProp<SettingsStackParamList, 'Settings'>;

export function SettingsScreen() {
  const navigation = useNavigation<Nav>();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    Alert.alert('确认登出', '登出后需要重新登录', [
      { text: '取消', style: 'cancel' },
      { text: '登出', style: 'destructive', onPress: () => logout() },
    ]);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* 用户信息 */}
      <Card style={styles.section}>
        <Text style={styles.sectionTitle}>账号信息</Text>
        <InfoRow label="用户名" value={user?.username || '-'} />
        <InfoRow label="邮箱" value={user?.email || '未设置'} />
        <InfoRow label="手机号" value={user?.phone || '未设置'} />
        <InfoRow
          label="教务凭证"
          value={user?.has_credential ? '已绑定 ✅' : '未绑定 ⚠️'}
        />
      </Card>

      {/* 凭证管理 */}
      <Card style={styles.section}>
        <Text style={styles.sectionTitle}>教务凭证</Text>
        <Text style={styles.hintText}>
          {user?.has_credential
            ? '你的教务凭证已安全绑定，数据自动同步'
            : '绑定教务凭证以获取课表、成绩、考试等数据'}
        </Text>
        <Button
          title={user?.has_credential ? '重新绑定' : '绑定教务凭证'}
          variant={user?.has_credential ? 'outline' : 'primary'}
          size="md"
          style={styles.actionBtn}
          onPress={() => navigation.navigate('BindCredential')}
        />
      </Card>

      {/* 登出 */}
      <Card style={styles.section}>
        <Button
          title="退出登录"
          variant="danger"
          size="md"
          onPress={handleLogout}
        />
      </Card>

      <Text style={styles.version}>v1.0.0</Text>
    </ScrollView>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  hintText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 12,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 0.5,
    borderBottomColor: '#F3F4F6',
  },
  infoLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  infoValue: {
    fontSize: 14,
    color: '#111827',
    fontWeight: '500',
  },
  actionBtn: {
    width: '100%',
  },
  version: {
    textAlign: 'center',
    fontSize: 12,
    color: '#D1D5DB',
    marginTop: 8,
  },
});
