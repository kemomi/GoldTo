from typing import Literal

from pydantic import BaseModel, Field

ReportLevel = Literal["must_report", "optional", "ignore", "manual_review"]
OptionId = Literal["hold", "local_follow", "limited_follow", "escalate_attention"]
RiskLevel = Literal["low", "medium", "high"]
SourceType = Literal[
    "competitor_official",
    "mall_official",
    "platform_announcement",
    "industry_news",
    "regulation_update",
    "seeded_media",
]
FetchStatus = Literal["live", "fixture_fallback"]


class ThresholdConfig(BaseModel):
    must_report_price_change_pct: float = 5.0
    optional_price_change_pct: float = 2.0


class SourceRecord(BaseModel):
    source_id: str
    market: str
    brand: str
    source_type: SourceType
    language: Literal["zh-Hans", "zh-Hant", "en"]
    url: str
    title: str
    body: str
    captured_at: str
    fetch_status: FetchStatus = "live"
    fallback_reason: str | None = None


class EventRecord(BaseModel):
    event_id: str
    market: str
    brand: str
    district: str
    event_type: Literal[
        "price_change",
        "promotion",
        "new_store",
        "store_move",
        "collection_launch",
        "platform_update",
        "industry_trend",
        "compliance_update",
    ]
    product_focus: Literal["gold", "wedding", "light_luxury", "high_jewelry", "other"]
    title: str
    summary_zh: str
    source_url: str
    source_id: str
    source_type: SourceType = "competitor_official"
    occurred_at: str
    price_change_pct: float | None = None
    is_core_district: bool = False
    confidence: float = 0.0
    report_level: ReportLevel = "optional"
    evidence: list[str] = Field(default_factory=list)
    fetch_status: FetchStatus = "live"
    fallback_reason: str | None = None


class SourceSummary(BaseModel):
    total_sources: int
    live_count: int
    fallback_count: int
    categories: list[SourceType] = Field(default_factory=list)


class BriefResponse(BaseModel):
    overview: str
    top_events: list[EventRecord]
    compliance_alerts: list[str]
    opportunities: list[str]
    role_actions: dict[str, str]
    manual_review: list[EventRecord] = Field(default_factory=list)
    source_summary: SourceSummary | None = None


class DimensionImpact(BaseModel):
    name: str
    level: RiskLevel
    rationale: str


class StrategyOption(BaseModel):
    option_id: OptionId
    label_zh: str
    impacts: list[DimensionImpact]
    rationale: str


class SimulationResponse(BaseModel):
    event_id: str
    options: list[StrategyOption]
    recommended_option_id: OptionId
    recommended_reason: str
    follow_up: list[str]


class ChatResponse(BaseModel):
    answer: str
    cited_event_ids: list[str] = Field(default_factory=list)
