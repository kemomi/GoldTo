from fastapi import APIRouter

from app.services.pipeline import build_today_brief

router = APIRouter(prefix="/api/briefs", tags=["briefs"])


@router.get("/today")
def get_today_brief():
    brief, _ = build_today_brief()
    return brief.model_dump()
