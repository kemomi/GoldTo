"""
GoldTo Backend — FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from api.routes import router as session_router
from api.user_routes import router as user_router
from api.briefing_routes import router as briefing_router
from api.scheduler_routes import router as scheduler_router
from api.source_routes import router as source_router
from api.dashboard_routes import router as dashboard_router
from api.alert_routes import router as alert_router
from config import settings
from models.database import init_db, SessionLocal
from models.user import UserConfig
from scheduler.trigger import start_scheduler, shutdown_scheduler, schedule_daily_job
from scheduler.daily_briefing_job import DailyBriefingJob

app = FastAPI(
    title="GoldTo Intelligence API",
    description="多 Agent 情报分析引擎 — CrewAI + WorldMonitor + 每日战略简报",
    version="2.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(session_router)
app.include_router(user_router)
app.include_router(briefing_router)
app.include_router(scheduler_router)
app.include_router(source_router)
app.include_router(dashboard_router)
app.include_router(alert_router)


@app.get("/")
async def root():
    return {
        "name": "GoldTo Intelligence",
        "version": "2.0.0-daily-briefing",
        "status": "running",
        "docs": "/docs",
        "mode": "mock" if settings.is_mock else "real",
        "llm_model": settings.llm_model_name,
        "crewai_available": True,
        "features": ["session_analysis", "daily_briefing", "multi_channel_push"],
    }


@app.get("/health")
async def health():
    from models.database import SessionLocal
    from models.user import UserConfig
    db = SessionLocal()
    try:
        user_count = db.query(UserConfig).count()
    except Exception:
        user_count = 0
    finally:
        db.close()

    return {
        "status": "ok",
        "llm_mode": "mock" if settings.is_mock else "real",
        "model": settings.llm_model_name,
        "zep_enabled": bool(settings.zep_api_key),
        "database": "connected",
        "user_configs": user_count,
    }


# ── Lifecycle ──

@app.on_event("startup")
async def startup():
    # 1. 初始化数据库
    init_db()
    print("[Startup] Database initialized")

    # 2. 启动 APScheduler
    start_scheduler()

    # 3. 读取用户配置，如果有推送时间则注册定时任务
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        user = db.query(UserConfig).first()
        if user and user.push_enabled and user.push_time:
            try:
                hour, minute = map(int, user.push_time.split(":"))
                job = DailyBriefingJob()
                schedule_daily_job(job.run, hour, minute, job_id="daily_briefing")
            except Exception as e:
                print(f"[Startup] Failed to schedule daily job: {e}")
    finally:
        db.close()


@app.on_event("shutdown")
async def shutdown():
    shutdown_scheduler()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5001, reload=True)
