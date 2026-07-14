// ============================================================
// 课表类型
// ============================================================

/** 学期课程 — GET /courses */
export interface Course {
  course_name: string;
  course_code: string;
  teacher: string;
  classroom: string;
  week_day: number; // 1=周一 ~ 7=周日
  start_node: number; // 开始节次 (1-12)
  end_node: number; // 结束节次
  start_week: number;
  end_week: number;
  credit: number;
  course_type: string; // "必修" | "选修" | ...
}

export interface CourseListResponse {
  total: number;
  data: Course[];
}

/** 星期映射 */
export const WEEKDAY_NAMES: Record<number, string> = {
  1: '周一',
  2: '周二',
  3: '周三',
  4: '周四',
  5: '周五',
  6: '周六',
  7: '周日',
};

/**
 * 节次时间映射 (北京化工大学官方作息时间表)
 * 来源: https://gcsxy.buct.edu.cn/896/list.htm
 *
 * 上午 5节: 08:00-12:20
 * 下午 5节: 13:00-17:15
 * 晚上 3节: 18:00-20:25
 */
export const NODE_TIMES: Record<number, string> = {
  1: '08:00-08:45',
  2: '08:50-09:35',
  3: '09:50-10:35',
  4: '10:45-11:30',
  5: '11:35-12:20',
  6: '13:00-13:45',
  7: '13:50-14:35',
  8: '14:45-15:30',
  9: '15:40-16:25',
  10: '16:30-17:15',
  11: '18:00-18:45',
  12: '18:50-19:35',
  13: '19:40-20:25',
};

// ============================================================
// 课程卡片配色
// ============================================================

/** 课程卡片颜色 (bg + text + border) */
export interface CourseColor {
  bg: string;
  text: string;
  border: string;
}

/** 8 色调色板 — 课程卡片背景色 */
export const COURSE_COLORS: CourseColor[] = [
  { bg: '#E6F4FE', text: '#0664A7', border: '#0880D7' }, // 蓝
  { bg: '#FEF3C7', text: '#92400E', border: '#F59E0B' }, // 黄
  { bg: '#D1FAE5', text: '#065F46', border: '#10B981' }, // 绿
  { bg: '#EDE9FE', text: '#5B21B6', border: '#8B5CF6' }, // 紫
  { bg: '#FCE7F3', text: '#9D174D', border: '#EC4899' }, // 粉
  { bg: '#FFEDD5', text: '#9A3412', border: '#F97316' }, // 橙
  { bg: '#CCFBF1', text: '#134E4A', border: '#14B8A6' }, // 青
  { bg: '#E0F2FE', text: '#075985', border: '#0EA5E9' }, // 天蓝
];

/**
 * 根据课程名确定性分配颜色
 * 同一课程名始终获得相同颜色，确保跨周切换时颜色不变
 */
export function getCourseColor(courseName: string): CourseColor {
  let hash = 0;
  for (let i = 0; i < courseName.length; i++) {
    hash = courseName.charCodeAt(i) + ((hash << 5) - hash);
  }
  return COURSE_COLORS[Math.abs(hash) % COURSE_COLORS.length];
}
