"""
API Routes for GoldTo Backend
"""
from __future__ import annotations
import asyncio
import io
import json
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.simulation_engine import engine, SimStatus
from config import settings

router = APIRouter(prefix="/api")


# ── Session management ────────────────────────────────────────────────────────

@router.post("/sessions")
async def create_session():
    session_id = str(uuid.uuid4())[:8]
    session = engine.create_session(session_id)
    return {"session_id": session_id, "status": session.status}


@router.get("/sessions")
async def list_sessions():
    return {"sessions": engine.list_sessions()}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = _get_or_404(session_id)
    return session.to_dict()


# ── Upload & start ────────────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/upload")
async def upload_seed(
    session_id: str,
    prediction_goal: str = Form(...),
    rounds: Optional[int] = Form(None),
    agents_count: Optional[int] = Form(None),
    file: UploadFile = File(...),
):
    session = _get_or_404(session_id)

    if session.status not in (SimStatus.IDLE, SimStatus.ERROR):
        raise HTTPException(400, "Session already running or completed")

    # Extract text from file
    content = await file.read()
    text = _extract_text(content, file.filename or "")

    session.prediction_goal = prediction_goal
    session.seed_text = text
    if rounds:
        session.total_rounds = min(rounds, 100)
    if agents_count:
        settings.agents_count = min(agents_count, 30)

    return {
        "session_id": session_id,
        "text_length": len(text),
        "prediction_goal": prediction_goal,
        "message": "上传成功，调用 /simulate 开始仿真",
    }


@router.post("/sessions/{session_id}/simulate")
async def start_simulation(session_id: str):
    session = _get_or_404(session_id)

    if not session.seed_text:
        raise HTTPException(400, "请先上传种子文档")
    if session.status == SimStatus.SIMULATING:
        raise HTTPException(400, "仿真已在进行中")

    # Run in background
    asyncio.create_task(engine.run_pipeline(session))
    return {"message": "仿真已启动", "session_id": session_id}


# ── SSE Stream ────────────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/stream")
async def stream_events(session_id: str):
    session = _get_or_404(session_id)

    async def event_generator():
        # Send current state immediately
        yield _sse({"type": "init", "data": session.to_dict()})

        while True:
            try:
                event = await asyncio.wait_for(session.events.get(), timeout=30)
                yield _sse(event)

                if event["type"] in ("completed", "error"):
                    break
            except asyncio.TimeoutError:
                yield _sse({"type": "heartbeat", "data": {
                    "status": session.status,
                    "progress": session.progress,
                }})

                if session.status in (SimStatus.COMPLETED, SimStatus.ERROR):
                    break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Report & Chat ─────────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/report")
async def get_report(session_id: str):
    session = _get_or_404(session_id)
    if not session.report:
        raise HTTPException(404, "报告尚未生成")
    return {"report": session.report, "session_id": session_id}


class ChatRequest(BaseModel):
    message: str
    agent_id: Optional[str] = None  # None or "report" for ReportAgent


@router.post("/sessions/{session_id}/chat")
async def chat(session_id: str, req: ChatRequest):
    session = _get_or_404(session_id)
    if session.status not in (SimStatus.COMPLETED,):
        raise HTTPException(400, "仿真尚未完成，无法对话")

    response = await engine.chat(session, req.agent_id, req.message)
    return {
        "response": response,
        "agent_id": req.agent_id or "report",
        "message": req.message,
    }


@router.get("/sessions/{session_id}/agents")
async def get_agents(session_id: str):
    session = _get_or_404(session_id)
    return {"agents": [a.to_dict() for a in session.agents]}


@router.get("/sessions/{session_id}/graph")
async def get_graph(session_id: str):
    session = _get_or_404(session_id)
    return {"graph": session.graph_data, "summary": session.graph_summary}


@router.get("/sessions/{session_id}/history")
async def get_history(session_id: str, limit: int = 50, offset: int = 0):
    session = _get_or_404(session_id)
    total = len(session.history)
    items = session.history[offset: offset + limit]
    return {"history": items, "total": total, "offset": offset, "limit": limit}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_404(session_id: str):
    session = engine.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")
    return session


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _extract_text(content: bytes, filename: str) -> str:
    """Extract plain text from uploaded file."""
    fname = filename.lower()

    if fname.endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)
        except Exception as e:
            print(f"[Upload] PDF parse error: {e}")
            return content.decode("utf-8", errors="replace")

    # Default: treat as text
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")
