from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .config import PipelineConfig
from .models import Classification, FeedbackItem, Ticket

try:
    from autogen_agentchat.agents import AssistantAgent
except Exception:  # pragma: no cover
    AssistantAgent = None


@dataclass
class AgentProfile:
    name: str
    responsibility: str


class BaseWorkflowAgent:
    def __init__(self, name: str, responsibility: str):
        self.profile = AgentProfile(name=name, responsibility=responsibility)
        self.autogen_agent_class = AssistantAgent


class CSVReaderAgent(BaseWorkflowAgent):
    def __init__(self):
        super().__init__("CSV Reader Agent", "Reads and parses app reviews and support emails.")

    def read(self, data_dir: Path) -> list[FeedbackItem]:
        reviews = pd.read_csv(data_dir / "app_store_reviews.csv")
        emails = pd.read_csv(data_dir / "support_emails.csv")
        items: list[FeedbackItem] = []

        for row in reviews.to_dict("records"):
            items.append(
                FeedbackItem(
                    source_id=row["review_id"],
                    source_type="app_store_review",
                    text=row["review_text"],
                    platform=row["platform"],
                    rating=int(row["rating"]),
                    user=row["user_name"],
                    date=row["date"],
                    app_version=row["app_version"],
                )
            )

        for row in emails.fillna("").to_dict("records"):
            text = f"{row['subject']}. {row['body']}"
            items.append(
                FeedbackItem(
                    source_id=row["email_id"],
                    source_type="support_email",
                    text=text,
                    user=row["sender_email"],
                    date=row["timestamp"],
                    priority_hint=row["priority"],
                )
            )
        return items


class FeedbackClassifierAgent(BaseWorkflowAgent):
    def __init__(self, config: PipelineConfig):
        super().__init__("Classifier Agent", "Categorizes feedback and assigns confidence and priority.")
        self.config = config

    def classify(self, item: FeedbackItem) -> Classification:
        text = item.text.lower()
        scores = {
            "Spam": self._score(text, ["buy cheap", "earn money", "promo", "clicking this link", "followers"]),
            "Bug": self._score(text, ["crash", "can't login", "cannot login", "invalid token", "not working", "data loss", "disappear", "freeze", "loop"]),
            "Feature Request": self._score(text, ["please add", "would love", "feature request", "suggestion", "could you add", "missing", "export"]),
            "Praise": self._score(text, ["amazing", "love", "great", "perfectly", "thank you", "helped"]),
            "Complaint": self._score(text, ["too expensive", "slow", "poor", "limited", "takes too long"]),
        }

        if item.rating is not None and item.rating <= 2:
            scores["Bug"] += 0.12
            scores["Complaint"] += 0.08
        if item.rating is not None and item.rating >= 4:
            scores["Praise"] += 0.10

        category = max(scores, key=scores.get)
        confidence = min(round(scores[category], 2), 0.98)
        if confidence < 0.25:
            category = "Complaint"
            confidence = 0.35

        priority = self._priority(text, category, item.priority_hint)
        rationale = f"Matched {category.lower()} language with confidence {confidence}."
        return Classification(category=category, confidence=confidence, priority=priority, rationale=rationale)

    @staticmethod
    def _score(text: str, keywords: list[str]) -> float:
        score = 0.05
        for keyword in keywords:
            if keyword in text:
                score += 0.24
        return score

    def _priority(self, text: str, category: str, priority_hint: str) -> str:
        hint = priority_hint.strip().title()
        if hint in {"Critical", "High", "Medium", "Low"}:
            return hint
        if category == "Spam" or category == "Praise":
            return "Low"
        if any(keyword in text for keyword in self.config.critical_keywords):
            return "Critical" if "data loss" in text or "disappear" in text else "High"
        if any(keyword in text for keyword in self.config.high_keywords):
            return "High"
        return "Medium"


class BugAnalysisAgent(BaseWorkflowAgent):
    def __init__(self):
        super().__init__("Bug Analyzer Agent", "Extracts reproduction steps, technical details, platform, and severity.")

    def analyze(self, item: FeedbackItem) -> dict:
        text = item.text
        device = self._find_device(text)
        steps = self._find_steps(text)
        details = [part for part in [device, steps, item.platform, item.app_version] if part]
        return {
            "technical_details": "; ".join(details) or "Technical details not provided by user.",
            "user_impact": "User is blocked or experiencing product reliability problems.",
        }

    @staticmethod
    def _find_device(text: str) -> str:
        match = re.search(r"(Pixel \d+|Samsung S\d+|iPhone \d+|Android \d+|iOS [\d.]+)", text, re.I)
        return match.group(0) if match else ""

    @staticmethod
    def _find_steps(text: str) -> str:
        match = re.search(r"Steps?:\s*(.*)", text, re.I)
        return f"Steps: {match.group(1)}" if match else ""


class FeatureExtractorAgent(BaseWorkflowAgent):
    def __init__(self):
        super().__init__("Feature Extractor Agent", "Identifies feature requests and estimates user impact.")

    def extract(self, item: FeedbackItem) -> dict:
        return {
            "technical_details": "Requested capability should be validated against roadmap and product documentation.",
            "user_impact": "Improves productivity workflow and user satisfaction for affected users.",
        }


class TicketCreatorAgent(BaseWorkflowAgent):
    def __init__(self):
        super().__init__("Ticket Creator Agent", "Generates structured tickets and metadata.")

    def create(self, item: FeedbackItem, classification: Classification, analysis: dict, sequence: int) -> Ticket:
        title = self._title(item.text, classification.category)
        description = f"Source {item.source_id} ({item.source_type}) says: {item.text}"
        return Ticket(
            ticket_id=f"TKT-{sequence:04d}",
            source_id=item.source_id,
            source_type=item.source_type,
            category=classification.category,
            priority=classification.priority,
            title=title,
            description=description,
            technical_details=analysis.get("technical_details", "No technical details required."),
            user_impact=analysis.get("user_impact", "General feedback captured for product review."),
            confidence=classification.confidence,
            status="Pending Review",
            quality_score=0.0,
            quality_notes="Not reviewed yet.",
        )

    @staticmethod
    def _title(text: str, category: str) -> str:
        clean = re.sub(r"\s+", " ", text).strip()
        clean = clean[:75].rstrip(".")
        return f"{category}: {clean}"


class QualityCriticAgent(BaseWorkflowAgent):
    def __init__(self):
        super().__init__("Quality Critic Agent", "Reviews generated tickets for completeness and consistency.")

    def review(self, ticket: Ticket) -> Ticket:
        score = 1.0
        notes = []
        if len(ticket.title) < 12:
            score -= 0.25
            notes.append("Title is too short.")
        if ticket.category in {"Bug", "Feature Request"} and "not provided" in ticket.technical_details.lower():
            score -= 0.20
            notes.append("Needs more technical or product details.")
        if ticket.priority not in {"Critical", "High", "Medium", "Low"}:
            score -= 0.25
            notes.append("Invalid priority.")
        ticket.quality_score = round(max(score, 0.0), 2)
        ticket.quality_notes = "Approved." if not notes else " ".join(notes)
        ticket.status = "Approved" if ticket.quality_score >= 0.75 else "Needs Manual Review"
        return ticket
