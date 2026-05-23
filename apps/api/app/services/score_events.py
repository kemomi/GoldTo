from app.models import EventRecord, ThresholdConfig


def _classify_price_change(event: EventRecord, config: ThresholdConfig) -> str:
    if event.confidence < 0.75:
        return "manual_review"
    pct = event.price_change_pct or 0.0
    if pct >= config.must_report_price_change_pct:
        return "must_report"
    if pct >= config.optional_price_change_pct:
        return "optional"
    return "ignore"


def _priority_score(event: EventRecord) -> float:
    score = 0.0
    score += (event.price_change_pct or 0.0) * 10
    score += 25 if event.is_core_district else 0
    score += 20 if event.product_focus in {"gold", "wedding"} else 0
    score += event.confidence * 10
    return score


def score_and_rank_events(events: list[EventRecord], config: ThresholdConfig) -> tuple[list[EventRecord], list[EventRecord]]:
    ranked: list[tuple[float, EventRecord]] = []
    manual_review: list[EventRecord] = []

    for event in events:
        event.report_level = _classify_price_change(event, config)
        if event.report_level == "manual_review":
            manual_review.append(event)
            continue
        ranked.append((_priority_score(event), event))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return [event for _, event in ranked], manual_review
