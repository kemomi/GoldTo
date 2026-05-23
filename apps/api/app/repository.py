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
