// ============================================================
// GPA 模拟器 API — POST /api/v1/scores/gpa-simulate
// ============================================================
import apiClient from './client';
import type { GpaSimulateRequest, GpaSimulateResponse } from '../types/gpa';

export const gpaApi = {
  /** GPA 模拟计算 */
  simulate(body: GpaSimulateRequest): Promise<GpaSimulateResponse> {
    return apiClient.post('/scores/gpa-simulate', body).then((r) => r.data);
  },
};
