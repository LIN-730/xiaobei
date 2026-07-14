// ============================================================
// 通知 API — GET /api/v1/notifications
// ============================================================
import apiClient from './client';

export interface NotificationItem {
  id: number;
  category: string;
  tag: string;
  title: string;
  content: string;
  date: string;
  link: string;
}

export interface NotificationListResponse {
  total: number;
  data: NotificationItem[];
}

export const notificationsApi = {
  /** 获取通知列表（可选按分类筛选） */
  getNotifications(category?: string, limit?: number): Promise<NotificationListResponse> {
    const params: Record<string, string | number> = {};
    if (category) params.category = category;
    if (limit) params.limit = limit;
    return apiClient.get('/notifications', { params }).then((r) => r.data);
  },
};
