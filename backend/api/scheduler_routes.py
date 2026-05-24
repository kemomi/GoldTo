"""
调度管理 API — 查看/更新每日简报定时任务
"""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.database import get_db
from models.user import UserConfig
from scheduler.trigger import (
    scheduler,
    schedule_daily_job,
    remove_daily_job,
    get_scheduled_jobs,
)
from scheduler.daily_briefing_job import DailyBriefingJob

router = APIRouter(prefix="/api")


# ── Schemas ──

class ScheduleUpdate(BaseModel):
    hour: int
    minute: int
    enabled: bool = True


# ── Helpers ──

def _get_user(db: Session) -> UserConfig:
    user = db.query(UserConfig).first()
    if not user:
        user = UserConfig(id=1)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# ── Routes ──

@router.get("/scheduler/jobs")
async def list_jobs():
    """获取当前所有定时任务。"""
    return {"jobs": get_scheduled_jobs(), "scheduler_running": scheduler.running}


@router.get("/scheduler/daily-briefing")
async def get_daily_briefing_schedule(db: Session = Depends(get_db)):
    """获取每日简报任务的当前配置。"""
    user = _get_user(db)
    job = scheduler.get_job("daily_briefing")

    return {
        "enabled": user.push_enabled,
        "push_time": user.push_time,
        "timezone": user.timezone,
        "push_channels": user.push_channels,
        "scheduled": job is not None,
        "next_run_time": job.next_run_time.isoformat() if job and job.next_run_time else None,
    }


@router.post("/scheduler/daily-briefing")
async def update_daily_briefing_schedule(data: ScheduleUpdate, db: Session = Depends(get_db)):
    """更新每日简报推送时间。"""
    user = _get_user(db)

    if not (0 <= data.hour <= 23 and 0 <= data.minute <= 59):
        raise HTTPException(400, "时间格式错误，hour: 0-23, minute: 0-59")

    user.push_time = f"{data.hour:02d}:{data.minute:02d}"
    user.push_enabled = data.enabled
    db.commit()

    # 重新调度
    if data.enabled:
        job = DailyBriefingJob()
        schedule_daily_job(job.run, data.hour, data.minute, job_id="daily_briefing")
    else:
        remove_daily_job("daily_briefing")

    return {
        "message": "定时任务已更新",
        "push_time": user.push_time,
        "enabled": user.push_enabled,
    }


@router.post("/scheduler/daily-briefing/run-now")
async def run_daily_briefing_now():
    """立即执行一次每日简报任务（手动触发）。"""
    job = DailyBriefingJob()
    job.run()
    return {"message": "每日简报任务已手动触发，请稍后查看结果"}


@router.post("/scheduler/daily-briefing/stop")
async def stop_daily_briefing():
    """暂停每日简报定时任务。"""
    remove_daily_job("daily_briefing")
    return {"message": "每日简报定时任务已暂停"}
