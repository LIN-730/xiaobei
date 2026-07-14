// ============================================================
// 成绩 API — GET /api/v1/scores/*
// ============================================================
import apiClient from './client';
import type { ScoreListResponse, TermsResponse, ScoreDetailItem } from '../types/score';

export const scoresApi = {
  /** 获取成绩 (可选按学期筛选) */
  getScores(term?: string): Promise<ScoreListResponse> {
    const params: Record<string, string> = {};
    if (term) params.term = term;
    return apiClient.get('/scores', { params }).then((r) => r.data);
  },

  /** 获取学期列表 */
  getTerms(): Promise<TermsResponse> {
    return apiClient.get('/scores/terms').then((r) => r.data);
  },

  /** 获取成绩明细 */
  getScoreDetail(courseName?: string): Promise<{ total: number; data: ScoreDetailItem[] }> {
    const params: Record<string, string> = {};
    if (courseName) params.course_name = courseName;
    return apiClient.get('/scores/detail', { params }).then((r) => r.data);
  },
};
