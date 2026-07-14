// ============================================================
// 仪表盘 API — GET /api/v1/dashboard
// ============================================================
import apiClient from './client';
import type { DashboardResponse } from '../types/api';

export const dashboardApi = {
  /** 获取仪表盘聚合数据 */
  getDashboard(): Promise<DashboardResponse> {
    return apiClient.get('/dashboard').then((r) => r.data);
  },
};
