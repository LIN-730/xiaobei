// ============================================================
// 课表 API — GET /api/v1/courses
// ============================================================
import apiClient from './client';
import type { Course, CourseListResponse } from '../types/course';

/** 冲突检测响应 */
export interface CourseConflict {
  course_a: Course;
  course_b: Course;
  weekday_name: string;
  overlap_nodes: string;
  overlap_weeks: string;
}

export interface ConflictResponse {
  total: number;
  has_conflicts: boolean;
  data: CourseConflict[];
}

export const coursesApi = {
  /** 获取课表 (可选按星期筛选) */
  getCourses(weekDay?: number): Promise<CourseListResponse> {
    const params: Record<string, number> = {};
    if (weekDay !== undefined) params.week_day = weekDay;
    return apiClient.get('/courses', { params }).then((r) => r.data);
  },

  /** 获取已选课程 */
  getSelectedCourses(): Promise<{ total: number; data: Course[] }> {
    return apiClient.get('/courses/selected').then((r) => r.data);
  },

  /** 导出 ICS 日历内容（带认证） */
  async exportIcsContent(): Promise<string> {
    const resp = await apiClient.get('/courses/export/ics', {
      responseType: 'text',
      headers: { Accept: 'text/calendar' },
    });
    return resp.data;
  },

  /** 检测课程冲突 */
  getConflicts(): Promise<ConflictResponse> {
    return apiClient.get('/courses/conflicts').then((r) => r.data);
  },
};
