from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import FeedbackItem, Ticket


class SQLiteStorage:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    source_id TEXT PRIMARY KEY,
                    source_type TEXT,
                    text TEXT,
                    platform TEXT,
                    rating INTEGER,
                    user TEXT,
                    date TEXT,
                    app_version TEXT,
                    priority_hint TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id TEXT PRIMARY KEY,
                    source_id TEXT,
                    source_type TEXT,
                    category TEXT,
                    priority TEXT,
                    title TEXT,
                    description TEXT,
                    technical_details TEXT,
                    user_impact TEXT,
                    confidence REAL,
                    status TEXT,
                    quality_score REAL,
                    quality_notes TEXT
                )
                """
            )

    def save_feedback(self, item: FeedbackItem) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO feedback VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.source_id,
                    item.source_type,
                    item.text,
                    item.platform,
                    item.rating,
                    item.user,
                    item.date,
                    item.app_version,
                    item.priority_hint,
                ),
            )

    def save_ticket(self, ticket: Ticket) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(ticket.to_dict().values()),
            )
