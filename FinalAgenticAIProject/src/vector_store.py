from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

import chromadb


class HashEmbeddingFunction:
    """Small deterministic embedding function that avoids external model downloads."""

    @staticmethod
    def name() -> str:
        return "hash_embedding_function"

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in input]

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self(input)

    @staticmethod
    def _embed(text: str, dimensions: int = 64) -> list[float]:
        vector = [0.0] * dimensions
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % dimensions
            vector[index] += 1.0
        norm = sum(value * value for value in vector) ** 0.5 or 1.0
        return [value / norm for value in vector]


class ChromaVectorStore:
    def __init__(self, path: Path):
        self.client = chromadb.PersistentClient(path=str(path))
        self.embedding_function = HashEmbeddingFunction()
        self.feedback = self.client.get_or_create_collection(
            "feedback_embeddings", embedding_function=self.embedding_function
        )
        self.tickets = self.client.get_or_create_collection(
            "ticket_embeddings", embedding_function=self.embedding_function
        )
        self.docs = self.client.get_or_create_collection(
            "product_docs", embedding_function=self.embedding_function
        )

    def upsert_feedback(self, item_id: str, document: str, metadata: dict) -> None:
        self.feedback.upsert(ids=[item_id], documents=[document], metadatas=[metadata])

    def upsert_ticket(self, ticket_id: str, document: str, metadata: dict) -> None:
        self.tickets.upsert(ids=[ticket_id], documents=[document], metadatas=[metadata])

    def upsert_docs(self, docs: Iterable[tuple[str, str]]) -> None:
        for doc_id, text in docs:
            self.docs.upsert(ids=[doc_id], documents=[text], metadatas=[{"source": "product_docs"}])

    def query_docs(self, text: str, n_results: int = 2) -> list[str]:
        result = self.docs.query(query_texts=[text], n_results=n_results)
        return result.get("documents", [[]])[0]
