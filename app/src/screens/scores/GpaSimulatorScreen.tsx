// ============================================================
// GPA 模拟器 — 输入预估课程，实时计算模拟 GPA
// ============================================================
import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  Alert,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { AcademicStackParamList } from '../../types/navigation';
import { gpaApi } from '../../api/gpa';
import type {
  GpaSimulateCourseInput,
  GpaSimulateResponse,
  GpTableRow,
} from '../../types/gpa';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';

type Props = NativeStackScreenProps<AcademicStackParamList, 'GpaSimulator'>;

// ============================================================
// 绩点对照表（本地静态，避免重复请求）
// ============================================================

const GP_TABLE: GpTableRow[] = [
  { grade: 'A+', grade_point: 4.33, score_range: '95-100' },
  { grade: 'A', grade_point: 4.0, score_range: '90-94' },
  { grade: 'A-', grade_point: 3.7, score_range: '85-89' },
  { grade: 'B+', grade_point: 3.3, score_range: '82-84' },
  { grade: 'B', grade_point: 3.0, score_range: '78-81' },
  { grade: 'B-', grade_point: 2.7, score_range: '75-77' },
  { grade: 'C+', grade_point: 2.3, score_range: '72-74' },
  { grade: 'C', grade_point: 2.0, score_range: '68-71' },
  { grade: 'C-', grade_point: 1.5, score_range: '64-67' },
  { grade: 'D', grade_point: 1.0, score_range: '60-63' },
  { grade: 'F', grade_point: 0.0, score_range: '0-59' },
];

// ============================================================
// 空课程模板
// ============================================================

function emptyCourse(): GpaSimulateCourseInput {
  return { name: '', credit: 3.0, score: 85 };
}

// ============================================================
// 主组件
// ============================================================

export function GpaSimulatorScreen({ navigation }: Props) {
  const [courses, setCourses] = useState<GpaSimulateCourseInput[]>([
    emptyCourse(),
  ]);
  const [result, setResult] = useState<GpaSimulateResponse | null>(null);
  const [loading, setLoading] = useState(false);

  // 添加课程行
  const addCourse = useCallback(() => {
    if (courses.length >= 10) {
      Alert.alert('提示', '最多同时模拟 10 门课程');
      return;
    }
    setCourses((prev) => [...prev, emptyCourse()]);
  }, [courses.length]);

  // 删除课程行
  const removeCourse = useCallback((index: number) => {
    setCourses((prev) => {
      if (prev.length <= 1) return prev;
      return prev.filter((_, i) => i !== index);
    });
  }, []);

  // 更新课程行
  const updateCourse = useCallback(
    (index: number, field: keyof GpaSimulateCourseInput, value: string) => {
      setCourses((prev) =>
        prev.map((c, i) => {
          if (i !== index) return c;
          if (field === 'name') return { ...c, name: value };
          return { ...c, [field]: parseFloat(value) || 0 };
        }),
      );
    },
    [],
  );

  // 提交模拟
  const simulate = useCallback(async () => {
    const valid = courses.filter((c) => c.name.trim() && c.credit > 0);
    if (valid.length === 0) {
      Alert.alert('提示', '请至少填写一门课程的名称和学分');
      return;
    }
    setLoading(true);
    try {
      const res = await gpaApi.simulate({ courses: valid });
      setResult(res);
    } catch (err: any) {
      Alert.alert('模拟失败', err?.message || '网络错误');
    } finally {
      setLoading(false);
    }
  }, [courses]);

  // 重置
  const reset = useCallback(() => {
    setCourses([emptyCourse()]);
    setResult(null);
  }, []);

  // ============================================================
  // Render
  // ============================================================

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
    >
      {/* ── 标题 ── */}
      <Text style={styles.subtitle}>
        输入预估课程，查看模拟后的 GPA 变化
      </Text>

      {/* ── 课程列表 ── */}
      {courses.map((course, index) => (
        <View key={index} style={[styles.courseCard, styles.cardShadow]}>
          {/* 课程名 */}
          <View style={styles.row}>
            <Text style={styles.label}>课程名</Text>
            <TextInput
              style={styles.input}
              placeholder="如: 高等数学"
              placeholderTextColor="#D1D5DB"
              value={course.name}
              onChangeText={(v) => updateCourse(index, 'name', v)}
            />
          </View>

          {/* 学分 + 分数 */}
          <View style={styles.row}>
            <View style={styles.half}>
              <Text style={styles.label}>学分</Text>
              <TextInput
                style={styles.input}
                placeholder="3.0"
                placeholderTextColor="#D1D5DB"
                keyboardType="decimal-pad"
                value={course.credit > 0 ? String(course.credit) : ''}
                onChangeText={(v) => updateCourse(index, 'credit', v)}
              />
            </View>
            <View style={styles.half}>
              <Text style={styles.label}>预估分数</Text>
              <TextInput
                style={styles.input}
                placeholder="85"
                placeholderTextColor="#D1D5DB"
                keyboardType="number-pad"
                value={course.score > 0 ? String(course.score) : ''}
                onChangeText={(v) => updateCourse(index, 'score', v)}
              />
            </View>
          </View>

          {/* 删除按钮 */}
          {courses.length > 1 && (
            <TouchableOpacity
              style={styles.removeBtn}
              onPress={() => removeCourse(index)}
              activeOpacity={0.6}
            >
              <Text style={styles.removeBtnText}>移除</Text>
            </TouchableOpacity>
          )}
        </View>
      ))}

      {/* ── 操作按钮 ── */}
      <View style={styles.actions}>
        <TouchableOpacity
          style={styles.addBtn}
          onPress={addCourse}
          activeOpacity={0.7}
        >
          <Text style={styles.addBtnText}>+ 添加课程</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.simBtn}
          onPress={simulate}
          activeOpacity={0.7}
          disabled={loading}
        >
          {loading ? (
            <LoadingSpinner size="small" />
          ) : (
            <Text style={styles.simBtnText}>开始模拟</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.resetBtn}
          onPress={reset}
          activeOpacity={0.7}
        >
          <Text style={styles.resetBtnText}>重置</Text>
        </TouchableOpacity>
      </View>

      {/* ── 模拟结果 ── */}
      {result && (
        <View style={[styles.resultCard, styles.cardShadow]}>
          <Text style={styles.resultTitle}>📊 模拟结果</Text>

          {/* 当前 vs 模拟后 */}
          <View style={styles.gpaRow}>
            <View style={styles.gpaItem}>
              <Text style={styles.gpaLabel}>当前 GPA</Text>
              <Text style={styles.gpaValue}>{result.current_gpa.toFixed(2)}</Text>
              <Text style={styles.gpaSub}>
                {result.current_credits.toFixed(1)} 学分
              </Text>
            </View>

            <View style={styles.gpaArrow}>
              <Text style={styles.arrowText}>→</Text>
            </View>

            <View style={styles.gpaItem}>
              <Text style={styles.gpaLabel}>模拟后 GPA</Text>
              <Text
                style={[
                  styles.gpaValue,
                  result.gpa_change > 0
                    ? styles.gpaUp
                    : result.gpa_change < 0
                      ? styles.gpaDown
                      : styles.gpaSame,
                ]}
              >
                {result.simulated_gpa.toFixed(2)}
              </Text>
              <Text style={styles.gpaSub}>
                {result.new_total_credits.toFixed(1)} 学分
              </Text>
            </View>
          </View>

          {/* 变化值 */}
          <View style={styles.changeWrap}>
            <Text
              style={[
                styles.changeText,
                result.gpa_change > 0
                  ? styles.changeUp
                  : result.gpa_change < 0
                    ? styles.changeDown
                    : styles.changeSame,
              ]}
            >
              {result.gpa_change >= 0 ? '+' : ''}
              {result.gpa_change.toFixed(2)} GPA
            </Text>
          </View>

          {/* 逐课程明细 */}
          <Text style={styles.detailTitle}>课程明细</Text>
          {result.courses.map((c, i) => (
            <View key={i} style={styles.detailRow}>
              <Text style={styles.detailName}>{c.name}</Text>
              <Text style={styles.detailScore}>
                {c.score}分 → 绩点{c.grade_point} × {c.credit}学分
              </Text>
              <Text style={styles.detailContrib}>
                +{c.gp_contribution}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* ── 绩点对照表 ── */}
      <View style={[styles.tableCard, styles.cardShadow]}>
        <Text style={styles.resultTitle}>📋 绩点对照表（北化标准）</Text>
        {GP_TABLE.map((row) => (
          <View key={row.grade} style={styles.tableRow}>
            <View style={styles.tableGrade}>
              <Text style={styles.tableGradeText}>{row.grade}</Text>
            </View>
            <Text style={styles.tableGp}>{row.grade_point.toFixed(2)}</Text>
            <Text style={styles.tableRange}>{row.score_range} 分</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  subtitle: {
    fontSize: 14,
    color: '#9CA3AF',
    marginBottom: 16,
  },

  // ── 课程卡片 ──
  courseCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
  },
  cardShadow: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6B7280',
    width: 64,
    marginRight: 8,
  },
  input: {
    flex: 1,
    fontSize: 15,
    color: '#111827',
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  half: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 8,
  },
  removeBtn: {
    alignSelf: 'flex-end',
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
  removeBtnText: {
    fontSize: 13,
    color: '#EF4444',
    fontWeight: '500',
  },

  // ── 操作按钮 ──
  actions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 6,
    marginBottom: 16,
  },
  addBtn: {
    flex: 1,
    minWidth: 100,
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
  },
  addBtnText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#374151',
  },
  simBtn: {
    flex: 1,
    minWidth: 100,
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: '#0880D7',
    alignItems: 'center',
  },
  simBtnText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  resetBtn: {
    flex: 1,
    minWidth: 80,
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: '#FEE2E2',
    alignItems: 'center',
  },
  resetBtnText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#DC2626',
  },

  // ── 模拟结果 ──
  resultCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 18,
    marginBottom: 16,
  },
  resultTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 14,
  },
  gpaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  gpaItem: {
    flex: 1,
    alignItems: 'center',
  },
  gpaLabel: {
    fontSize: 12,
    color: '#9CA3AF',
    marginBottom: 4,
  },
  gpaValue: {
    fontSize: 28,
    fontWeight: '700',
    color: '#111827',
  },
  gpaSub: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 2,
  },
  gpaArrow: {
    paddingHorizontal: 8,
  },
  arrowText: {
    fontSize: 22,
    color: '#D1D5DB',
  },
  gpaUp: { color: '#059669' },
  gpaDown: { color: '#DC2626' },
  gpaSame: { color: '#6B7280' },
  changeWrap: {
    alignItems: 'center',
    paddingVertical: 8,
    marginBottom: 10,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
  },
  changeText: {
    fontSize: 17,
    fontWeight: '700',
  },
  changeUp: { color: '#059669' },
  changeDown: { color: '#DC2626' },
  changeSame: { color: '#6B7280' },

  // ── 逐课程明细 ──
  detailTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  detailName: {
    flex: 2,
    fontSize: 14,
    fontWeight: '500',
    color: '#111827',
  },
  detailScore: {
    flex: 3,
    fontSize: 12,
    color: '#6B7280',
  },
  detailContrib: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: '#0880D7',
    textAlign: 'right',
  },

  // ── 绩点对照表 ──
  tableCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 18,
  },
  tableRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  tableGrade: {
    width: 40,
    height: 28,
    borderRadius: 6,
    backgroundColor: '#EEF2FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  tableGradeText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#4F46E5',
  },
  tableGp: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    width: 50,
  },
  tableRange: {
    fontSize: 13,
    color: '#6B7280',
    flex: 1,
    textAlign: 'right',
  },
});
