from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_config
from app.models import BriefResponse, EventRecord
from app.repository import EventRepository
from app.services.chat import answer_demo_question
from app.services.generate_brief import generate_daily_brief
from app.services.pipeline import build_today_brief
from app.services.simulate_response import simulate_response


class ChatRequest(BaseModel):
    question: str


router = APIRouter(prefix="/api/chat", tags=["chat"])


def _repo() -> EventRepository:
    repo = EventRepository(get_config().database_path)
    repo.init_db()
    return repo


def _priority_score(event: EventRecord) -> float:
    score = 0.0
    score += (event.price_change_pct or 0.0) * 10
    score += 25 if event.is_core_district else 0
    score += 20 if event.product_focus in {"gold", "wedding"} else 0
    score += event.confidence * 10
    return score


def _load_brief_from_repo(repo: EventRepository) -> BriefResponse | None:
    events = repo.list_events()
    if not events:
        return None

    ranked = sorted(
        [event for event in events if event.report_level != "manual_review"],
        key=_priority_score,
        reverse=True,
    )
    manual_review = sorted(
        [event for event in events if event.report_level == "manual_review"],
        key=_priority_score,
        reverse=True,
    )
    return generate_daily_brief(ranked, manual_review)


@router.post("")
def chat(request: ChatRequest):
    repo = _repo()
    brief = _load_brief_from_repo(repo)
    if brief is None:
        brief, repo = build_today_brief()
    top_event = repo.get_event(brief.top_events[0].event_id) if brief.top_events else None
    simulation = simulate_response(top_event) if top_event else None
    return answer_demo_question(request.question, brief, simulation).model_dump()
