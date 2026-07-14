// ============================================================
// 学业规划类型 — 对应 /api/v1/planning/*
// ============================================================

// ---- 学分缺口 ----

/** 单个模块组的学分缺口 */
export interface CreditGapModule {
  module_name: string;
  required: number;
  earned: number;
  remaining: number;
}

export interface CreditGapResponse {
  modules: CreditGapModule[];
  total_required: number;
  total_earned: number;
  total_remaining: number;
}

// ---- 必修课检查 ----

export interface RequiredCourseStatus {
  course_name: string;
  course_code: string;
  is_completed: boolean;
  grade?: string;
  term?: string;
}

export interface RequiredCoursesResponse {
  courses: RequiredCourseStatus[];
  completed_count: number;
  total_count: number;
}

// ---- 选课推荐 ----

export interface CourseRecommendation {
  course_name: string;
  course_code: string;
  credit: number;
  course_type: string;
  teacher?: string;
  reason?: string;
}

export interface RecommendResponse {
  recommendations: CourseRecommendation[];
  target_semester?: string;
}

// ---- 学业路径 ----

export interface SemesterPlan {
  semester: string;
  courses: Array<{
    course_name: string;
    course_code: string;
    credit: number;
  }>;
  total_credits: number;
}

export interface PathPlanResponse {
  semesters: SemesterPlan[];
  remaining_credits: number;
}
