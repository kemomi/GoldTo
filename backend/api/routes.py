"""
API Routes — 情报分析版
流程：创建会话 → 数据采集 → CrewAI 分析 → SSE 推流 → 简报
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

from intelligence.analysis_engine import engine, AnalysisStatus
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


# ── Data Collection ───────────────────────────────────────────────────────────

class CollectRequest(BaseModel):
    topic: str


@router.post("/sessions/{session_id}/collect")
async def collect_data(session_id: str, req: CollectRequest):
    """Step 1: 从 World Monitor 数据源采集事件"""
    session = _get_or_404(session_id)

    if session.status not in (AnalysisStatus.IDLE, AnalysisStatus.ERROR):
        raise HTTPException(400, "会话已在进行中或已完成")

    await engine.collect_data(session, req.topic)
    return {"message": "数据采集完成", "session_id": session_id, "topic": req.topic}


# ── Upload seed (保留 GoldTo 原有能力) ────────────────────────────────────────

@router.post("/sessions/{session_id}/upload")
async def upload_seed(
    session_id: str,
    prediction_goal: str = Form(...),
    file: UploadFile = File(...),
):
    """上传种子文档作为补充材料"""
    session = _get_or_404(session_id)

    content = await file.read()
    text = _extract_text(content, file.filename or "")

    # 将上传内容附加到 topic
    if session.topic:
        session.topic += f"\n[补充材料]: {text[:500]}"
    else:
        session.topic = f"{prediction_goal}\n[补充材料]: {text[:500]}"

    return {
        "session_id": session_id,
        "text_length": len(text),
        "message": "种子文档已上传",
    }


# ── Analysis ──────────────────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/analyze")
async def start_analysis(session_id: str):
    """Step 2: 启动 CrewAI 多 Agent 分析"""
    session = _get_or_404(session_id)

    if not session.events_collected and not session.topic:
        raise HTTPException(400, "请先调用 /collect 采集数据或上传种子文档")
    if session.status == AnalysisStatus.ANALYZING:
        raise HTTPException(400, "分析已在进行中")

    asyncio.create_task(engine.run_analysis(session))
    return {"message": "CrewAI 分析已启动", "session_id": session_id}


# ── SSE Stream ────────────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/stream")
async def stream_events(session_id: str):
    session = _get_or_404(session_id)

    async def event_generator():
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

                if session.status in (AnalysisStatus.COMPLETED, AnalysisStatus.ERROR):
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


# ── Briefing & Chat ───────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/briefing")
async def get_briefing(session_id: str):
    session = _get_or_404(session_id)
    if not session.briefing:
        raise HTTPException(404, "简报尚未生成")
    return {"briefing": session.briefing, "session_id": session_id}


class ChatRequest(BaseModel):
    message: str


@router.post("/sessions/{session_id}/chat")
async def chat(session_id: str, req: ChatRequest):
    session = _get_or_404(session_id)
    response = await engine.chat(session, req.message)
    return {"response": response, "message": req.message}


@router.get("/sessions/{session_id}/events")
async def get_events(session_id: str):
    session = _get_or_404(session_id)
    return {"events": session.events_collected}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_404(session_id: str):
    session = engine.get_session(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")
    return session


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _extract_text(content: bytes, filename: str) -> str:
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

    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")
