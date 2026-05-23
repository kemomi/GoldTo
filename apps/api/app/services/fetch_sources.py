import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from app.config import get_config
from app.models import SourceRecord


logger = logging.getLogger(__name__)
LIVE_SOURCE_TIMEOUT_SECONDS = 2


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_html(text: str) -> tuple[str, str]:
    soup = BeautifulSoup(text, "html.parser")
    title_node = soup.find("h1")
    if title_node is None:
        raise ValueError("missing h1 title")
    title = title_node.get_text(strip=True)
    body = " ".join(node.get_text(" ", strip=True) for node in soup.find_all("p"))
    return title, body


def _parse_fixture(path: Path, fallback_captured_at: str | None) -> tuple[str, str, str]:
    if path.suffix == ".json":
        payload = json.loads(_read_text(path))
        return payload["title"], payload["body"], payload["captured_at"]

    title, body = _parse_html(_read_text(path))
    if fallback_captured_at is None:
        raise ValueError(f"missing fallback captured_at for fixture {path}")
    return title, body, fallback_captured_at


def fetch_source_records() -> list[SourceRecord]:
    config = get_config()
    manifest = json.loads(config.manifest_path.read_text(encoding="utf-8"))
    records: list[SourceRecord] = []

    for item in manifest:
        fixture_path = config.repo_root / item["fixture_path"]
        fallback_captured_at = item.get("captured_at")

        try:
            response = requests.get(item["url"], timeout=LIVE_SOURCE_TIMEOUT_SECONDS)
            response.raise_for_status()
            title, body = _parse_html(response.text)
            captured_at = datetime.now(timezone.utc).isoformat()
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            logger.warning(
                "fixture fallback for %s (%s): %s",
                item["source_id"],
                item["url"],
                exc,
            )
            title, body, captured_at = _parse_fixture(fixture_path, fallback_captured_at)

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
