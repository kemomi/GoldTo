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
