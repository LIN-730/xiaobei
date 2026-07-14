// ============================================================
// 教务凭证 API — /api/v1/credentials/*
// ============================================================
import apiClient from './client';
import type {
  BindCredentialRequest,
  CredentialStatusResponse,
  MessageResponse,
} from '../types/api';

export const credentialsApi = {
  /** 绑定教务凭证 */
  bind(data: BindCredentialRequest): Promise<MessageResponse> {
    return apiClient.post('/credentials/bind', data).then((r) => r.data);
  },

  /** 查询凭证状态 */
  getStatus(): Promise<CredentialStatusResponse> {
    return apiClient.get('/credentials/status').then((r) => r.data);
  },

  /** 解绑凭证 */
  unbind(): Promise<MessageResponse> {
    return apiClient.delete('/credentials/unbind').then((r) => r.data);
  },
};
