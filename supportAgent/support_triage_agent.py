"""Customer Support Triage Agent for the Agno assignment."""

from __future__ import annotations

import io
import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from pypdf import PdfReader

from vector_store import LocalVectorStore

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
VECTOR_STORE_PATH = DATA_DIR / "support_knowledge.json"
SESSION_STATE_PATH = DATA_DIR / "session_history.json"

INTENT_KEYWORDS = {
    "refund": ["refund", "return", "money back", "reimburse", "cancel order"],
    "shipping": ["shipping", "delivery", "delayed", "late", "tracking", "package"],
    "product issue": ["broken", "damaged", "defective", "faulty", "missing item"],
    "account": ["login", "password", "account", "email", "profile", "locked"],
    "billing": ["charged", "payment", "invoice", "subscription", "card"],
}

NEGATIVE_WORDS = {
    "angry",
    "bad",
    "broken",
    "cancel",
    "complaint",
    "delayed",
    "disappointed",
    "faulty",
    "frustrated",
    "late",
    "lost",
    "missing",
    "not working",
    "poor",
    "refund",
    "terrible",
    "worst",
}

POSITIVE_WORDS = {
    "appreciate",
    "good",
    "great",
    "happy",
    "helpful",
    "resolved",
    "thanks",
    "thank you",
}

URGENT_WORDS = {
    "asap",
    "immediately",
    "urgent",
    "emergency",
    "today",
    "legal",
    "fraud",
    "chargeback",
    "manager",
    "supervisor",
}


@dataclass
class TriageResult:
    ticket_id: str
    issue: str
    intent: str
    sentiment: str
    urgency: str
    topic: str
    route_to: str
    escalation_needed: bool
    draft_response: str


class SimpleAgnoCompatibleAgent:
    """Fallback wrapper used when the installed Agno package is unavailable.

    The repository already contains a folder named ``agno``, which can shadow the
    real package. This class keeps the assignment structure intact locally.
    """

    def __init__(self, name: str, instructions: str) -> None:
        self.name = name
        self.instructions = instructions


def build_agno_agent() -> Any:
    try:
        from agno.agent import Agent
        from agno.models.openai import OpenAIChat

        model_id = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        model = OpenAIChat(id=model_id) if os.getenv("OPENAI_API_KEY") else None
        return Agent(
            name="SupportTriageAgent",
            model=model,
            instructions=[
                "Categorize customer support tickets.",
                "Extract intent, sentiment, urgency, and topic.",
                "Suggest concise, policy-aware support replies.",
                "Use retrieved support history and policy sections as context.",
            ],
            markdown=True,
        )
    except Exception:
        return SimpleAgnoCompatibleAgent(
            name="SupportTriageAgent",
            instructions=(
                "Categorize support tickets, detect sentiment and urgency, "
                "retrieve relevant history/policy context, and suggest replies."
            ),
        )


class SupportTriageAgent:
    """Assignment-facing agent class."""

    def __init__(self) -> None:
        self.agent = build_agno_agent()
        self.store = LocalVectorStore(VECTOR_STORE_PATH)

    def ingest_uploaded_file(self, file_name: str, file_bytes: bytes) -> dict[str, Any]:
        suffix = Path(file_name).suffix.lower()
        if suffix == ".csv":
            chunks, tickets = self._parse_csv(file_name, file_bytes)
        elif suffix == ".txt":
            chunks, tickets = self._parse_txt(file_name, file_bytes)
        elif suffix == ".pdf":
            chunks, tickets = self._parse_pdf(file_name, file_bytes)
        else:
            raise ValueError("Only CSV, TXT, and PDF files are supported.")

        self.store.add_documents(chunks)
        return {
            "file_name": file_name,
            "chunks_added": len(chunks),
            "tickets_found": len(tickets),
            "tickets": tickets,
        }

    def triage_ticket(self, issue: str, timestamp: str = "") -> TriageResult:
        clean_issue = normalize_text(issue)
        intent = detect_intent(clean_issue)
        sentiment = detect_sentiment(clean_issue)
        urgency = detect_urgency(clean_issue)
        topic = intent.title()
        escalation_needed = urgency == "high" or sentiment == "negative"
        route_to = route_for_intent(intent, escalation_needed)
        policy_matches = self.search(f"{intent} policy {clean_issue}", top_k=2)
        draft_response = self.generate_draft_response(
            issue=clean_issue,
            intent=intent,
            sentiment=sentiment,
            urgency=urgency,
            policy_matches=policy_matches,
        )
        result = TriageResult(
            ticket_id=f"TKT-{uuid.uuid4().hex[:8].upper()}",
            issue=clean_issue,
            intent=intent,
            sentiment=sentiment,
            urgency=urgency,
            topic=topic,
            route_to=route_to,
            escalation_needed=escalation_needed,
            draft_response=draft_response,
        )
        self._save_session_event(
            {
                "type": "triage",
                "timestamp": timestamp or datetime.now().isoformat(timespec="seconds"),
                "result": result.__dict__,
            }
        )
        return result

    def analyze_tickets(self, tickets: list[dict[str, Any]]) -> pd.DataFrame:
        rows = []
        for ticket in tickets:
            issue = ticket.get("issue", "")
            result = self.triage_ticket(issue, ticket.get("timestamp", ""))
            rows.append(
                {
                    "ticket_id": result.ticket_id,
                    "timestamp": ticket.get("timestamp", ""),
                    "issue": result.issue,
                    "intent": result.intent,
                    "sentiment": result.sentiment,
                    "urgency": result.urgency,
                    "route_to": result.route_to,
                    "escalation_needed": result.escalation_needed,
                    "draft_response": result.draft_response,
                }
            )
        return pd.DataFrame(rows)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self.store.search(query, top_k=top_k)

    def answer_query(self, query: str) -> str:
        matches = self.search(query, top_k=5)
        if not matches:
            return "I do not have uploaded support data yet. Upload support logs or policies first."

        context_lines = [
            f"- {item.get('source')} | {item.get('kind')}: {item.get('text', '')[:350]}"
            for item in matches
        ]
        summary = summarize_matches(matches)

        llm_answer = self._try_llm_answer(query, "\n".join(context_lines))
        if llm_answer:
            answer = llm_answer
        else:
            answer = (
                f"{summary}\n\n"
                "Most relevant sources:\n"
                + "\n".join(context_lines[:3])
            )

        self._save_session_event(
            {
                "type": "chat",
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "query": query,
                "answer": answer,
            }
        )
        return answer

    def clear_knowledge(self) -> None:
        self.store.clear()

    def _try_llm_answer(self, query: str, context: str) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return ""
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a customer support triage analyst. Answer "
                            "using only the uploaded ticket and policy context."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Question:\n{query}\n\nContext:\n{context}",
                    },
                ],
            )
            return response.choices[0].message.content or ""
        except Exception:
            return ""

    def generate_draft_response(
        self,
        issue: str,
        intent: str,
        sentiment: str,
        urgency: str,
        policy_matches: list[dict[str, Any]],
    ) -> str:
        policy_note = ""
        if policy_matches:
            policy_note = f" Based on our policy, {policy_matches[0].get('text', '')[:180]}..."

        opener = "I am sorry for the trouble." if sentiment == "negative" else "Thanks for contacting support."
        action = {
            "refund": "Please share your order ID and delivery date so we can check refund eligibility.",
            "shipping": "Please share your order ID so we can check the latest tracking status.",
            "product issue": "Please share the order ID, product name, and a photo if the item is damaged.",
            "account": "Please confirm the registered email address so we can help with account access.",
            "billing": "Please share the invoice or transaction ID so we can review the charge.",
        }.get(intent, "Please share the order ID and any extra details so we can investigate.")

        escalation = " I am also routing this for priority review." if urgency == "high" else ""
        return f"{opener} {action}{policy_note}{escalation}"

    def _parse_csv(self, file_name: str, file_bytes: bytes) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        dataframe = pd.read_csv(io.BytesIO(file_bytes))
        tickets = []
        chunks = []
        for index, row in dataframe.iterrows():
            issue = pick_first_available(
                row,
                ["issue", "customer_issue", "message", "query", "complaint", "description", "ticket"],
            )
            if not issue:
                issue = " ".join(str(value) for value in row.dropna().values)
            timestamp = pick_first_available(row, ["timestamp", "date", "created_at", "time"])
            response = pick_first_available(row, ["response", "reply", "resolution"])
            ticket = {
                "issue": str(issue),
                "timestamp": str(timestamp),
                "response": str(response),
                "source": file_name,
            }
            tickets.append(ticket)
            chunks.append(
                make_chunk(
                    text=f"Issue: {issue}\nResponse: {response}",
                    source=file_name,
                    kind="support_ticket",
                    metadata={"row": int(index), "timestamp": str(timestamp)},
                )
            )
        return chunks, tickets

    def _parse_txt(self, file_name: str, file_bytes: bytes) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        text = file_bytes.decode("utf-8", errors="ignore")
        parts = chunk_text(text, max_words=160, overlap=30)
        chunks = [
            make_chunk(part, source=file_name, kind="support_note", metadata={"chunk": index + 1})
            for index, part in enumerate(parts)
        ]
        tickets = [{"issue": part, "timestamp": "", "response": "", "source": file_name} for part in parts]
        return chunks, tickets

    def _parse_pdf(self, file_name: str, file_bytes: bytes) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        reader = PdfReader(io.BytesIO(file_bytes))
        page_texts = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            page_texts.append((page_number, text))

        chunks = []
        for page_number, text in page_texts:
            for index, part in enumerate(chunk_text(text, max_words=180, overlap=25), start=1):
                chunks.append(
                    make_chunk(
                        part,
                        source=file_name,
                        kind="policy_document",
                        metadata={"page": page_number, "chunk": index},
                    )
                )
        return chunks, []

    def _save_session_event(self, event: dict[str, Any]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        history = []
        if SESSION_STATE_PATH.exists():
            try:
                history = json.loads(SESSION_STATE_PATH.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                history = []
        history.append(event)
        SESSION_STATE_PATH.write_text(json.dumps(history[-100:], indent=2), encoding="utf-8")


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip())


def detect_intent(text: str) -> str:
    lowered = text.lower()
    scores = {
        intent: sum(1 for keyword in keywords if keyword in lowered)
        for intent, keywords in INTENT_KEYWORDS.items()
    }
    best_intent, best_score = max(scores.items(), key=lambda item: item[1])
    return best_intent if best_score else "general support"


def detect_sentiment(text: str) -> str:
    lowered = text.lower()
    negative_score = sum(1 for word in NEGATIVE_WORDS if word in lowered)
    positive_score = sum(1 for word in POSITIVE_WORDS if word in lowered)
    if negative_score > positive_score:
        return "negative"
    if positive_score > negative_score:
        return "positive"
    return "neutral"


def detect_urgency(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in URGENT_WORDS):
        return "high"
    if any(word in lowered for word in ["soon", "waiting", "again", "still"]):
        return "medium"
    return "low"


def route_for_intent(intent: str, escalation_needed: bool) -> str:
    if escalation_needed:
        return "senior_support"
    routes = {
        "refund": "refund_team",
        "shipping": "logistics_team",
        "product issue": "product_support",
        "account": "account_support",
        "billing": "billing_team",
    }
    return routes.get(intent, "general_support")


def pick_first_available(row: pd.Series, columns: list[str]) -> str:
    lower_map = {str(column).lower().strip(): column for column in row.index}
    for column in columns:
        actual = lower_map.get(column)
        if actual is not None and not pd.isna(row[actual]):
            return str(row[actual])
    return ""


def chunk_text(text: str, max_words: int = 180, overlap: int = 30) -> list[str]:
    words = normalize_text(text).split()
    if not words:
        return []
    chunks = []
    step = max(max_words - overlap, 1)
    for start in range(0, len(words), step):
        part = " ".join(words[start : start + max_words])
        if part:
            chunks.append(part)
    return chunks


def make_chunk(text: str, source: str, kind: str, metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": uuid.uuid4().hex,
        "text": normalize_text(text),
        "source": source,
        "kind": kind,
        "metadata": metadata,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def summarize_matches(matches: list[dict[str, Any]]) -> str:
    intents = []
    sentiments = []
    urgency = []
    for item in matches:
        text = item.get("text", "")
        intents.append(detect_intent(text))
        sentiments.append(detect_sentiment(text))
        urgency.append(detect_urgency(text))

    top_intent = most_common(intents)
    top_sentiment = most_common(sentiments)
    high_count = sum(1 for value in urgency if value == "high")
    return (
        f"I found {len(matches)} relevant uploaded chunks. "
        f"The main topic appears to be {top_intent}, the common sentiment is "
        f"{top_sentiment}, and {high_count} result(s) look high urgency."
    )


def most_common(values: list[str]) -> str:
    if not values:
        return "unknown"
    return max(set(values), key=values.count)
