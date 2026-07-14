// ============================================================
// 通用 API 类型
// ============================================================

/** 通用消息响应 */
export interface MessageResponse {
  message: string;
}

/** 健康检查响应 */
export interface HealthResponse {
  status: string;
  app: string;
}

// ============================================================
// 教务凭证 — 对应 app/auth/schemas.py
// ============================================================

/** POST /credentials/bind 请求 */
export interface BindCredentialRequest {
  student_no: string;
  login_account: string;
  password: string;
  base_url?: string;
  doubao_api_key?: string;
}

/** GET /credentials/status 响应 */
export interface CredentialStatusResponse {
  is_bound: boolean;
  student_no?: string;
  is_valid?: boolean;
  last_sync_at?: string; // ISO 8601
}

// ============================================================
// 仪表盘
// ============================================================

export interface StudentInfo {
  name: string;
  college: string;
  major: string;
  grade: string;
}

export interface DashboardKpi {
  course_count: number;
  exam_count: number;
  total_credits: number;
  avg_gpa: number;
  warning_count: number;
}

export interface AcademicStatus {
  total_credits: number;
  earned_credits: number;
  average_gpa: number;
  required_done: number;
  required_total: number;
}

export interface DashboardResponse {
  student: StudentInfo;
  kpi: DashboardKpi;
  academic_status: AcademicStatus;
}

// ============================================================
// 同步
// ============================================================

export interface SyncTriggerResponse {
  message: string;
  task_id: string;
}

export interface SyncStatusResponse {
  status: 'running' | 'success' | 'failed' | 'never_synced';
  module?: string;
  record_count?: number;
  error_msg?: string | null;
  started_at?: string;
  completed_at?: string;
}

// ============================================================
// 分页
// ============================================================

export interface PaginatedResponse<T> {
  total: number;
  data: T[];
}
