from app.models import BriefResponse, EventRecord


def generate_daily_brief(events: list[EventRecord], manual_review: list[EventRecord]) -> BriefResponse:
    must_report = [event for event in events if event.report_level == "must_report"]
    top_events: list[EventRecord] = []
    used_markets: set[str] = set()

    for event in must_report:
        if event.market in used_markets:
            continue
        top_events.append(event)
        used_markets.add(event.market)
        if len(top_events) == 5:
            break

    return BriefResponse(
        overview="今日五大市场整体竞争烈度偏高，香港婚嫁黄金相关异动对晨会优先级最高。",
        top_events=top_events,
        compliance_alerts=["美国贵金属标识与钻石溯源内容需持续关注。"],
        opportunities=["新加坡高端婚嫁珠宝内容热度可作为新品观察线索。"],
        role_actions={
            "hq": "总部管理层重点关注香港核心商圈应对级别是否上收决策。",
            "ops": "区域运营今日优先巡检尖沙咀商圈并准备局部促销预案。",
            "marketing": "市场策略岗同步检查婚嫁黄金内容方向与投放素材。",
        },
        manual_review=manual_review,
    )
