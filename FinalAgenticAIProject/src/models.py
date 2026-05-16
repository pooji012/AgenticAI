from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class FeedbackItem:
    source_id: str
    source_type: str
    text: str
    platform: str = ""
    rating: int | None = None
    user: str = ""
    date: str = ""
    app_version: str = ""
    priority_hint: str = ""


@dataclass
class Classification:
    category: str
    confidence: float
    priority: str
    rationale: str


@dataclass
class Ticket:
    ticket_id: str
    source_id: str
    source_type: str
    category: str
    priority: str
    title: str
    description: str
    technical_details: str
    user_impact: str
    confidence: float
    status: str
    quality_score: float
    quality_notes: str

    def to_dict(self) -> dict:
        return asdict(self)
