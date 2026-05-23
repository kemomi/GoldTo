"""
GoldTo API Routes
"""
from __future__ import annotations
import asyncio
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.simulation_engine import engine, SimStatus

router = APIRouter(prefix="/api")


# ── Request / Response models ─────────────────────────────────────────────────

class SimulateRequest(BaseModel):
    seed_text: str
    prediction_target: str = "预测未来价格走势"
    agent_count: int = 20
    num_rounds: int = 10


class ChatRequest(BaseModel):
    message: str


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    from config import settings
    return {
        "ok": True,
        "llm_mode": "mock" if settings.is_mock else "real",
        "model": settings.llm_model_name,
    }


# ── Simulate ──────────────────────────────────────────────────────────────────

@router.post("/simulate")
async def start_simulation(req: SimulateRequest, background_tasks: BackgroundTasks):
    if req.agent_count > 50:
        raise HTTPException(400, "agent_count 最大 50")
    if req.num_rounds > 40:
        raise HTTPException(400, "num_rounds 最大 40")

    sim_id = uuid.uuid4().hex[:8]
    session = engine.create_session(sim_id)
    session.prediction_goal = req.prediction_target
    session.seed_text = req.seed_text
    session.total_rounds = req.num_rounds

    from config import settings
    settings.agents_count = req.agent_count

    background_tasks.add_task(engine.run_pipeline, session)
    return {"sim_id": sim_id, "message": "仿真已启动"}


# ── Session status ────────────────────────────────────────────────────────────

@router.get("/simulation/{sim_id}")
async def get_simulation(sim_id: str):
    session = engine.get_session(sim_id)
    if not session:
        raise HTTPException(404, "仿真不存在")

    data = session.to_dict()
    # Build sentiment_trend from history
    rounds_map: dict[int, dict] = {}
    for item in session.history:
        r = item["round"]
        if r not in rounds_map:
            rounds_map[r] = {"bull": 0, "neut": 0, "bear": 0, "total": 0}
        rounds_map[r]["total"] += 1

    sentiment_trend = []
    for r, counts in sorted(rounds_map.items()):
        total = max(counts["total"], 1)
        agents_snap = [a.to_dict() for a in session.agents]
        bull = sum(1 for a in agents_snap if a["sentiment"] == "看涨")
        bear = sum(1 for a in agents_snap if a["sentiment"] == "看跌")
        neut = len(agents_snap) - bull - bear
        n = max(len(agents_snap), 1)
        sentiment_trend.append({
            "round": r,
            "breakdown": {
                "看涨": round(bull / n * 100),
                "中性": round(neut / n * 100),
                "看跌": round(bear / n * 100),
            },
            "dominant": "看涨" if bull >= bear else "看跌",
        })

    data["sentiment_trend"] = sentiment_trend
    data["rounds"] = session.history[-20:]  # last 20 interactions
    data["status"] = session.status.value if hasattr(session.status, "value") else session.status
    return data


@router.get("/simulation/{sim_id}/agents")
async def get_agents(sim_id: str):
    session = engine.get_session(sim_id)
    if not session:
        raise HTTPException(404, "仿真不存在")
    return [a.to_dict() for a in session.agents]


@router.get("/simulation/{sim_id}/graph")
async def get_graph(sim_id: str):
    session = engine.get_session(sim_id)
    if not session:
        raise HTTPException(404, "仿真不存在")
    return session.graph_data


# ── SSE event stream ──────────────────────────────────────────────────────────

@router.get("/simulation/{sim_id}/events")
async def event_stream(sim_id: str):
    session = engine.get_session(sim_id)
    if not session:
        raise HTTPException(404, "仿真不存在")

    import json

    async def generator():
        while True:
            try:
                event = await asyncio.wait_for(session.events.get(), timeout=30.0)
                data = json.dumps(event, ensure_ascii=False)
                yield f"data: {data}\n\n"
                if event.get("type") in ("completed", "error"):
                    break
            except asyncio.TimeoutError:
                yield ": ping\n\n"  # keepalive

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Chat ──────────────────────────────────────────────────────────────────────

@router.post("/simulation/{sim_id}/report/chat")
async def chat_with_report(sim_id: str, req: ChatRequest):
    session = engine.get_session(sim_id)
    if not session:
        raise HTTPException(404, "仿真不存在")
    if session.status != SimStatus.COMPLETED:
        raise HTTPException(400, "仿真尚未完成")
    response = await engine.chat(session, None, req.message)
    return {"response": response}


@router.post("/simulation/{sim_id}/agent/{agent_id}/chat")
async def chat_with_agent(sim_id: str, agent_id: str, req: ChatRequest):
    session = engine.get_session(sim_id)
    if not session:
        raise HTTPException(404, "仿真不存在")
    response = await engine.chat(session, agent_id, req.message)
    return {"response": response}


# ── List all sessions ─────────────────────────────────────────────────────────

@router.get("/simulations")
async def list_simulations():
    return engine.list_sessions()
