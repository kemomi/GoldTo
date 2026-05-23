from fastapi import APIRouter, HTTPException

from app.config import get_config
from app.repository import EventRepository
from app.services.simulate_response import simulate_response

router = APIRouter(prefix="/api/events", tags=["events"])


def _repo() -> EventRepository:
    repo = EventRepository(get_config().database_path)
    repo.init_db()
    return repo


@router.post("/{event_id}/simulate")
def simulate_event(event_id: str):
    event = _repo().get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return simulate_response(event).model_dump()
