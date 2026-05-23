from fastapi import APIRouter

from app.config import get_config
from app.models import ThresholdConfig
from app.repository import EventRepository

router = APIRouter(prefix="/api/config", tags=["config"])


def _repo() -> EventRepository:
    repo = EventRepository(get_config().database_path)
    repo.init_db()
    return repo


@router.patch("/thresholds")
def update_thresholds(payload: ThresholdConfig):
    _repo().save_thresholds(payload)
    return payload.model_dump()


@router.get("/thresholds")
def get_thresholds():
    return _repo().load_thresholds().model_dump()
