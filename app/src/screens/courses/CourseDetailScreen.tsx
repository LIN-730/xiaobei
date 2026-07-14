// ============================================================
// 课程详情页
// 从课表周视图点击课程卡片进入
// ============================================================
import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { ScheduleStackParamList } from '../../types/navigation';
import { WEEKDAY_NAMES, NODE_TIMES, getCourseColor } from '../../types/course';
import { Card } from '../../components/ui/Card';

type Props = NativeStackScreenProps<ScheduleStackParamList, 'CourseDetail'>;

export function CourseDetailScreen({ route }: Props) {
  const { course } = route.params;
  const color = getCourseColor(course.course_name);

  // 构造上课时间描述
  const weekday = WEEKDAY_NAMES[course.week_day] || `周${course.week_day}`;
  const startTime = NODE_TIMES[course.start_node]?.split('-')[0] || '';
  const endTime = NODE_TIMES[course.end_node]?.split('-')[1] || '';
  const timeDesc = `${weekday} 第${course.start_node}-${course.end_node}节`;
  const timeRange = startTime && endTime ? `${startTime}-${endTime}` : '';
  const weekDesc = `第${course.start_week}-${course.end_week}周`;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* 课程名卡片 (带颜色标识) */}
      <Card style={styles.headerCard}>
        <View style={styles.headerRow}>
          <View style={[styles.colorBar, { backgroundColor: color.border }]} />
          <View style={styles.headerText}>
            <Text style={styles.courseName}>{course.course_name}</Text>
            <Text style={styles.courseCode}>{course.course_code}</Text>
          </View>
        </View>
      </Card>

      {/* 详细信息 */}
      <Card style={styles.detailCard}>
        <InfoRow label="授课教师" value={course.teacher || '暂无'} />
        <InfoRow label="上课教室" value={course.classroom || '暂无'} />
        <InfoRow
          label="上课时间"
          value={timeRange ? `${timeDesc} (${timeRange})` : timeDesc}
        />
        <InfoRow label="上课周次" value={weekDesc} />
      </Card>

      <Card style={styles.detailCard}>
        <InfoRow label="学分" value={`${course.credit.toFixed(1)} 分`} />
        <InfoRow label="课程类型" value={course.course_type || '未知'} />
      </Card>
    </ScrollView>
  );
}

// ============================================================
// 信息行子组件
// ============================================================

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  headerCard: {
    marginBottom: 16,
    padding: 0,
    overflow: 'hidden',
  },
  headerRow: {
    flexDirection: 'row',
  },
  colorBar: {
    width: 4,
    alignSelf: 'stretch',
  },
  headerText: {
    flex: 1,
    padding: 16,
  },
  courseName: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 6,
  },
  courseCode: {
    fontSize: 13,
    color: '#6B7280',
  },
  detailCard: {
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#F3F4F6',
  },
  infoLabel: {
    fontSize: 15,
    color: '#6B7280',
  },
  infoValue: {
    fontSize: 15,
    fontWeight: '500',
    color: '#111827',
    textAlign: 'right',
    flex: 1,
    marginLeft: 16,
  },
});
