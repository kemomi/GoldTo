import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(slots=True)
class AppConfig:
    repo_root: Path = DEFAULT_REPO_ROOT
    database_path: Path | None = None
    manifest_path: Path | None = None
    must_report_price_change_pct: float = 5.0
    optional_price_change_pct: float = 2.0
    enable_live_sources: bool = True

    def __post_init__(self) -> None:
        if self.database_path is None:
            override = os.environ.get("APP_DATABASE_PATH")
            use_override = override and self.repo_root == DEFAULT_REPO_ROOT
            self.database_path = Path(override) if use_override else self.repo_root / "data" / "demo.sqlite"
        if self.manifest_path is None:
            self.manifest_path = self.repo_root / "data" / "source_manifest.json"


def get_config() -> AppConfig:
    return AppConfig()
