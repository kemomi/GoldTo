"""
APScheduler 配置 — 定时任务调度器
使用 BackgroundScheduler 在 FastAPI 后台运行。
"""
from __future__ import annotations
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

# 全局调度器实例
scheduler = BackgroundScheduler(timezone=ZoneInfo("Asia/Shanghai"))


def start_scheduler():
    """启动调度器。在 FastAPI startup 事件中调用。"""
    if not scheduler.running:
        scheduler.start()
        print("[Scheduler] APScheduler started")


def shutdown_scheduler():
    """关闭调度器。在 FastAPI shutdown 事件中调用。"""
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] APScheduler shutdown")


def schedule_daily_job(job_func, hour: int, minute: int, job_id: str = "daily_briefing"):
    """
    注册每日定时任务。
    :param job_func: 任务函数
    :param hour: 小时 (0-23)
    :param minute: 分钟 (0-59)
    :param job_id: 任务 ID
    """
    # 先移除同名旧任务
    existing = scheduler.get_job(job_id)
    if existing:
        scheduler.remove_job(job_id)

    trigger = CronTrigger(hour=hour, minute=minute)
    scheduler.add_job(
        job_func,
        trigger=trigger,
        id=job_id,
        name="Daily Strategic Briefing",
        replace_existing=True,
    )
    print(f"[Scheduler] Daily job scheduled at {hour:02d}:{minute:02d} (job_id={job_id})")


def remove_daily_job(job_id: str = "daily_briefing"):
    """移除每日任务。"""
    existing = scheduler.get_job(job_id)
    if existing:
        scheduler.remove_job(job_id)
        print(f"[Scheduler] Job {job_id} removed")


def get_scheduled_jobs():
    """获取当前所有已注册任务。"""
    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        }
        for job in scheduler.get_jobs()
    ]
