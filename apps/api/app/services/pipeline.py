from app.config import get_config
from app.models import BriefResponse, ThresholdConfig
from app.repository import EventRepository
from app.services.extract_events import extract_event_candidates
from app.services.fetch_sources import fetch_source_records
from app.services.generate_brief import generate_daily_brief
from app.services.score_events import score_and_rank_events


def build_today_brief() -> tuple[BriefResponse, EventRepository]:
    config = get_config()
    repo = EventRepository(config.database_path)
    repo.init_db()
    thresholds = repo.load_thresholds()
    if thresholds == ThresholdConfig():
        repo.save_thresholds(ThresholdConfig())
        thresholds = repo.load_thresholds()

    records = fetch_source_records()
    events = extract_event_candidates(records)
    ranked, manual_review = score_and_rank_events(events, thresholds)
    repo.save_events(ranked + manual_review)
    return generate_daily_brief(ranked, manual_review), repo
