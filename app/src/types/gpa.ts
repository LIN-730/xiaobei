// ============================================================
// GPA 模拟器类型 — POST /scores/gpa-simulate
// ============================================================

/** 单门模拟课程输入 */
export interface GpaSimulateCourseInput {
  name: string;
  credit: number;
  score: number; // 0-100
}

/** 绩点对照表条目 */
export interface GpTableRow {
  grade: string; // "A+", "A", ...
  grade_point: number; // 4.33, 4.0, ...
  score_range: string; // "95-100", ...
}

/** 模拟结果中的课程明细 */
export interface GpaSimulateCourseResult {
  name: string;
  credit: number;
  score: number;
  grade_point: number;
  gp_contribution: number;
}

/** GPA 模拟请求 */
export interface GpaSimulateRequest {
  courses: GpaSimulateCourseInput[];
}

/** GPA 模拟响应 */
export interface GpaSimulateResponse {
  current_gpa: number;
  current_credits: number;
  simulated_gpa: number;
  gpa_change: number;
  new_total_credits: number;
  courses: GpaSimulateCourseResult[];
  gp_table: GpTableRow[];
  message?: string;
}
