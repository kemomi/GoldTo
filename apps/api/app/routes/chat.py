from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_config
from app.repository import EventRepository
from app.services.chat import answer_demo_question
from app.services.pipeline import build_today_brief
from app.services.simulate_response import simulate_response


class ChatRequest(BaseModel):
    question: str


router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
def chat(request: ChatRequest):
    brief, _ = build_today_brief()
    repo = EventRepository(get_config().database_path)
    repo.init_db()
    top_event = repo.get_event(brief.top_events[0].event_id) if brief.top_events else None
    simulation = simulate_response(top_event) if top_event else None
    return answer_demo_question(request.question, brief, simulation).model_dump()
