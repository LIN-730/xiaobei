// ============================================================
// 空闲教室 API — GET /api/v1/classrooms
// ============================================================
import apiClient from './client';

export interface ClassroomItem {
  campus: string;
  building: string;
  room_no: string;
  capacity: number;
  week_day: number;
  start_node: number;
  end_node: number;
  status: string;
}

export interface ClassroomListResponse {
  total: number;
  data: ClassroomItem[];
}

export const classroomsApi = {
  /** 查询空闲教室 */
  getClassrooms(weekDay?: number, building?: string): Promise<ClassroomListResponse> {
    const params: Record<string, string | number> = {};
    if (weekDay !== undefined) params.week_day = weekDay;
    if (building) params.building = building;
    return apiClient.get('/classrooms', { params }).then((r) => r.data);
  },
};
