"""Step 2 of the RAG pipeline: load index.json, retrieve top chunks, and answer.

Run example:
python 02_ask_rag.py
"""

from __future__ import annotations

from rag_utils import (
    DEFAULT_CHAT_MODEL,
    DEFAULT_EMBEDDING_MODEL,
    answer_with_rag,
    build_context,
    get_client,
    load_index,
    retrieve_top_k,
)


def main() -> None:
    client = get_client()
    chunks, vectors = load_index()

    print("RAG system is ready.")
    question = input("Enter your question: ").strip()
    if not question:
        raise ValueError("Question cannot be empty.")

    retrieved = retrieve_top_k(client, question, chunks, vectors, top_k=3)
    context = build_context(retrieved)
    answer = answer_with_rag(client, question, context)

    print("\n--- Top Retrieved Chunks ---")
    for item in retrieved:
        preview = item["chunk"][:150].strip()
        print(f"Score: {item['score']:.4f} | {preview}...")

    print("\n--- Model Used ---")
    print(f"Embedding model: {DEFAULT_EMBEDDING_MODEL}")
    print(f"Chat model: {DEFAULT_CHAT_MODEL}")

    print("\n--- Final Answer ---")
    print(answer)


if __name__ == "__main__":
    main()
