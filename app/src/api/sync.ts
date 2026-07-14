// ============================================================
// 同步 API — POST+GET /api/v1/sync/*
// ============================================================
import apiClient from './client';
import type { SyncTriggerResponse, SyncStatusResponse } from '../types/api';

export const syncApi = {
  /** 触发全量同步 */
  trigger(): Promise<SyncTriggerResponse> {
    return apiClient.post('/sync/trigger').then((r) => r.data);
  },

  /** 查询同步状态 */
  getStatus(module?: string): Promise<SyncStatusResponse> {
    const params: Record<string, string> = {};
    if (module) params.module = module;
    return apiClient.get('/sync/status', { params }).then((r) => r.data);
  },
};
