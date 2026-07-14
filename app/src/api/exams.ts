// ============================================================
// 考试 API — GET /api/v1/exams
// ============================================================
import apiClient from './client';
import type { ExamListResponse } from '../types/exam';

export const examsApi = {
  /** 获取考试安排 */
  getExams(limit: number = 20): Promise<ExamListResponse> {
    return apiClient.get('/exams', { params: { limit } }).then((r) => r.data);
  },
};
