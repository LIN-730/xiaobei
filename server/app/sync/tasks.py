# tasks.py — Celery 异步同步任务
import asyncio
import time
from typing import Dict, Any, List
from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.sync.celery_app import celery_app
from app.sync.session_pool import session_pool
from app.config import settings

# 并发控制：同一时间最多 3 个用户在执行同步
_SYNC_SEMAPHORE = asyncio.Semaphore(3)


# ═══════════════════════════════════════════════════════════
# 爬虫工厂 — 模块名 → 爬虫类
# ═══════════════════════════════════════════════════════════

def _build_crawler(module: str, session, student_no: str, base_url: str):
    """根据模块名创建对应的爬虫实例"""
    from app.crawlers import (
        courses, scores, exams, student_info, academic_status,
        academic_warning, score_detail, training_plan,
        selected_courses, classrooms, notifications, all_courses,
        graduation,
    )

    modules: Dict[str, Any] = {
        "courses":           courses.CourseCrawler,
        "scores":            scores.ScoreCrawler,
        "exams":             exams.ExamCrawler,
        "student_info":      student_info.StudentInfoCrawler,
        "academic_status":   academic_status.AcademicStatusCrawler,
        "academic_warning":  academic_warning.AcademicWarningCrawler,
        "score_detail":      score_detail.ScoreDetailCrawler,
        "training_plan":     training_plan.TrainingPlanCrawler,
        "selected_courses":  selected_courses.SelectedCourseCrawler,
        "classrooms":        classrooms.ClassroomCrawler,
        "notifications":     notifications.NotificationCrawler,
        "all_courses":       all_courses.AllCourseCrawler,
        "graduation":        graduation.GraduationAuditCrawler,
    }

    crawler_cls = modules.get(module)
    if crawler_cls is None:
        raise ValueError(f"未知模块: {module}")

    return crawler_cls(session, student_no=student_no, base_url=base_url)


# ═══════════════════════════════════════════════════════════
# 异步同步任务
# ═══════════════════════════════════════════════════════════

@celery_app.task(name="sync_user_module", bind=True)
def sync_user_module(self, user_id: str, module: str):
    """
    异步同步单个用户 + 单个模块。

    Args:
        user_id: 用户 UUID
        module: 爬虫模块名 (courses/scores/exams/...)
    """
    return asyncio.run(_sync_user_module_async(user_id, module))


@celery_app.task(name="sync_user_all", bind=True)
def sync_user_all(self, user_id: str):
    """
    异步同步单个用户的所有模块。

    Args:
        user_id: 用户 UUID
    """
    MODULES = [
        "student_info", "courses", "scores", "score_detail",
        "exams", "academic_status", "academic_warning",
        "training_plan", "selected_courses", "classrooms",
        "notifications", "all_courses",
    ]
    results = {}
    for module in MODULES:
        try:
            result = sync_user_module.delay(user_id, module)
            results[module] = result.id
        except Exception as e:
            results[module] = f"error: {e}"
    return results


async def _sync_user_module_async(user_id: str, module: str) -> dict:
    """同步核心逻辑（异步）"""
    start_time = time.time()

    # 1. 从数据库读取用户凭据
    engine = create_engine(settings.DATABASE_URL_SYNC)
    with Session(engine) as db:
        from app.database.models import EduCredential
        from app.auth.security import decrypt_credential

        cred = db.query(EduCredential).filter(
            EduCredential.user_id == user_id,
            EduCredential.is_valid == True,
        ).first()

        if not cred:
            return {"status": "skipped", "reason": "未绑定有效教务凭证"}

        student_no = cred.student_no
        base_url = cred.base_url
        login_account = cred.login_account
        edu_password = decrypt_credential(cred.encrypted_password)

    # 2. 获取或创建教务 Session
    async with _SYNC_SEMAPHORE:
        edu_session = await session_pool.get(user_id)
        if edu_session is None:
            from app.crawlers.auth import login_edu
            edu_session = login_edu(login_account, edu_password, base_url)
            if edu_session is None:
                return {"status": "failed", "reason": "教务系统登录失败"}
            await session_pool.set(user_id, edu_session)

    # 3. 创建爬虫并执行
    try:
        crawler = _build_crawler(module, edu_session, student_no, base_url)
        data = crawler.crawl()
    except Exception as e:
        # 登录态可能过期，清除缓存
        await session_pool.invalidate(user_id)
        return {"status": "failed", "reason": f"爬虫执行失败: {e}"}

    if data is None:
        return {"status": "skipped", "reason": "无数据返回"}

    # 4. 保存到数据库 (通过 Repository)
    from app.database.repositories.repos import (
        CourseRepo, ScoreRepo, ScoreDetailRepo, ExamRepo,
        StudentRepo, AcademicWarningRepo, AcademicStatusRepo,
        GraduationAuditRepo, ClassroomRepo, TrainingPlanRepo,
        SelectedCourseRepo, NotificationRepo, SyncLogRepo,
    )

    repo_map = {
        "courses":          CourseRepo,
        "scores":           ScoreRepo,
        "exams":            ExamRepo,
        "student_info":     StudentRepo,
        "academic_status":  AcademicStatusRepo,
        "academic_warning": AcademicWarningRepo,
        "score_detail":     ScoreDetailRepo,
        "training_plan":    TrainingPlanRepo,
        "selected_courses": SelectedCourseRepo,
        "classrooms":       ClassroomRepo,
        "notifications":    NotificationRepo,
        "all_courses":      None,  # 无需存储
        "graduation":       GraduationAuditRepo,
    }

    repo_cls = repo_map.get(module)
    record_count = 0

    if repo_cls is not None and data:
        with Session(engine) as db:
            repo = repo_cls(db, user_id)
            record_count = repo.replace_all(data)  # 同步执行

    # 5. 记录同步日志
    duration_ms = int((time.time() - start_time) * 1000)
    with Session(engine) as db:
        log_repo = SyncLogRepo(db, user_id)
        log_repo.log_complete(module, record_count, duration_ms)

    return {
        "status": "success",
        "module": module,
        "record_count": record_count,
        "duration_ms": duration_ms,
    }
