// ============================================================
// 学业规划 API — GET /api/v1/planning/*
// ============================================================
import apiClient from './client';

export const planningApi = {
  /** 学分缺口分析 */
  getCreditGap() {
    return apiClient.get('/planning/credit-gap').then((r) => r.data);
  },

  /** 必修课完成情况 */
  getRequiredCourses() {
    return apiClient.get('/planning/required-courses').then((r) => r.data);
  },

  /** 选课推荐 */
  getRecommend(semester?: string, limit: number = 10) {
    const params: Record<string, string | number> = { limit };
    if (semester) params.semester = semester;
    return apiClient.get('/planning/recommend', { params }).then((r) => r.data);
  },

  /** 学业路径规划 */
  getPath(creditsPerSemester: number = 25) {
    return apiClient
      .get('/planning/path', { params: { credits_per_semester: creditsPerSemester } })
      .then((r) => r.data);
  },
};
