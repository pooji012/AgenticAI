"""Utility functions for a simple, teachable RAG pipeline.

This module keeps the logic small and readable so it is easy to explain in class.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Iterable, List

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None

try:
    from docx import Document as DocxDocument
except Exception:  # pragma: no cover
    DocxDocument = None


load_dotenv()

INDEX_FILE = "index.json"
DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
DEFAULT_CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")


def get_client() -> OpenAI:
    """Create an OpenAI client using the API key from the environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY was not found. Put it in your .env file or environment variables."
        )
    return OpenAI(api_key=api_key)


def load_text_from_file(file_path: str) -> str:
    """Load text from .txt, .pdf, or .docx files."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".txt":
        return path.read_text(encoding="utf-8")

    if suffix == ".pdf":
        if PdfReader is None:
            raise ImportError("pypdf is not installed. Run: pip install pypdf")
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)

    if suffix == ".docx":
        if DocxDocument is None:
            raise ImportError("python-docx is not installed. Run: pip install python-docx")
        doc = DocxDocument(str(path))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    raise ValueError("Supported file types are: .txt, .pdf, .docx")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks.

    Overlap is useful because important ideas often span chunk boundaries.
    """
    text = " ".join(text.split())
    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: List[str] = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += step

    return chunks


def create_embeddings(client: OpenAI, texts: Iterable[str], model: str = DEFAULT_EMBEDDING_MODEL) -> List[List[float]]:
    """Create embeddings for a list of texts."""
    texts = list(texts)
    response = client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in response.data]


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    denom = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
    if denom == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / denom)


def save_index(chunks: List[str], vectors: List[List[float]], output_file: str = INDEX_FILE) -> None:
    """Save chunks and vectors into a JSON file."""
    payload = {
        "chunks": chunks,
        "vectors": vectors,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_index(index_file: str = INDEX_FILE) -> tuple[list[str], np.ndarray]:
    """Load chunks and vectors from the JSON index file."""
    with open(index_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    chunks = data["chunks"]
    vectors = np.array(data["vectors"], dtype=np.float32)
    return chunks, vectors


def retrieve_top_k(
    client: OpenAI,
    question: str,
    chunks: List[str],
    vectors: np.ndarray,
    top_k: int = 3,
    model: str = DEFAULT_EMBEDDING_MODEL,
) -> list[dict]:
    """Retrieve the most relevant chunks for a question."""
    question_vector = create_embeddings(client, [question], model=model)[0]
    question_vector = np.array(question_vector, dtype=np.float32)

    scored = []
    for idx, chunk_vector in enumerate(vectors):
        score = cosine_similarity(question_vector, chunk_vector)
        scored.append({"rank": idx, "score": score, "chunk": chunks[idx]})

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def build_context(retrieved_chunks: list[dict]) -> str:
    """Format retrieved chunks into a readable context block."""
    lines = []
    for i, item in enumerate(retrieved_chunks, start=1):
        lines.append(f"Context {i}:\n{item['chunk']}")
    return "\n\n".join(lines)


def answer_with_rag(
    client: OpenAI,
    question: str,
    context: str,
    model: str = DEFAULT_CHAT_MODEL,
) -> str:
    """Generate an answer grounded in the retrieved context."""
    prompt = f"""
You are a helpful teacher.
Answer the user's question only from the provided context.
If the answer is not present in the context, clearly say that it is not available in the retrieved text.

Question:
{question}

Retrieved Context:
{context}
""".strip()

    response = client.responses.create(
        model=model,
        input=prompt,
    )
    return response.output_text
