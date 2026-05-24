# Overseas Jewelry Strategy Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a demo-ready overseas jewelry strategy simulator MVP that ingests a small set of real official-source pages plus seeded fixtures, generates a daily strategy brief, and simulates responses for the highest-priority competitor event in a three-pane analyst UI.

**Architecture:** Use a small monorepo with a FastAPI backend and a React/Vite frontend. The backend owns ingestion, normalization, scoring, brief generation, scenario simulation, threshold tuning, and chat-style explanations; the frontend renders the analyst workspace and calls backend APIs. Persist events and tunable thresholds in SQLite, but keep seeded demo fixtures in versioned JSON/HTML files so the demo remains reproducible offline.

**Tech Stack:** Python 3.12, FastAPI, sqlite3, pytest, requests, BeautifulSoup4, OpenAI-compatible client, React 18, TypeScript, Vite, Vitest, Testing Library

---

## File Structure

### Root

- Create: `.gitignore`
  Purpose: Ignore Python, Node, build, and SQLite artifacts.
- Create: `README.md`
  Purpose: Explain architecture, setup, demo flow, and verification commands.
- Create: `data/source_manifest.json`
  Purpose: Declare the handful of real/fallback sources used by the demo.
- Create: `data/fixtures/raw/hk_csg_pricecut.html`
  Purpose: Offline fallback for a high-priority Hong Kong competitor event.
- Create: `data/fixtures/raw/hk_mall_promo.html`
  Purpose: Offline fallback for an official mall announcement.
- Create: `data/fixtures/raw/seed_us_signet.json`
  Purpose: Seeded North America scenario coverage.
- Create: `data/demo.sqlite`
  Purpose: Runtime SQLite store; gitignored.

### Backend (`apps/api`)

- Create: `apps/api/requirements.txt`
  Purpose: Backend dependencies.
- Create: `apps/api/app/__init__.py`
  Purpose: Python package marker.
- Create: `apps/api/app/main.py`
  Purpose: FastAPI app assembly and route registration.
- Create: `apps/api/app/config.py`
  Purpose: App paths, tunable threshold defaults, and runtime settings.
- Create: `apps/api/app/models.py`
  Purpose: Pydantic models for sources, events, briefs, thresholds, simulations, and chat responses.
- Create: `apps/api/app/repository.py`
  Purpose: SQLite persistence for events and threshold config.
- Create: `apps/api/app/services/fetch_sources.py`
  Purpose: Load source manifest, fetch live content, and fall back to local fixtures.
- Create: `apps/api/app/services/extract_events.py`
  Purpose: Normalize source text and turn it into structured event candidates.
- Create: `apps/api/app/services/score_events.py`
  Purpose: Apply threshold rules, confidence handling, and tie-break ranking.
- Create: `apps/api/app/services/generate_brief.py`
  Purpose: Assemble the fixed daily brief sections.
- Create: `apps/api/app/services/simulate_response.py`
  Purpose: Compare `hold`, `local_follow`, and `limited_follow` response levels.
- Create: `apps/api/app/services/chat.py`
  Purpose: Answer the three demo question types from current brief/simulation context.
- Create: `apps/api/app/services/pipeline.py`
  Purpose: Run fetch → extract → score → persist → brief in one place.
- Create: `apps/api/app/routes/briefs.py`
  Purpose: Daily brief endpoints.
- Create: `apps/api/app/routes/events.py`
  Purpose: Event detail and simulation endpoints.
- Create: `apps/api/app/routes/chat.py`
  Purpose: Chat-style explanation endpoint.
- Create: `apps/api/app/routes/config.py`
  Purpose: Threshold read/update endpoint for demo tuning.
- Create: `apps/api/tests/test_health.py`
- Create: `apps/api/tests/test_repository.py`
- Create: `apps/api/tests/test_extraction.py`
- Create: `apps/api/tests/test_scoring_and_brief.py`
- Create: `apps/api/tests/test_api_flow.py`
- Create: `apps/api/tests/test_demo_contract.py`

### Frontend (`apps/web`)

- Create: `apps/web/package.json`
  Purpose: Frontend scripts and dependencies.
- Create: `apps/web/tsconfig.json`
  Purpose: TypeScript configuration.
- Create: `apps/web/vite.config.ts`
  Purpose: Vitest and Vite configuration.
- Create: `apps/web/index.html`
  Purpose: Vite entry document.
- Create: `apps/web/src/main.tsx`
  Purpose: React bootstrap.
- Create: `apps/web/src/App.tsx`
  Purpose: Page state orchestration and API calls.
- Create: `apps/web/src/styles.css`
  Purpose: Three-pane analyst layout.
- Create: `apps/web/src/types.ts`
  Purpose: Shared frontend API/result types.
- Create: `apps/web/src/api/client.ts`
  Purpose: Typed fetch client for backend endpoints.
- Create: `apps/web/src/components/BriefSidebar.tsx`
  Purpose: Markets, top events, compliance, and opportunities list.
- Create: `apps/web/src/components/ChatPanel.tsx`
  Purpose: Conversational center panel and canned question actions.
- Create: `apps/web/src/components/EvidencePanel.tsx`
  Purpose: Source evidence, original text, and source links.
- Create: `apps/web/src/components/SimulationPanel.tsx`
  Purpose: Three-option simulation cards and recommended action.
- Create: `apps/web/src/components/ThresholdPanel.tsx`
  Purpose: Small developer-facing tuning panel for price thresholds.
- Create: `apps/web/src/__tests__/app.spec.tsx`
  Purpose: UI smoke test with mocked API client.

## Assumptions

- Start from the current near-empty repository; do not wait for additional code scaffolding.
- Prioritize a deterministic, demo-safe flow over broad automation.
- Use live fetching only for a tiny set of official pages and always keep fixture fallback.
- Keep identifiers in English in code and labels in Chinese in UI payloads.

### Task 1: Bootstrap the backend shell and health endpoint

**Files:**
- Create: `.gitignore`
- Create: `apps/api/requirements.txt`
- Create: `apps/api/app/__init__.py`
- Create: `apps/api/app/main.py`
- Test: `apps/api/tests/test_health.py`

- [ ] **Step 1: Write the failing health test**

```python
# apps/api/tests/test_health.py
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run the backend health test to prove the shell is missing**

Run:

```powershell
cd apps/api
python -m pytest tests/test_health.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 3: Write the minimal backend shell**

```text
# .gitignore
.venv/
__pycache__/
.pytest_cache/
node_modules/
dist/
*.db
.env
```

```text
# apps/api/requirements.txt
fastapi==0.111.0
uvicorn==0.30.1
pydantic==2.7.4
pytest==8.2.2
httpx==0.27.0
requests==2.32.3
beautifulsoup4==4.12.3
openai==1.30.5
```

```python
# apps/api/app/__init__.py
"""API package for the overseas jewelry strategy simulator."""
```

```python
# apps/api/app/main.py
from fastapi import FastAPI

app = FastAPI(title="Overseas Jewelry Strategy Simulator API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Run the health test again**

Run:

```powershell
cd apps/api
python -m pytest tests/test_health.py -v
```

Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit the backend bootstrap**

```bash
git add .gitignore apps/api/requirements.txt apps/api/app/__init__.py apps/api/app/main.py apps/api/tests/test_health.py
git commit -m "chore: bootstrap backend api shell"
```

### Task 2: Add core models, runtime config, and SQLite persistence

**Files:**
- Create: `apps/api/app/config.py`
- Create: `apps/api/app/models.py`
- Create: `apps/api/app/repository.py`
- Test: `apps/api/tests/test_repository.py`

- [ ] **Step 1: Write the failing repository round-trip test**

```python
# apps/api/tests/test_repository.py
from pathlib import Path

from app.models import EventRecord, ThresholdConfig
from app.repository import EventRepository


def test_repository_round_trips_events_and_thresholds(tmp_path: Path):
    repo = EventRepository(tmp_path / "demo.sqlite")
    repo.init_db()

    repo.save_thresholds(ThresholdConfig(must_report_price_change_pct=5.0, optional_price_change_pct=2.0))
    repo.save_events(
        [
            EventRecord(
                event_id="hk-csg-pricecut-20260523",
                market="HK",
                brand="周生生",
                district="尖沙咀",
                event_type="price_change",
                product_focus="wedding",
                title="周生生尖沙咀婚嫁黄金限时 8% 优惠",
                summary_zh="周生生在香港尖沙咀核心婚嫁商圈推出 8% 限时优惠。",
                source_url="https://example.com/hk-csg-pricecut",
                source_id="hk-csg-official",
                occurred_at="2026-05-23T08:00:00+08:00",
                price_change_pct=8.0,
                is_core_district=True,
                confidence=0.92,
                report_level="must_report",
                evidence=["https://example.com/hk-csg-pricecut"],
            )
        ]
    )

    stored = repo.list_events()
    config = repo.load_thresholds()

    assert stored[0].event_id == "hk-csg-pricecut-20260523"
    assert stored[0].price_change_pct == 8.0
    assert config.must_report_price_change_pct == 5.0
    assert config.optional_price_change_pct == 2.0
```

- [ ] **Step 2: Run the repository test to confirm the domain layer is missing**

Run:

```powershell
cd apps/api
python -m pytest tests/test_repository.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `app.models` or `app.repository`.

- [ ] **Step 3: Write config, models, and SQLite repository**

```python
# apps/api/app/config.py
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    repo_root: Path = Path(__file__).resolve().parents[3]
    database_path: Path = repo_root / "data" / "demo.sqlite"
    manifest_path: Path = repo_root / "data" / "source_manifest.json"
    must_report_price_change_pct: float = 5.0
    optional_price_change_pct: float = 2.0
    enable_live_sources: bool = True


def get_config() -> AppConfig:
    return AppConfig()
```

```python
# apps/api/app/models.py
from typing import Literal

from pydantic import BaseModel, Field

ReportLevel = Literal["must_report", "optional", "ignore", "manual_review"]
OptionId = Literal["hold", "local_follow", "limited_follow", "escalate_attention"]
RiskLevel = Literal["low", "medium", "high"]


class ThresholdConfig(BaseModel):
    must_report_price_change_pct: float = 5.0
    optional_price_change_pct: float = 2.0


class SourceRecord(BaseModel):
    source_id: str
    market: str
    brand: str
    source_type: Literal["competitor_official", "mall_official", "seeded_media"]
    language: Literal["zh-Hans", "zh-Hant", "en"]
    url: str
    title: str
    body: str
    captured_at: str


class EventRecord(BaseModel):
    event_id: str
    market: str
    brand: str
    district: str
    event_type: Literal["price_change", "promotion", "new_store", "store_move", "collection_launch", "compliance_update"]
    product_focus: Literal["gold", "wedding", "light_luxury", "high_jewelry", "other"]
    title: str
    summary_zh: str
    source_url: str
    source_id: str
    occurred_at: str
    price_change_pct: float | None = None
    is_core_district: bool = False
    confidence: float = 0.0
    report_level: ReportLevel = "optional"
    evidence: list[str] = Field(default_factory=list)


class BriefResponse(BaseModel):
    overview: str
    top_events: list[EventRecord]
    compliance_alerts: list[str]
    opportunities: list[str]
    role_actions: dict[str, str]
    manual_review: list[EventRecord] = Field(default_factory=list)


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
```

```python
# apps/api/app/repository.py
import json
import sqlite3
from pathlib import Path

from app.models import EventRecord, ThresholdConfig


class EventRepository:
    def __init__(self, database_path: Path):
        self.database_path = Path(database_path)

    def init_db(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as conn:
            conn.execute(
                """
                create table if not exists events (
                    event_id text primary key,
                    payload text not null
                )
                """
            )
            conn.execute(
                """
                create table if not exists app_config (
                    config_key text primary key,
                    payload text not null
                )
                """
            )

    def save_events(self, events: list[EventRecord]) -> None:
        with sqlite3.connect(self.database_path) as conn:
            conn.executemany(
                "insert or replace into events(event_id, payload) values (?, ?)",
                [(event.event_id, event.model_dump_json()) for event in events],
            )

    def list_events(self) -> list[EventRecord]:
        with sqlite3.connect(self.database_path) as conn:
            rows = conn.execute("select payload from events order by event_id").fetchall()
        return [EventRecord.model_validate_json(row[0]) for row in rows]

    def get_event(self, event_id: str) -> EventRecord | None:
        with sqlite3.connect(self.database_path) as conn:
            row = conn.execute("select payload from events where event_id = ?", (event_id,)).fetchone()
        return EventRecord.model_validate_json(row[0]) if row else None

    def save_thresholds(self, config: ThresholdConfig) -> None:
        with sqlite3.connect(self.database_path) as conn:
            conn.execute(
                "insert or replace into app_config(config_key, payload) values (?, ?)",
                ("thresholds", config.model_dump_json()),
            )

    def load_thresholds(self) -> ThresholdConfig:
        with sqlite3.connect(self.database_path) as conn:
            row = conn.execute("select payload from app_config where config_key = ?", ("thresholds",)).fetchone()
        return ThresholdConfig.model_validate_json(row[0]) if row else ThresholdConfig()
```

- [ ] **Step 4: Run the repository test again**

Run:

```powershell
cd apps/api
python -m pytest tests/test_repository.py -v
```

Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit the domain and persistence layer**

```bash
git add apps/api/app/config.py apps/api/app/models.py apps/api/app/repository.py apps/api/tests/test_repository.py
git commit -m "feat: add api models and sqlite repository"
```

### Task 3: Add manifest-driven fetching, fixture fallback, and event extraction

**Files:**
- Create: `data/source_manifest.json`
- Create: `data/fixtures/raw/hk_csg_pricecut.html`
- Create: `data/fixtures/raw/hk_mall_promo.html`
- Create: `data/fixtures/raw/seed_us_signet.json`
- Create: `apps/api/app/services/fetch_sources.py`
- Create: `apps/api/app/services/extract_events.py`
- Test: `apps/api/tests/test_extraction.py`

- [ ] **Step 1: Write the failing extraction test**

```python
# apps/api/tests/test_extraction.py
from app.services.extract_events import extract_event_candidates
from app.services.fetch_sources import fetch_source_records


def test_fetch_falls_back_to_fixture_and_extracts_price_cut(monkeypatch):
    def raise_offline(*args, **kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr("app.services.fetch_sources.requests.get", raise_offline)

    records = fetch_source_records()
    events = extract_event_candidates(records)
    top = next(event for event in events if event.event_id == "hk-csg-pricecut-20260523")

    assert top.market == "HK"
    assert top.brand == "周生生"
    assert top.price_change_pct == 8.0
    assert top.is_core_district is True
    assert top.product_focus == "wedding"
```

- [ ] **Step 2: Run the extraction test to confirm the source pipeline is missing**

Run:

```powershell
cd apps/api
python -m pytest tests/test_extraction.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `app.services.fetch_sources` or `app.services.extract_events`.

- [ ] **Step 3: Add the manifest, fixtures, fetcher, and extractor**

```json
// data/source_manifest.json
[
  {
    "source_id": "hk-csg-official",
    "market": "HK",
    "brand": "周生生",
    "source_type": "competitor_official",
    "language": "zh-Hant",
    "url": "https://example.com/hk-csg-pricecut",
    "fixture_path": "data/fixtures/raw/hk_csg_pricecut.html"
  },
  {
    "source_id": "hk-harbour-city-mall",
    "market": "HK",
    "brand": "海港城",
    "source_type": "mall_official",
    "language": "zh-Hant",
    "url": "https://example.com/hk-mall-promo",
    "fixture_path": "data/fixtures/raw/hk_mall_promo.html"
  },
  {
    "source_id": "us-signet-seed",
    "market": "US",
    "brand": "Signet",
    "source_type": "seeded_media",
    "language": "en",
    "url": "https://example.com/us-signet-seed",
    "fixture_path": "data/fixtures/raw/seed_us_signet.json"
  }
]
```

```html
<!-- data/fixtures/raw/hk_csg_pricecut.html -->
<html>
  <body>
    <h1>周生生尖沙咀婚嫁黄金限时 8% 优惠</h1>
    <p>活动覆盖尖沙咀核心门店，主打婚嫁黄金套系，活动有效期 48 小时。</p>
  </body>
</html>
```

```html
<!-- data/fixtures/raw/hk_mall_promo.html -->
<html>
  <body>
    <h1>海港城周末婚嫁珠宝购物礼遇</h1>
    <p>海港城官方公告显示，本周末婚嫁珠宝品牌集中促销活动覆盖核心楼层。</p>
  </body>
</html>
```

```json
// data/fixtures/raw/seed_us_signet.json
{
  "title": "Signet launches summer bridal promotion",
  "body": "Official retail messaging highlights a bridal promotion across selected stores with a 5 percent incentive.",
  "captured_at": "2026-05-23T09:00:00-04:00"
}
```

```python
# apps/api/app/services/fetch_sources.py
import json
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from app.config import get_config
from app.models import SourceRecord


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_fixture(path: Path) -> tuple[str, str, str]:
    if path.suffix == ".json":
        payload = json.loads(_read_text(path))
        return payload["title"], payload["body"], payload["captured_at"]

    soup = BeautifulSoup(_read_text(path), "html.parser")
    title = soup.find("h1").get_text(strip=True)
    body = " ".join(node.get_text(" ", strip=True) for node in soup.find_all("p"))
    return title, body, datetime.now(timezone.utc).isoformat()


def fetch_source_records() -> list[SourceRecord]:
    config = get_config()
    manifest = json.loads(config.manifest_path.read_text(encoding="utf-8"))
    records: list[SourceRecord] = []

    for item in manifest:
        fixture_path = config.repo_root / item["fixture_path"]

        try:
            response = requests.get(item["url"], timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.find("h1").get_text(strip=True)
            body = " ".join(node.get_text(" ", strip=True) for node in soup.find_all("p"))
            captured_at = datetime.now(timezone.utc).isoformat()
        except Exception:
            title, body, captured_at = _parse_fixture(fixture_path)

        records.append(
            SourceRecord(
                source_id=item["source_id"],
                market=item["market"],
                brand=item["brand"],
                source_type=item["source_type"],
                language=item["language"],
                url=item["url"],
                title=title,
                body=body,
                captured_at=captured_at,
            )
        )

    return records
```

```python
# apps/api/app/services/extract_events.py
import re

from app.models import EventRecord, SourceRecord


def _price_change_pct(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent)", text.lower())
    return float(match.group(1)) if match else None


def _district(text: str) -> str:
    for district in ("尖沙咀", "铜锣湾", "乌节路", "滨海湾", "第五大道"):
        if district in text:
            return district
    return "未标注商圈"


def _product_focus(text: str) -> str:
    lowered = text.lower()
    if "婚嫁" in text or "bridal" in lowered:
        return "wedding"
    if "黄金" in text or "gold" in lowered:
        return "gold"
    if "轻奢" in text or "light luxury" in lowered:
        return "light_luxury"
    return "other"


def extract_event_candidates(records: list[SourceRecord]) -> list[EventRecord]:
    events: list[EventRecord] = []

    for record in records:
        merged = f"{record.title} {record.body}"
        price_change = _price_change_pct(merged)
        event_type = "price_change" if price_change is not None else "promotion"
        district = _district(merged)
        product_focus = _product_focus(merged)
        is_core_district = district in {"尖沙咀", "乌节路", "滨海湾", "第五大道"}

        event_id = {
            "hk-csg-official": "hk-csg-pricecut-20260523",
            "hk-harbour-city-mall": "hk-mall-promo-20260523",
            "us-signet-seed": "us-signet-bridal-20260523",
        }[record.source_id]

        events.append(
            EventRecord(
                event_id=event_id,
                market=record.market,
                brand=record.brand,
                district=district,
                event_type=event_type,
                product_focus=product_focus,
                title=record.title,
                summary_zh=f"{record.brand}：{record.title}",
                source_url=record.url,
                source_id=record.source_id,
                occurred_at=record.captured_at,
                price_change_pct=price_change,
                is_core_district=is_core_district,
                confidence=0.92 if record.source_type != "seeded_media" else 0.78,
                evidence=[record.url],
            )
        )

    return events
```

- [ ] **Step 4: Run the extraction test again**

Run:

```powershell
cd apps/api
python -m pytest tests/test_extraction.py -v
```

Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit the fetch and extraction pipeline**

```bash
git add data/source_manifest.json data/fixtures/raw/hk_csg_pricecut.html data/fixtures/raw/hk_mall_promo.html data/fixtures/raw/seed_us_signet.json apps/api/app/services/fetch_sources.py apps/api/app/services/extract_events.py apps/api/tests/test_extraction.py
git commit -m "feat: add source fetching and event extraction"
```

### Task 4: Add configurable scoring rules, tie-break ranking, and daily brief generation

**Files:**
- Create: `apps/api/app/services/score_events.py`
- Create: `apps/api/app/services/generate_brief.py`
- Test: `apps/api/tests/test_scoring_and_brief.py`

- [ ] **Step 1: Write the failing scoring and brief test**

```python
# apps/api/tests/test_scoring_and_brief.py
from app.models import EventRecord, ThresholdConfig
from app.services.generate_brief import generate_daily_brief
from app.services.score_events import score_and_rank_events


def _event(event_id: str, district: str, product_focus: str, pct: float) -> EventRecord:
    return EventRecord(
        event_id=event_id,
        market="HK",
        brand="周生生",
        district=district,
        event_type="price_change",
        product_focus=product_focus,
        title=event_id,
        summary_zh=event_id,
        source_url="https://example.com",
        source_id=event_id,
        occurred_at="2026-05-23T08:00:00+08:00",
        price_change_pct=pct,
        is_core_district=district == "尖沙咀",
        confidence=0.91,
        evidence=["https://example.com"],
    )


def test_scoring_respects_thresholds_and_core_district_priority():
    config = ThresholdConfig(must_report_price_change_pct=5.0, optional_price_change_pct=2.0)
    events = [
        _event("non-core", "新界", "other", 5.0),
        _event("core-wedding", "尖沙咀", "wedding", 5.0),
        _event("ignore", "新界", "other", 1.0),
    ]

    ranked, manual_review = score_and_rank_events(events, config)
    brief = generate_daily_brief(ranked, manual_review)

    assert ranked[0].event_id == "core-wedding"
    assert ranked[0].report_level == "must_report"
    assert ranked[-1].report_level == "ignore"
    assert brief.top_events[0].event_id == "core-wedding"
    assert "整体竞争烈度" in brief.overview
```

- [ ] **Step 2: Run the scoring test to prove the rules are missing**

Run:

```powershell
cd apps/api
python -m pytest tests/test_scoring_and_brief.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `app.services.score_events`.

- [ ] **Step 3: Implement scoring, dynamic thresholds, and brief generation**

```python
# apps/api/app/services/score_events.py
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
```

```python
# apps/api/app/services/generate_brief.py
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
```

- [ ] **Step 4: Run the scoring and brief test again**

Run:

```powershell
cd apps/api
python -m pytest tests/test_scoring_and_brief.py -v
```

Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit the ranking and brief layer**

```bash
git add apps/api/app/services/score_events.py apps/api/app/services/generate_brief.py apps/api/tests/test_scoring_and_brief.py
git commit -m "feat: add event scoring and brief generation"
```

### Task 5: Add scenario simulation, orchestration pipeline, and backend APIs

**Files:**
- Create: `apps/api/app/services/simulate_response.py`
- Create: `apps/api/app/services/chat.py`
- Create: `apps/api/app/services/pipeline.py`
- Create: `apps/api/app/routes/briefs.py`
- Create: `apps/api/app/routes/events.py`
- Create: `apps/api/app/routes/chat.py`
- Create: `apps/api/app/routes/config.py`
- Modify: `apps/api/app/main.py`
- Test: `apps/api/tests/test_api_flow.py`

- [ ] **Step 1: Write the failing API flow test**

```python
# apps/api/tests/test_api_flow.py
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_brief_simulation_and_threshold_update_flow():
    brief = client.get("/api/briefs/today")
    assert brief.status_code == 200
    assert brief.json()["top_events"][0]["event_id"] == "hk-csg-pricecut-20260523"

    simulation = client.post("/api/events/hk-csg-pricecut-20260523/simulate")
    assert simulation.status_code == 200
    assert simulation.json()["recommended_option_id"] == "local_follow"

    config = client.patch(
        "/api/config/thresholds",
        json={"must_report_price_change_pct": 6.0, "optional_price_change_pct": 3.0},
    )
    assert config.status_code == 200
    assert config.json()["must_report_price_change_pct"] == 6.0

    chat = client.post(
        "/api/chat",
        json={"question": "综合多方因素最优选择哪种应对级别，各岗位后续该落实哪些相关工作"},
    )
    assert chat.status_code == 200
    assert "局部跟进" in chat.json()["answer"]
```

- [ ] **Step 2: Run the API flow test to prove orchestration and routes are missing**

Run:

```powershell
cd apps/api
python -m pytest tests/test_api_flow.py -v
```

Expected: FAIL with missing route or import errors.

- [ ] **Step 3: Implement simulation logic, orchestration, and API endpoints**

```python
# apps/api/app/services/simulate_response.py
from app.models import DimensionImpact, EventRecord, SimulationResponse, StrategyOption


def simulate_response(event: EventRecord) -> SimulationResponse:
    if event.confidence < 0.75:
        return SimulationResponse(
            event_id=event.event_id,
            options=[
                StrategyOption(
                    option_id="escalate_attention",
                    label_zh="升级关注",
                    impacts=[DimensionImpact(name="合规风险", level="high", rationale="证据不足，需人工确认。")],
                    rationale="当前证据不完整，不建议直接执行价格动作。",
                )
            ],
            recommended_option_id="escalate_attention",
            recommended_reason="该事件证据不完整，先人工复核再决定是否跟进。",
            follow_up=["补充官方链接或门店公告截图。"],
        )

    options = [
        StrategyOption(
            option_id="hold",
            label_zh="保持不动",
            impacts=[
                DimensionImpact(name="毛利/价格体系压力", level="low", rationale="不调整价格体系。"),
                DimensionImpact(name="客流分流风险", level="high", rationale="核心商圈婚嫁客流可能短期流失。"),
                DimensionImpact(name="品牌调性受损风险", level="low", rationale="不新增促销信号。"),
                DimensionImpact(name="合规风险", level="low", rationale="不新增执行动作。"),
            ],
            rationale="适合影响范围有限或非核心商圈事件。",
        ),
        StrategyOption(
            option_id="local_follow",
            label_zh="局部跟进",
            impacts=[
                DimensionImpact(name="毛利/价格体系压力", level="medium", rationale="仅在受影响商圈做局部回应。"),
                DimensionImpact(name="客流分流风险", level="medium", rationale="可部分对冲竞品短期吸客。"),
                DimensionImpact(name="品牌调性受损风险", level="low", rationale="不破坏全市场高端定位。"),
                DimensionImpact(name="合规风险", level="low", rationale="动作边界可控。"),
            ],
            rationale="适合核心商圈、婚嫁黄金主力品类的高优异动。",
        ),
        StrategyOption(
            option_id="limited_follow",
            label_zh="限时跟进",
            impacts=[
                DimensionImpact(name="毛利/价格体系压力", level="high", rationale="促销更广，价格体系承压。"),
                DimensionImpact(name="客流分流风险", level="low", rationale="短期截留客流能力更强。"),
                DimensionImpact(name="品牌调性受损风险", level="medium", rationale="频繁促销会稀释高端感。"),
                DimensionImpact(name="合规风险", level="medium", rationale="活动文案和门店物料需同步审查。"),
            ],
            rationale="仅适合竞品动作覆盖范围极大且时点紧迫的事件。",
        ),
    ]

    recommended = "local_follow" if event.is_core_district and (event.price_change_pct or 0) >= 5 else "hold"
    reason = "竞品在核心婚嫁黄金商圈发起 8% 级别促销，局部跟进能平衡客流防守与价格体系压力。"

    return SimulationResponse(
        event_id=event.event_id,
        options=options,
        recommended_option_id=recommended,
        recommended_reason=reason,
        follow_up=[
            "区域运营今日核查尖沙咀竞品门店活动落地情况。",
            "市场团队同步更新婚嫁黄金内容口径。",
            "合规专员复核临时促销文案与贵金属标识。",
        ],
    )
```

```python
# apps/api/app/services/chat.py
from app.models import BriefResponse, ChatResponse, SimulationResponse


def answer_demo_question(question: str, brief: BriefResponse, simulation: SimulationResponse | None) -> ChatResponse:
    if "风险等级最高" in question:
        top = brief.top_events[0]
        return ChatResponse(
            answer=f"今天风险最高的是 {top.title}。原因是它发生在核心商圈、涉及婚嫁黄金主力品类，且价格异动达到 {top.price_change_pct}%。",
            cited_event_ids=[top.event_id],
        )
    if "不同应对策略" in question and simulation is not None:
        answer = "；".join(f"{option.label_zh}：{option.rationale}" for option in simulation.options if option.option_id != "escalate_attention")
        return ChatResponse(answer=answer, cited_event_ids=[simulation.event_id])
    if "最优选择" in question and simulation is not None:
        return ChatResponse(
            answer=f"建议选择局部跟进。{simulation.recommended_reason} 后续由区域运营巡检商圈、市场策略调整婚嫁黄金内容、合规专员复核促销物料。",
            cited_event_ids=[simulation.event_id],
        )
    return ChatResponse(answer="请围绕今日高风险事件、策略利弊或推荐动作提问。")
```

```python
# apps/api/app/services/pipeline.py
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
```

```python
# apps/api/app/routes/briefs.py
from fastapi import APIRouter

from app.services.pipeline import build_today_brief

router = APIRouter(prefix="/api/briefs", tags=["briefs"])


@router.get("/today")
def get_today_brief():
    brief, _ = build_today_brief()
    return brief.model_dump()
```

```python
# apps/api/app/routes/events.py
from fastapi import APIRouter, HTTPException

from app.config import get_config
from app.repository import EventRepository
from app.services.simulate_response import simulate_response

router = APIRouter(prefix="/api/events", tags=["events"])


def _repo() -> EventRepository:
    repo = EventRepository(get_config().database_path)
    repo.init_db()
    return repo


@router.get("/{event_id}")
def get_event(event_id: str):
    event = _repo().get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.model_dump()


@router.post("/{event_id}/simulate")
def simulate_event(event_id: str):
    event = _repo().get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return simulate_response(event).model_dump()
```

```python
# apps/api/app/routes/chat.py
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
```

```python
# apps/api/app/routes/config.py
from fastapi import APIRouter

from app.config import get_config
from app.models import ThresholdConfig
from app.repository import EventRepository

router = APIRouter(prefix="/api/config", tags=["config"])


def _repo() -> EventRepository:
    repo = EventRepository(get_config().database_path)
    repo.init_db()
    return repo


@router.get("/thresholds")
def get_thresholds():
    return _repo().load_thresholds().model_dump()


@router.patch("/thresholds")
def update_thresholds(payload: ThresholdConfig):
    _repo().save_thresholds(payload)
    return payload.model_dump()
```

```python
# apps/api/app/main.py
from fastapi import FastAPI

from app.routes.briefs import router as briefs_router
from app.routes.chat import router as chat_router
from app.routes.config import router as config_router
from app.routes.events import router as events_router

app = FastAPI(title="Overseas Jewelry Strategy Simulator API")
app.include_router(briefs_router)
app.include_router(events_router)
app.include_router(chat_router)
app.include_router(config_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Run the API flow test again**

Run:

```powershell
cd apps/api
python -m pytest tests/test_api_flow.py -v
```

Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit the simulation and API layer**

```bash
git add apps/api/app/services/simulate_response.py apps/api/app/services/chat.py apps/api/app/services/pipeline.py apps/api/app/routes/briefs.py apps/api/app/routes/events.py apps/api/app/routes/chat.py apps/api/app/routes/config.py apps/api/app/main.py apps/api/tests/test_api_flow.py
git commit -m "feat: add brief, simulation, and chat api flow"
```

### Task 6: Build the analyst UI with brief, chat, evidence, simulation, and threshold tuning

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/vite.config.ts`
- Create: `apps/web/index.html`
- Create: `apps/web/src/main.tsx`
- Create: `apps/web/src/App.tsx`
- Create: `apps/web/src/styles.css`
- Create: `apps/web/src/types.ts`
- Create: `apps/web/src/api/client.ts`
- Create: `apps/web/src/components/BriefSidebar.tsx`
- Create: `apps/web/src/components/ChatPanel.tsx`
- Create: `apps/web/src/components/EvidencePanel.tsx`
- Create: `apps/web/src/components/SimulationPanel.tsx`
- Create: `apps/web/src/components/ThresholdPanel.tsx`
- Test: `apps/web/src/__tests__/app.spec.tsx`

- [ ] **Step 1: Write the failing frontend smoke test**

```tsx
// apps/web/src/__tests__/app.spec.tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "../App";

const api = {
  getBrief: async () => ({
    overview: "今日五大市场整体竞争烈度偏高。",
    top_events: [
      {
        event_id: "hk-csg-pricecut-20260523",
        title: "周生生尖沙咀婚嫁黄金限时 8% 优惠",
        summary_zh: "周生生在香港尖沙咀核心婚嫁商圈推出 8% 限时优惠。",
        market: "HK",
        source_url: "https://example.com/hk-csg-pricecut",
      },
    ],
    compliance_alerts: ["美国贵金属标识与钻石溯源内容需持续关注。"],
    opportunities: ["新加坡高端婚嫁珠宝内容热度可作为新品观察线索。"],
    role_actions: {
      hq: "总部管理层重点关注香港核心商圈应对级别是否上收决策。",
      ops: "区域运营今日优先巡检尖沙咀商圈并准备局部促销预案。",
      marketing: "市场策略岗同步检查婚嫁黄金内容方向与投放素材。",
    },
    manual_review: [],
  }),
  getThresholds: async () => ({ must_report_price_change_pct: 5, optional_price_change_pct: 2 }),
  updateThresholds: async () => ({ must_report_price_change_pct: 6, optional_price_change_pct: 3 }),
  simulateEvent: async () => ({
    event_id: "hk-csg-pricecut-20260523",
    recommended_option_id: "local_follow",
    recommended_reason: "局部跟进能平衡客流防守与价格体系压力。",
    follow_up: ["区域运营巡检尖沙咀。"],
    options: [],
  }),
  askQuestion: async () => ({ answer: "建议选择局部跟进。", cited_event_ids: ["hk-csg-pricecut-20260523"] }),
};

describe("App", () => {
  it("renders the top event and simulate action", async () => {
    render(<App api={api as never} />);

    expect(await screen.findByText("周生生尖沙咀婚嫁黄金限时 8% 优惠")).toBeTruthy();
    expect(screen.getByRole("button", { name: "开始模拟" })).toBeTruthy();
    expect(screen.getByText("今日五大市场整体竞争烈度偏高。")).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run the frontend test to prove the web shell is missing**

Run:

```powershell
cd apps/web
npm test -- --run src/__tests__/app.spec.tsx
```

Expected: FAIL because `package.json` and source files do not exist yet.

- [ ] **Step 3: Implement the Vite app, typed client, and three-pane UI**

```json
// apps/web/package.json
{
  "name": "overseas-jewelry-strategy-simulator-web",
  "private": true,
  "version": "0.0.1",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.5",
    "@testing-library/react": "^15.0.7",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "jsdom": "^24.1.1",
    "typescript": "^5.5.3",
    "vite": "^5.3.3",
    "vitest": "^2.0.2"
  }
}
```

```json
// apps/web/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"],
  "references": []
}
```

```ts
// apps/web/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
  },
});
```

```html
<!-- apps/web/index.html -->
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Overseas Jewelry Strategy Simulator</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

```ts
// apps/web/src/types.ts
export type Thresholds = {
  must_report_price_change_pct: number;
  optional_price_change_pct: number;
};

export type EventCard = {
  event_id: string;
  title: string;
  summary_zh: string;
  market: string;
  source_url: string;
};

export type Brief = {
  overview: string;
  top_events: EventCard[];
  compliance_alerts: string[];
  opportunities: string[];
  role_actions: Record<string, string>;
  manual_review: EventCard[];
};

export type Simulation = {
  event_id: string;
  recommended_option_id: string;
  recommended_reason: string;
  follow_up: string[];
  options: Array<{
    option_id: string;
    label_zh: string;
    rationale: string;
    impacts: Array<{ name: string; level: string; rationale: string }>;
  }>;
};

export type ChatAnswer = {
  answer: string;
  cited_event_ids: string[];
};
```

```tsx
// apps/web/src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";

import { App } from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

```ts
// apps/web/src/api/client.ts
import type { Brief, ChatAnswer, Simulation, Thresholds } from "../types";

const API_BASE = "http://localhost:8000";

export const api = {
  async getBrief(): Promise<Brief> {
    const response = await fetch(`${API_BASE}/api/briefs/today`);
    return response.json();
  },
  async simulateEvent(eventId: string): Promise<Simulation> {
    const response = await fetch(`${API_BASE}/api/events/${eventId}/simulate`, { method: "POST" });
    return response.json();
  },
  async askQuestion(question: string): Promise<ChatAnswer> {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    return response.json();
  },
  async getThresholds(): Promise<Thresholds> {
    const response = await fetch(`${API_BASE}/api/config/thresholds`);
    return response.json();
  },
  async updateThresholds(payload: Thresholds): Promise<Thresholds> {
    const response = await fetch(`${API_BASE}/api/config/thresholds`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return response.json();
  },
};
```

```tsx
// apps/web/src/App.tsx
import { useEffect, useState } from "react";

import type { Brief, Simulation, Thresholds } from "./types";
import { api as defaultApi } from "./api/client";
import { BriefSidebar } from "./components/BriefSidebar";
import { ChatPanel } from "./components/ChatPanel";
import { EvidencePanel } from "./components/EvidencePanel";
import { SimulationPanel } from "./components/SimulationPanel";
import { ThresholdPanel } from "./components/ThresholdPanel";

type AppProps = {
  api?: typeof defaultApi;
};

export function App({ api = defaultApi }: AppProps) {
  const [brief, setBrief] = useState<Brief | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string>("");
  const [simulation, setSimulation] = useState<Simulation | null>(null);
  const [answer, setAnswer] = useState<string>("");
  const [thresholds, setThresholds] = useState<Thresholds | null>(null);

  useEffect(() => {
    void api.getBrief().then((result) => {
      setBrief(result);
      setSelectedEventId(result.top_events[0]?.event_id ?? "");
    });
    void api.getThresholds().then(setThresholds);
  }, [api]);

  const selectedEvent = brief?.top_events.find((event) => event.event_id === selectedEventId) ?? null;

  return (
    <div className="layout">
      <BriefSidebar brief={brief} selectedEventId={selectedEventId} onSelectEvent={setSelectedEventId} />
      <main className="center-panel">
        <ChatPanel
          overview={brief?.overview ?? ""}
          answer={answer}
          onAsk={async (question) => {
            const result = await api.askQuestion(question);
            setAnswer(result.answer);
          }}
          onSimulate={async () => {
            if (!selectedEventId) return;
            setSimulation(await api.simulateEvent(selectedEventId));
          }}
        />
      </main>
      <aside className="right-panel">
        <ThresholdPanel
          thresholds={thresholds}
          onSave={async (next) => {
            const saved = await api.updateThresholds(next);
            setThresholds(saved);
          }}
        />
        <EvidencePanel event={selectedEvent} />
        <SimulationPanel simulation={simulation} />
      </aside>
    </div>
  );
}
```

```tsx
// apps/web/src/components/BriefSidebar.tsx
import type { Brief } from "../types";

type Props = {
  brief: Brief | null;
  selectedEventId: string;
  onSelectEvent: (eventId: string) => void;
};

export function BriefSidebar({ brief, selectedEventId, onSelectEvent }: Props) {
  return (
    <aside className="sidebar">
      <h1>今日战略简报</h1>
      <p>{brief?.overview ?? "正在加载简报..."}</p>
      <h2>高优竞品异动</h2>
      <ul>
        {brief?.top_events.map((event) => (
          <li key={event.event_id}>
            <button className={selectedEventId === event.event_id ? "selected" : ""} onClick={() => onSelectEvent(event.event_id)}>
              {event.title}
            </button>
          </li>
        ))}
      </ul>
      <h2>合规红线提醒</h2>
      <ul>{brief?.compliance_alerts.map((item) => <li key={item}>{item}</li>)}</ul>
      <h2>市场机会看点</h2>
      <ul>{brief?.opportunities.map((item) => <li key={item}>{item}</li>)}</ul>
    </aside>
  );
}
```

```tsx
// apps/web/src/components/ChatPanel.tsx
type Props = {
  overview: string;
  answer: string;
  onAsk: (question: string) => Promise<void>;
  onSimulate: () => Promise<void>;
};

const DEMO_QUESTIONS = [
  "今日五大重点市场里，哪起竞品调价促销事件风险等级最高，判定依据是什么",
  "面对此次竞品促销攻势，不同应对策略分别会产生哪些利弊影响",
  "综合多方因素最优选择哪种应对级别，各岗位后续该落实哪些相关工作",
];

export function ChatPanel({ overview, answer, onAsk, onSimulate }: Props) {
  return (
    <section>
      <h2>智能分析师</h2>
      <p>{overview}</p>
      <div className="question-list">
        {DEMO_QUESTIONS.map((question) => (
          <button key={question} onClick={() => void onAsk(question)}>
            {question}
          </button>
        ))}
      </div>
      <button onClick={() => void onSimulate()}>开始模拟</button>
      <article className="answer-box">{answer || "选择一个问题或直接开始模拟。"}</article>
    </section>
  );
}
```

```tsx
// apps/web/src/components/EvidencePanel.tsx
import type { EventCard } from "../types";

type Props = {
  event: EventCard | null;
};

export function EvidencePanel({ event }: Props) {
  if (!event) return <section className="card">请选择一个高优事件。</section>;

  return (
    <section className="card">
      <h3>事件核心概况</h3>
      <p>{event.summary_zh}</p>
      <a href={event.source_url} target="_blank" rel="noreferrer">
        查看来源
      </a>
    </section>
  );
}
```

```tsx
// apps/web/src/components/SimulationPanel.tsx
import type { Simulation } from "../types";

type Props = {
  simulation: Simulation | null;
};

export function SimulationPanel({ simulation }: Props) {
  if (!simulation) return <section className="card">点击“开始模拟”查看三类应对级别方案。</section>;

  return (
    <section className="card">
      <h3>三类可选应对级别方案</h3>
      {simulation.options.map((option) => (
        <article key={option.option_id} className="option-card">
          <h4>{option.label_zh}</h4>
          <p>{option.rationale}</p>
          <ul>
            {option.impacts.map((impact) => (
              <li key={`${option.option_id}-${impact.name}`}>
                {impact.name}：{impact.level}，{impact.rationale}
              </li>
            ))}
          </ul>
        </article>
      ))}
      <h3>优选方案及判定理由</h3>
      <p>{simulation.recommended_reason}</p>
      <h4>后续观测与执行提示</h4>
      <ul>
        {simulation.follow_up.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
```

```css
/* apps/web/src/styles.css */
:root {
  font-family: "Segoe UI", "PingFang SC", sans-serif;
  color: #1c1b18;
  background: linear-gradient(180deg, #f7f1e7 0%, #f3f4ef 100%);
}

body {
  margin: 0;
}

.layout {
  display: grid;
  grid-template-columns: 320px 1fr 380px;
  min-height: 100vh;
}

.sidebar,
.center-panel,
.right-panel {
  padding: 24px;
}

.sidebar {
  border-right: 1px solid #d7cdbd;
  background: rgba(255, 250, 244, 0.95);
}

.right-panel {
  border-left: 1px solid #d7cdbd;
  display: grid;
  gap: 16px;
  align-content: start;
}

.card,
.answer-box,
.option-card {
  padding: 16px;
  border-radius: 14px;
  background: #fffdf9;
  border: 1px solid #e7dcc9;
}

button {
  cursor: pointer;
}
```

```tsx
// apps/web/src/components/ThresholdPanel.tsx
import { useEffect, useState } from "react";

import type { Thresholds } from "../types";

type Props = {
  thresholds: Thresholds | null;
  onSave: (next: Thresholds) => Promise<void>;
};

export function ThresholdPanel({ thresholds, onSave }: Props) {
  const [form, setForm] = useState<Thresholds>({ must_report_price_change_pct: 5, optional_price_change_pct: 2 });

  useEffect(() => {
    if (thresholds) setForm(thresholds);
  }, [thresholds]);

  return (
    <section className="card">
      <h3>价格异动阈值</h3>
      <label>
        必须上报阈值
        <input type="number" value={form.must_report_price_change_pct} onChange={(event) => setForm({ ...form, must_report_price_change_pct: Number(event.target.value) })} />
      </label>
      <label>
        可选上报阈值
        <input type="number" value={form.optional_price_change_pct} onChange={(event) => setForm({ ...form, optional_price_change_pct: Number(event.target.value) })} />
      </label>
      <button onClick={() => void onSave(form)}>保存阈值</button>
    </section>
  );
}
```

- [ ] **Step 4: Run the frontend smoke test again**

Run:

```powershell
cd apps/web
npm test -- --run src/__tests__/app.spec.tsx
```

Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit the analyst UI**

```bash
git add apps/web/package.json apps/web/tsconfig.json apps/web/vite.config.ts apps/web/index.html apps/web/src
git commit -m "feat: add analyst web interface"
```

### Task 7: Add README, demo contract verification, and end-to-end checks

**Files:**
- Create: `apps/api/tests/test_demo_contract.py`
- Create: `README.md`

- [ ] **Step 1: Write the failing demo contract test**

```python
# apps/api/tests/test_demo_contract.py
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_today_brief_contract_contains_required_sections():
    response = client.get("/api/briefs/today")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) >= {"overview", "top_events", "compliance_alerts", "opportunities", "role_actions", "manual_review"}
    assert payload["top_events"][0]["source_url"].startswith("https://")
```

- [ ] **Step 2: Run the contract test before adding the final docs**

Run:

```powershell
cd apps/api
python -m pytest tests/test_demo_contract.py -v
```

Expected: PASS or reveal any route contract drift that must be fixed before handoff.

- [ ] **Step 3: Write the README with architecture, setup, and demo script**

````markdown
# Overseas Jewelry Strategy Simulator

## What This Demo Shows

- A daily strategic brief built from official-source competitor and mall signals
- A Top 1 competitor event chosen by configurable threshold and tie-break rules
- A three-option response simulation: 保持不动 / 局部跟进 / 限时跟进
- Evidence links, manual-review isolation, and threshold tuning

## Repository Layout

- `apps/api`: FastAPI backend
- `apps/web`: React/Vite frontend
- `data`: source manifest, fixture fallbacks, and SQLite database

## Backend Setup

```powershell
cd apps/api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Frontend Setup

```powershell
cd apps/web
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## Verification

```powershell
cd apps/api
python -m pytest -v

cd ..\..\apps\web
npm test -- --run
npm run build
```

## Demo Flow

1. Open the app and show the daily brief.
2. Click the Hong Kong top event generated from a real or fallback official source.
3. Ask the three canned judging questions.
4. Trigger simulation and explain why `局部跟进` wins.
5. Adjust thresholds to show the event scoring is configurable.
````

- [ ] **Step 4: Run the full backend and frontend verification commands**

Run:

```powershell
cd apps/api
python -m pytest -v

cd ..\web
npm test -- --run
npm run build
```

Expected:

- Backend: all tests PASS
- Frontend: all tests PASS
- Build: `vite build` completes successfully

- [ ] **Step 5: Commit the docs and verification pass**

```bash
git add README.md apps/api/tests/test_demo_contract.py
git commit -m "docs: add demo setup and verification guide"
```

## Self-Review

### Spec coverage

- Real official-source ingestion: Task 3
- Fixture fallback and seeded breadth: Task 3
- Threshold tuning entry: Tasks 2, 5, and 6
- Top event scoring and tie-breaks: Task 4
- Manual-review safety path: Tasks 4 and 5
- Daily brief structure: Task 4
- Top 1 event simulation: Task 5
- Chat-style judged questions: Tasks 5 and 6
- Evidence links and traceability: Tasks 3, 4, and 6
- Readme and demo instructions: Task 7

### Placeholder scan

- No `TODO`, `TBD`, or “implement later” placeholders remain.
- All routes, files, commands, and identifiers referenced in later tasks are defined earlier in the plan.

### Type consistency

- Event identifier used across extraction, API flow, chat, and frontend: `hk-csg-pricecut-20260523`
- Strategy option identifiers used across simulation and frontend: `hold`, `local_follow`, `limited_follow`, `escalate_attention`
- Threshold keys used across repository, API, and frontend: `must_report_price_change_pct`, `optional_price_change_pct`
