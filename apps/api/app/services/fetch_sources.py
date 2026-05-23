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
