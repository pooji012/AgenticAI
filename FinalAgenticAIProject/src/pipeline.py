from __future__ import annotations

from datetime import datetime

import pandas as pd

from .agents import (
    BugAnalysisAgent,
    CSVReaderAgent,
    FeatureExtractorAgent,
    FeedbackClassifierAgent,
    QualityCriticAgent,
    TicketCreatorAgent,
)
from .config import DATA_DIR, DEFAULT_CONFIG, OUTPUT_DIR, STORAGE_DIR, PipelineConfig
from .models import Ticket
from .storage import SQLiteStorage
from .vector_store import ChromaVectorStore


class FeedbackPipeline:
    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.reader = CSVReaderAgent()
        self.classifier = FeedbackClassifierAgent(config)
        self.bug_analyzer = BugAnalysisAgent()
        self.feature_extractor = FeatureExtractorAgent()
        self.ticket_creator = TicketCreatorAgent()
        self.critic = QualityCriticAgent()
        self.storage = SQLiteStorage(STORAGE_DIR / "feedback_system.db")
        self.vector_store = ChromaVectorStore(STORAGE_DIR / "chroma")

    def run(self) -> dict:
        self._load_product_docs()
        items = self.reader.read(DATA_DIR)
        tickets: list[Ticket] = []
        logs: list[dict] = []

        for index, item in enumerate(items, start=1):
            self.storage.save_feedback(item)
            self.vector_store.upsert_feedback(
                item.source_id,
                item.text,
                {"source_type": item.source_type, "date": item.date or "", "platform": item.platform or ""},
            )

            classification = self.classifier.classify(item)
            if classification.category == "Bug":
                analysis = self.bug_analyzer.analyze(item)
            elif classification.category == "Feature Request":
                product_context = " ".join(self.vector_store.query_docs(item.text))
                analysis = self.feature_extractor.extract(item)
                analysis["technical_details"] += f" Related product context: {product_context[:180]}"
            else:
                analysis = {
                    "technical_details": "No technical extraction required for this feedback type.",
                    "user_impact": "Captured for product analytics and support visibility.",
                }

            ticket = self.ticket_creator.create(item, classification, analysis, index)
            ticket = self.critic.review(ticket)
            self.storage.save_ticket(ticket)
            self.vector_store.upsert_ticket(
                ticket.ticket_id,
                f"{ticket.title}. {ticket.description}. {ticket.technical_details}",
                {"source_id": ticket.source_id, "category": ticket.category, "priority": ticket.priority},
            )
            tickets.append(ticket)
            logs.append(
                {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "source_id": item.source_id,
                    "agent_path": self._agent_path(classification.category),
                    "category": classification.category,
                    "priority": classification.priority,
                    "confidence": classification.confidence,
                    "decision": classification.rationale,
                    "ticket_id": ticket.ticket_id,
                    "quality_score": ticket.quality_score,
                    "status": ticket.status,
                }
            )

        tickets_df = pd.DataFrame([ticket.to_dict() for ticket in tickets])
        logs_df = pd.DataFrame(logs)
        metrics_df = self._metrics(tickets_df)

        tickets_df.to_csv(OUTPUT_DIR / "generated_tickets.csv", index=False)
        logs_df.to_csv(OUTPUT_DIR / "processing_log.csv", index=False)
        metrics_df.to_csv(OUTPUT_DIR / "metrics.csv", index=False)
        return {"tickets": tickets_df, "logs": logs_df, "metrics": metrics_df}

    def _load_product_docs(self) -> None:
        doc_path = DATA_DIR / "product_docs.md"
        if doc_path.exists():
            text = doc_path.read_text(encoding="utf-8")
            chunks = [(f"product_doc_{idx}", chunk.strip()) for idx, chunk in enumerate(text.split("\n\n"), start=1) if chunk.strip()]
            self.vector_store.upsert_docs(chunks)

    @staticmethod
    def _agent_path(category: str) -> str:
        if category == "Bug":
            return "CSV Reader -> Classifier -> Bug Analyzer -> Ticket Creator -> Quality Critic"
        if category == "Feature Request":
            return "CSV Reader -> Classifier -> Feature Extractor -> Ticket Creator -> Quality Critic"
        return "CSV Reader -> Classifier -> Ticket Creator -> Quality Critic"

    @staticmethod
    def _metrics(tickets_df: pd.DataFrame) -> pd.DataFrame:
        expected_path = DATA_DIR / "expected_classifications.csv"
        total = len(tickets_df)
        approved = int((tickets_df["status"] == "Approved").sum()) if total else 0
        accuracy = None
        if expected_path.exists() and total:
            expected = pd.read_csv(expected_path)
            merged = tickets_df.merge(expected, on="source_id", suffixes=("_actual", "_expected"))
            accuracy = round((merged["category_actual"] == merged["category_expected"]).mean(), 3)
        rows = [
            {"metric": "processed_feedback", "value": total},
            {"metric": "approved_tickets", "value": approved},
            {"metric": "needs_manual_review", "value": total - approved},
            {"metric": "classification_accuracy", "value": accuracy if accuracy is not None else "not_available"},
            {"metric": "average_quality_score", "value": round(tickets_df["quality_score"].mean(), 3) if total else 0},
        ]
        return pd.DataFrame(rows)


def run_pipeline() -> dict:
    return FeedbackPipeline().run()
