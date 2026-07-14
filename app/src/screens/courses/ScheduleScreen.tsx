// ============================================================
// 课表周视图 — 6列(时间轴+周一~周五) × 13行(节次1-13)
// 支持水平滑动切换周次 + 课程重叠检测 + 课程卡片点击进入详情
// ============================================================
import React, { useMemo, useState, useLayoutEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Dimensions,
  Alert,
  Share,
} from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { coursesApi } from '../../api/courses';
import { getCourseColor, type Course, type CourseColor } from '../../types/course';
import type { ScheduleStackParamList } from '../../types/navigation';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';

// ============================================================
// 布局常量 (13节，北化官方作息)
// ============================================================

const TIME_COLUMN_WIDTH = 48;
const DAY_HEADER_HEIGHT = 44;
const ROW_HEIGHT = 60;
const COLUMN_GAP = 1;
const MAX_NODES = 13; // 北化 13 节课

const SCREEN_WIDTH = Dimensions.get('window').width;
const DAY_COLUMN_WIDTH =
  (SCREEN_WIDTH - TIME_COLUMN_WIDTH - COLUMN_GAP * 6) / 5;
const GRID_HEIGHT = DAY_HEADER_HEIGHT + ROW_HEIGHT * MAX_NODES;

const WEEKDAYS = ['周一', '周二', '周三', '周四', '周五'];

// ============================================================
// 类型
// ============================================================

interface PlacedCourse extends Course {
  lane: number;
  totalLanes: number;
  color: CourseColor;
}

type ScheduleNav = NativeStackNavigationProp<ScheduleStackParamList, 'Schedule'>;

// ============================================================
// ScheduleScreen 组件
// ============================================================

export function ScheduleScreen() {
  const navigation = useNavigation<ScheduleNav>();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['courses'],
    queryFn: () => coursesApi.getCourses(),
  });

  // ICS 日历导出（带认证 fetch + Share API）
  const handleExportIcs = useCallback(async () => {
    try {
      const icsContent = await coursesApi.exportIcsContent();
      await Share.share({
        message: icsContent,
        title: '北化课表.ics',
      });
    } catch (err: any) {
      if (err?.message !== 'User did not share') {
        Alert.alert('导出失败', err?.message || '请检查网络后重试');
      }
    }
  }, []);

  useLayoutEffect(() => {
    navigation.setOptions({
      headerRight: () => (
        <TouchableOpacity
          onPress={handleExportIcs}
          activeOpacity={0.7}
          style={{
            paddingHorizontal: 10,
            paddingVertical: 5,
            backgroundColor: '#D97706',
            borderRadius: 8,
            marginRight: 4,
          }}
        >
          <Text style={{ color: '#FFFFFF', fontSize: 13, fontWeight: '600' }}>
            导出日历
          </Text>
        </TouchableOpacity>
      ),
    });
  }, [navigation, handleExportIcs]);

  // 计算有效周范围
  const { minWeek, maxWeek } = useMemo(() => {
    const courses = data?.data;
    if (!courses?.length) return { minWeek: 1, maxWeek: 20 };
    const weeks = courses.flatMap((c) => [c.start_week, c.end_week]);
    return { minWeek: Math.min(...weeks), maxWeek: Math.max(...weeks) };
  }, [data]);

  const [currentWeek, setCurrentWeek] = useState(minWeek);

  // 筛选本周 + 周一至周五的课程
  const weekCourses = useMemo(() => {
    if (!data?.data) return [];
    return data.data.filter(
      (c) =>
        c.start_week <= currentWeek &&
        c.end_week >= currentWeek &&
        c.week_day >= 1 &&
        c.week_day <= 5,
    );
  }, [data, currentWeek]);

  // 重叠检测 + 车道分配
  const placedCourses = useMemo(
    () => layoutCourses(weekCourses),
    [weekCourses],
  );

  // 水平手势 — 滑动切换周
  const panGesture = Gesture.Pan()
    .activeOffsetX([-30, 30])
    .onEnd((e) => {
      if (e.translationX < -50) {
        setCurrentWeek((prev) => Math.min(prev + 1, maxWeek));
      } else if (e.translationX > 50) {
        setCurrentWeek((prev) => Math.max(prev - 1, minWeek));
      }
    });

  const canGoPrev = currentWeek > minWeek;
  const canGoNext = currentWeek < maxWeek;

  // 加载
  if (isLoading) {
    return <LoadingSpinner fullScreen />;
  }

  // 错误
  if (isError || !data) {
    return (
      <EmptyState
        icon="⚠️"
        title="数据加载失败"
        description="请检查网络连接后重试"
        actionLabel="重试"
        onAction={() => refetch()}
      />
    );
  }

  return (
    <View style={styles.container}>
      {/* 周次选择器 */}
      <View style={styles.weekSelector}>
        <TouchableOpacity
          onPress={() => setCurrentWeek((p) => Math.max(p - 1, minWeek))}
          disabled={!canGoPrev}
          style={[styles.weekArrow, !canGoPrev && styles.weekArrowDisabled]}
          activeOpacity={0.6}
        >
          <Text
            style={[
              styles.weekArrowText,
              !canGoPrev && styles.weekArrowTextDisabled,
            ]}
          >
            ‹
          </Text>
        </TouchableOpacity>
        <View style={styles.weekCenter}>
          <Text style={styles.weekLabel}>第 {currentWeek} 周</Text>
          <Text style={styles.weekSummary}>
            共 {weekCourses.length} 门课
          </Text>
        </View>
        <TouchableOpacity
          onPress={() => setCurrentWeek((p) => Math.min(p + 1, maxWeek))}
          disabled={!canGoNext}
          style={[styles.weekArrow, !canGoNext && styles.weekArrowDisabled]}
          activeOpacity={0.6}
        >
          <Text
            style={[
              styles.weekArrowText,
              !canGoNext && styles.weekArrowTextDisabled,
            ]}
          >
            ›
          </Text>
        </TouchableOpacity>
      </View>

      {/* 课表网格 */}
      <GestureDetector gesture={panGesture}>
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.grid}>
            {/* 表头 — 星期 */}
            <View style={styles.gridHeader}>
              <View style={styles.timeColumnHeader} />
              {WEEKDAYS.map((day) => (
                <View key={day} style={styles.dayHeader}>
                  <Text style={styles.dayHeaderText}>{day}</Text>
                </View>
              ))}
            </View>

            {/* 表体 */}
            <View style={[styles.gridBody, { height: GRID_HEIGHT - DAY_HEADER_HEIGHT }]}>
              {/* 时间轴 + 行网格线 */}
              {Array.from({ length: MAX_NODES }, (_, i) => (
                <View
                  key={i}
                  style={[
                    styles.timeRow,
                    { top: i * ROW_HEIGHT, height: ROW_HEIGHT },
                  ]}
                >
                  <View style={styles.timeLabel}>
                    <Text style={styles.timeLabelText}>{i + 1}</Text>
                  </View>
                  {/* 列分割线 */}
                  {WEEKDAYS.map((_, di) => (
                    <View
                      key={di}
                      style={[
                        styles.gridLine,
                        {
                          left:
                            TIME_COLUMN_WIDTH +
                            di * (DAY_COLUMN_WIDTH + COLUMN_GAP) +
                            DAY_COLUMN_WIDTH,
                        },
                      ]}
                    />
                  ))}
                  {/* 行分割线 */}
                  <View style={styles.rowLine} />
                </View>
              ))}

              {/* 课程卡片 */}
              {placedCourses.map((course, idx) => {
                const cardStyle = getCardStyle(course);
                return (
                  <TouchableOpacity
                    key={`${course.course_code}-${course.start_node}-${idx}`}
                    style={[styles.courseCard, cardStyle]}
                    activeOpacity={0.7}
                    onPress={() =>
                      navigation.navigate('CourseDetail', { course })
                    }
                  >
                    <Text
                      style={[
                        styles.courseCardName,
                        { color: course.color.text },
                      ]}
                      numberOfLines={2}
                    >
                      {course.course_name}
                    </Text>
                    {cardStyle.height > 80 && (
                      <Text style={styles.courseCardRoom} numberOfLines={1}>
                        {course.classroom || ''}
                      </Text>
                    )}
                  </TouchableOpacity>
                );
              })}

              {/* 本周无课提示 */}
              {weekCourses.length === 0 && (
                <View style={styles.emptyOverlay}>
                  <Text style={styles.emptyText}>📅 本周无课</Text>
                </View>
              )}
            </View>
          </View>

          {/* 图例 */}
          {weekCourses.length > 0 && (
            <Text style={styles.legend}>
              周次范围: 第 {minWeek}-{maxWeek} 周 · 左滑查看下一周
            </Text>
          )}
        </ScrollView>
      </GestureDetector>
    </View>
  );
}

// ============================================================
// 重叠检测 + 车道分配算法
// ============================================================

function layoutCourses(courses: Course[]): PlacedCourse[] {
  const byDay = new Map<number, Course[]>();
  for (const c of courses) {
    if (!byDay.has(c.week_day)) byDay.set(c.week_day, []);
    byDay.get(c.week_day)!.push(c);
  }

  const result: PlacedCourse[] = [];
  for (const [day, dayCourses] of byDay) {
    dayCourses.sort((a, b) => a.start_node - b.start_node);
    const lanes: number[] = []; // 每条车道最后一个课程的 end_node

    for (const course of dayCourses) {
      let assigned = -1;
      for (let i = 0; i < lanes.length; i++) {
        if (lanes[i] < course.start_node) {
          assigned = i;
          break;
        }
      }
      if (assigned === -1) assigned = lanes.length;
      lanes[assigned] = course.end_node;

      result.push({
        ...course,
        lane: assigned,
        totalLanes: 0,
        color: getCourseColor(course.course_name),
      });
    }

    // 回填当天 totalLanes
    const tl = lanes.length;
    for (const pc of result) {
      if (pc.week_day === day) pc.totalLanes = tl;
    }
  }

  return result;
}

// ============================================================
// 课程卡片定位计算
// ============================================================

function getCardStyle(course: PlacedCourse) {
  const laneWidth = DAY_COLUMN_WIDTH / course.totalLanes;
  const nodeCount = course.end_node - course.start_node + 1;

  return {
    position: 'absolute' as const,
    left:
      TIME_COLUMN_WIDTH +
      (course.week_day - 1) * (DAY_COLUMN_WIDTH + COLUMN_GAP) +
      course.lane * laneWidth +
      2,
    top: (course.start_node - 1) * ROW_HEIGHT + 2,
    width: laneWidth - 4,
    height: nodeCount * ROW_HEIGHT - 4,
  };
}

// ============================================================
// Styles
// ============================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },

  // 周次选择器
  weekSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E7EB',
  },
  weekArrow: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  weekArrowDisabled: {
    opacity: 0.3,
  },
  weekArrowText: {
    fontSize: 22,
    color: '#374151',
    lineHeight: 24,
  },
  weekArrowTextDisabled: {
    color: '#D1D5DB',
  },
  weekCenter: {
    alignItems: 'center',
  },
  weekLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  weekSummary: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 2,
  },

  // 滚动区域
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 24,
  },

  // 网格
  grid: {
    backgroundColor: '#FFFFFF',
  },
  gridHeader: {
    flexDirection: 'row',
    height: DAY_HEADER_HEIGHT,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E7EB',
    backgroundColor: '#FAFAFA',
  },
  timeColumnHeader: {
    width: TIME_COLUMN_WIDTH,
  },
  dayHeader: {
    width: DAY_COLUMN_WIDTH,
    marginLeft: COLUMN_GAP,
    alignItems: 'center',
    justifyContent: 'center',
    borderLeftWidth: StyleSheet.hairlineWidth,
    borderLeftColor: '#E5E7EB',
  },
  dayHeaderText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#374151',
  },

  // 表体
  gridBody: {
    position: 'relative',
    width: SCREEN_WIDTH,
  },
  timeRow: {
    position: 'absolute',
    left: 0,
    right: 0,
    flexDirection: 'row',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#F3F4F6',
  },
  timeLabel: {
    width: TIME_COLUMN_WIDTH,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FAFAFA',
  },
  timeLabelText: {
    fontSize: 11,
    color: '#9CA3AF',
    fontWeight: '500',
  },
  gridLine: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    width: StyleSheet.hairlineWidth,
    backgroundColor: '#E5E7EB',
  },
  rowLine: {
    display: 'none', // 行线由 timeRow 的 borderBottom 提供
  },

  // 课程卡片
  courseCard: {
    borderRadius: 6,
    borderLeftWidth: 3,
    padding: 4,
    overflow: 'hidden',
  },
  courseCardName: {
    fontSize: 10,
    fontWeight: '600',
    lineHeight: 13,
    marginBottom: 2,
  },
  courseCardRoom: {
    fontSize: 9,
    color: '#9CA3AF',
    lineHeight: 11,
  },

  // 空状态
  emptyOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyText: {
    fontSize: 14,
    color: '#D1D5DB',
  },

  // 图例
  legend: {
    textAlign: 'center',
    fontSize: 12,
    color: '#D1D5DB',
    marginTop: 12,
  },
});
