// ============================================================
// AI 对话 API — /api/v1/agent/* (会话管理，不含 SSE 流)
// ============================================================
import apiClient from './client';
import type {
  AgentSessionListResponse,
  AgentMessageListResponse,
  AgentDeleteResponse,
} from '../types/chat';

export const agentApi = {
  /** 获取会话列表 (分页) */
  getSessions(limit: number = 50, offset: number = 0): Promise<AgentSessionListResponse> {
    return apiClient.get('/agent/sessions', { params: { limit, offset } }).then((r) => r.data);
  },

  /** 获取会话消息历史 (游标分页) */
  getMessages(
    sessionKey: string,
    beforeId?: number,
    limit: number = 50,
  ): Promise<AgentMessageListResponse> {
    const params: Record<string, number> = { limit };
    if (beforeId !== undefined) params.before_id = beforeId;
    return apiClient
      .get(`/agent/sessions/${sessionKey}/messages`, { params })
      .then((r) => r.data);
  },

  /** 删除会话 */
  deleteSession(sessionKey: string): Promise<AgentDeleteResponse> {
    return apiClient.delete(`/agent/sessions/${sessionKey}`).then((r) => r.data);
  },
};
