// ============================================================
// 成绩类型
// ============================================================

/** 成绩项 — GET /scores */
export interface Score {
  course_name: string;
  course_code: string;
  term: string; // "2024-2025-1"
  score: string; // 可能是 "92" 或 "优秀" 等
  credit: number;
  grade_point: number;
  course_type: string;
  exam_type: string;
}

export interface GpaStats {
  total_credits: number;
  avg_gpa: number;
}

export interface ScoreListResponse {
  total: number;
  gpa_stats: GpaStats;
  data: Score[];
}

/** 成绩明细 — GET /scores/detail */
export interface ScoreDetailItem {
  course_name: string;
  course_code: string;
  term: string;
  score: string;
  credit: number;
  grade_point: number;
  course_type: string;
  exam_type: string;
}

/** 学期列表 — GET /scores/terms */
export interface TermsResponse {
  data: string[];
}
