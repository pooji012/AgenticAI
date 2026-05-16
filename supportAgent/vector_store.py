"""Small local vector-style search store for support triage.

This uses TF-IDF-like weighted token vectors so the assignment can run without
an external vector database. The public methods mirror a simple vector store:
add documents, search by meaning-ish similarity, and persist to JSON.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


class LocalVectorStore:
    """Persistent local semantic/keyword search over uploaded chunks."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.documents: list[dict[str, Any]] = []
        self._idf: dict[str, float] = {}
        self._vectors: list[dict[str, float]] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        self.documents = payload.get("documents", [])
        self._rebuild_index()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"documents": self.documents}, indent=2),
            encoding="utf-8",
        )

    def clear(self) -> None:
        self.documents = []
        self._idf = {}
        self._vectors = []
        self.save()

    def add_documents(self, docs: list[dict[str, Any]]) -> None:
        self.documents.extend(docs)
        self._rebuild_index()
        self.save()

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not self.documents:
            return []
        query_vector = self._vectorize(query)
        scored = []
        for doc, vector in zip(self.documents, self._vectors):
            score = self._cosine(query_vector, vector)
            if score > 0:
                item = dict(doc)
                item["score"] = round(score, 4)
                scored.append(item)
        return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]

    def _rebuild_index(self) -> None:
        tokenized_docs = [set(tokenize(doc.get("text", ""))) for doc in self.documents]
        doc_count = max(len(tokenized_docs), 1)
        document_frequency = Counter(token for tokens in tokenized_docs for token in tokens)
        self._idf = {
            token: math.log((1 + doc_count) / (1 + frequency)) + 1
            for token, frequency in document_frequency.items()
        }
        self._vectors = [self._vectorize(doc.get("text", "")) for doc in self.documents]

    def _vectorize(self, text: str) -> dict[str, float]:
        counts = Counter(tokenize(text))
        if not counts:
            return {}
        max_count = max(counts.values())
        return {
            token: (count / max_count) * self._idf.get(token, 1.0)
            for token, count in counts.items()
        }

    @staticmethod
    def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        common_tokens = set(left) & set(right)
        dot = sum(left[token] * right[token] for token in common_tokens)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)
