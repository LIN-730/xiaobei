// ============================================================
// 考试类型
// ============================================================

/** 考试安排 — GET /exams */
export interface Exam {
  course_name: string;
  exam_date: string; // "2026-06-20"
  exam_time: string; // "08:00-10:00"
  classroom: string;
  seat_no: string;
  exam_type: string; // "期末" | "期中" | ...
  campus: string;
}

export interface ExamListResponse {
  total: number;
  data: Exam[];
}
