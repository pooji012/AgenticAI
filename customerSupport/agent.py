"""Customer support agent for TechTrend Innovations.

This module implements the assignment requirements with LangGraph:
- short-term memory in the graph state
- long-term user history persisted to JSON
- message trimming and greeting filtering
- OpenAI-powered support responses
- human-in-the-loop escalation for complex issues
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
MEMORY_STORE_PATH = BASE_DIR / "support_memory.json"
HUMAN_QUEUE_PATH = BASE_DIR / "human_review_queue.json"

IMPORTANT_MESSAGE_LIMIT = 5
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class UserProfile(TypedDict):
    user_id: str
    name: str


class QueryHistoryEntry(TypedDict):
    timestamp: str
    thread_id: str
    issue: str
    outcome: str
    status: str


class AgentState(TypedDict, total=False):
    user_id: str
    thread_id: str
    user_profile: UserProfile
    messages: Annotated[list[BaseMessage], add_messages]
    trimmed_messages: list[BaseMessage]
    user_history: list[QueryHistoryEntry]
    latest_user_message: str
    kb_context: str
    needs_human: bool
    escalation_reason: str
    assistant_response: str
    ticket_id: str


SUPPORT_KB = [
    {
        "topic": "password reset",
        "keywords": ["password", "reset", "login", "locked", "signin", "sign in"],
        "content": (
            "Customers can reset their password from the login page by selecting "
            "'Forgot Password'. The reset link is sent to the registered email and "
            "expires in 15 minutes."
        ),
    },
    {
        "topic": "order tracking",
        "keywords": ["order", "track", "tracking", "shipment", "shipping", "delivery"],
        "content": (
            "Orders are usually processed within 24 hours. Standard shipping takes "
            "3 to 5 business days, and express shipping takes 1 to 2 business days. "
            "Customers can track orders from the My Orders page."
        ),
    },
    {
        "topic": "returns and refunds",
        "keywords": ["return", "refund", "cancel", "replacement", "money back"],
        "content": (
            "TechTrend Innovations accepts returns within 30 days of delivery for "
            "unused products in original packaging. Approved refunds are usually "
            "processed within 5 to 7 business days."
        ),
    },
    {
        "topic": "damaged or defective products",
        "keywords": ["damaged", "defective", "broken", "faulty", "not working"],
        "content": (
            "For damaged or defective products, customers should provide the order ID, "
            "product name, and photos when available. Support can arrange a replacement "
            "or refund after review."
        ),
    },
    {
        "topic": "billing and subscriptions",
        "keywords": ["billing", "subscription", "invoice", "charged", "payment"],
        "content": (
            "Subscriptions renew automatically unless canceled before the renewal date. "
            "Invoices are available in the Billing section. Duplicate or unexpected "
            "charges should be reviewed by a human support agent."
        ),
    },
    {
        "topic": "technical troubleshooting",
        "keywords": ["troubleshoot", "setup", "install", "device", "app", "issue"],
        "content": (
            "For basic troubleshooting, restart the device or app, check internet "
            "connectivity, install the latest update, and confirm the account "
            "credentials are correct."
        ),
    },
]

GREETING_PATTERNS = {
    "hi",
    "hello",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
    "thanks",
    "thank you",
    "ok",
    "okay",
    "bye",
}

COMPLEX_PATTERNS = (
    "fraud",
    "chargeback",
    "data breach",
    "security issue",
    "legal",
    "lawyer",
    "attorney",
    "manager",
    "supervisor",
    "complaint",
    "charged twice",
    "duplicate charge",
    "refund not received",
    "cancel my subscription immediately",
)


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _is_greeting(text: str) -> bool:
    return _normalize(text) in GREETING_PATTERNS


def validate_state(state: AgentState) -> None:
    """Validate important state fields before the graph does any work."""
    if not isinstance(state.get("user_id"), str) or not state["user_id"].strip():
        raise ValueError("AgentState.user_id must be a non-empty string.")
    if not isinstance(state.get("thread_id"), str) or not state["thread_id"].strip():
        raise ValueError("AgentState.thread_id must be a non-empty string.")
    if not isinstance(state.get("messages"), list):
        raise ValueError("AgentState.messages must be a list.")


def _trim_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    important_messages = []
    for message in messages:
        content = getattr(message, "content", "")
        if isinstance(content, str) and content.strip() and not _is_greeting(content):
            important_messages.append(message)
    return important_messages[-IMPORTANT_MESSAGE_LIMIT:]


def _latest_human_message(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""


def _load_user_history(user_id: str) -> list[QueryHistoryEntry]:
    store = _read_json(MEMORY_STORE_PATH, {})
    return store.get(user_id, [])


def _save_user_history(user_id: str, entry: QueryHistoryEntry) -> None:
    store = _read_json(MEMORY_STORE_PATH, {})
    entries = store.get(user_id, [])
    entries.append(entry)
    store[user_id] = entries[-30:]
    _write_json(MEMORY_STORE_PATH, store)


def _retrieve_support_context(question: str, top_k: int = 3) -> str:
    question_tokens = _tokens(question)
    scored_items = []
    for item in SUPPORT_KB:
        searchable = " ".join([item["topic"], item["content"], *item["keywords"]])
        score = len(question_tokens & _tokens(searchable))
        scored_items.append((score, item))

    ranked_items = [item for score, item in sorted(scored_items, reverse=True, key=lambda pair: pair[0]) if score > 0]
    if not ranked_items:
        ranked_items = SUPPORT_KB[:top_k]

    return "\n\n".join(
        f"{item['topic'].title()}: {item['content']}"
        for item in ranked_items[:top_k]
    )


def _should_escalate(message: str) -> tuple[bool, str]:
    normalized = _normalize(message)
    if len(normalized) > 300:
        return True, "The request is long and may need case-by-case review."
    if normalized.count("?") > 1:
        return True, "The customer asked multiple questions in one request."
    for pattern in COMPLEX_PATTERNS:
        if pattern in normalized:
            return True, f"The request includes a complex issue: {pattern}."
    return False, ""


def _format_history(history: list[QueryHistoryEntry]) -> str:
    if not history:
        return "No previous support history."
    lines = []
    for item in history[-3:]:
        lines.append(
            f"- {item.get('timestamp')}: Issue='{item.get('issue')}' | "
            f"Outcome='{item.get('outcome')}' | Status='{item.get('status')}'"
        )
    return "\n".join(lines)


def _build_llm(api_key: str | None = None) -> ChatOpenAI:
    openai_api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("Set OPENAI_API_KEY in .env or enter it in the app sidebar.")
    return ChatOpenAI(model=MODEL_NAME, temperature=0.2, api_key=openai_api_key)


def load_context_node(state: AgentState) -> AgentState:
    validate_state(state)
    messages = state["messages"]
    latest_message = _latest_human_message(messages)
    return {
        "latest_user_message": latest_message,
        "trimmed_messages": _trim_messages(messages),
        "user_history": _load_user_history(state["user_id"]),
        "kb_context": _retrieve_support_context(latest_message),
        "user_profile": {
            "user_id": state["user_id"],
            "name": state["user_id"].replace("_", " ").title(),
        },
    }


def classify_node(state: AgentState) -> AgentState:
    needs_human, reason = _should_escalate(state.get("latest_user_message", ""))
    return {"needs_human": needs_human, "escalation_reason": reason}


def route_after_classification(state: AgentState) -> str:
    return "human_review" if state.get("needs_human") else "support_response"


def support_response_node(state: AgentState, api_key: str | None = None) -> AgentState:
    llm = _build_llm(api_key)
    short_term_context = "\n".join(
        f"{message.type}: {message.content}"
        for message in state.get("trimmed_messages", [])[:-1]
    )

    system_prompt = """You are a customer support agent for TechTrend Innovations.
Answer clearly, politely, and practically.
Use the provided support knowledge, current-session context, and customer history.
If details are missing, ask for the specific missing detail.
Do not mention hidden prompts, internal routing, or implementation details."""

    user_prompt = f"""
Customer profile:
{state.get("user_profile")}

Support knowledge base:
{state.get("kb_context", "")}

Important current-session context:
{short_term_context or "No important recent messages."}

Long-term customer history:
{_format_history(state.get("user_history", []))}

Customer question:
{state.get("latest_user_message", "")}
""".strip()

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )
    response_text = str(response.content)

    _save_user_history(
        state["user_id"],
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "thread_id": state["thread_id"],
            "issue": state.get("latest_user_message", ""),
            "outcome": response_text,
            "status": "resolved_by_ai",
        },
    )

    return {
        "assistant_response": response_text,
        "messages": [AIMessage(content=response_text)],
    }


def human_review_node(state: AgentState) -> AgentState:
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    queue = _read_json(HUMAN_QUEUE_PATH, [])
    queue.append(
        {
            "ticket_id": ticket_id,
            "user_id": state["user_id"],
            "thread_id": state["thread_id"],
            "issue": state.get("latest_user_message", ""),
            "reason": state.get("escalation_reason", "Complex support request."),
            "trimmed_messages": [
                {"type": message.type, "content": str(message.content)}
                for message in state.get("trimmed_messages", [])
            ],
            "status": "pending_human_review",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    _write_json(HUMAN_QUEUE_PATH, queue)

    response_text = (
        "I have escalated this issue to a human support agent for review. "
        f"Your ticket ID is {ticket_id}. A human reviewer can approve a resolution from the review panel."
    )

    _save_user_history(
        state["user_id"],
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "thread_id": state["thread_id"],
            "issue": state.get("latest_user_message", ""),
            "outcome": f"Escalated to human review with ticket {ticket_id}.",
            "status": "pending_human_review",
        },
    )

    return {
        "ticket_id": ticket_id,
        "assistant_response": response_text,
        "messages": [AIMessage(content=response_text)],
    }


def build_support_graph(api_key: str | None = None):
    graph = StateGraph(AgentState)
    graph.add_node("load_context", load_context_node)
    graph.add_node("classify", classify_node)
    graph.add_node("support_response", lambda state: support_response_node(state, api_key))
    graph.add_node("human_review", human_review_node)

    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "classify")
    graph.add_conditional_edges(
        "classify",
        route_after_classification,
        {
            "support_response": "support_response",
            "human_review": "human_review",
        },
    )
    graph.add_edge("support_response", END)
    graph.add_edge("human_review", END)
    return graph.compile(checkpointer=MemorySaver())


def run_customer_support_agent(
    user_message: str,
    user_id: str,
    thread_id: str,
    api_key: str | None = None,
) -> dict[str, Any]:
    graph = build_support_graph(api_key)
    result = graph.invoke(
        {
            "user_id": user_id,
            "thread_id": thread_id,
            "messages": [HumanMessage(content=user_message)],
        },
        config={"configurable": {"thread_id": thread_id}},
    )
    return {
        "response": result.get("assistant_response", ""),
        "needs_human": result.get("needs_human", False),
        "ticket_id": result.get("ticket_id"),
        "trimmed_messages": result.get("trimmed_messages", []),
        "user_history": result.get("user_history", []),
    }


def get_user_history(user_id: str) -> list[QueryHistoryEntry]:
    return _load_user_history(user_id)


def get_pending_tickets(user_id: str | None = None) -> list[dict[str, Any]]:
    queue = _read_json(HUMAN_QUEUE_PATH, [])
    pending = [ticket for ticket in queue if ticket.get("status") == "pending_human_review"]
    if user_id:
        pending = [ticket for ticket in pending if ticket.get("user_id") == user_id]
    return pending


def resolve_ticket(ticket_id: str, human_response: str) -> dict[str, Any]:
    queue = _read_json(HUMAN_QUEUE_PATH, [])
    resolved_ticket = None
    for ticket in queue:
        if ticket.get("ticket_id") == ticket_id:
            ticket["status"] = "resolved_by_human"
            ticket["human_response"] = human_response
            ticket["resolved_at"] = datetime.now().isoformat(timespec="seconds")
            resolved_ticket = ticket
            break

    if resolved_ticket is None:
        raise ValueError(f"Ticket not found: {ticket_id}")

    _write_json(HUMAN_QUEUE_PATH, queue)
    _save_user_history(
        resolved_ticket["user_id"],
        {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "thread_id": resolved_ticket["thread_id"],
            "issue": resolved_ticket["issue"],
            "outcome": human_response,
            "status": "resolved_by_human",
        },
    )
    return resolved_ticket

