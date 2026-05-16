"""Step 1 of the RAG pipeline: load a file, split it, embed it, and save index.json.

Run example:
python 01_build_index.py sample_knowledge.txt
"""

from __future__ import annotations

import sys

from rag_utils import (
    DEFAULT_EMBEDDING_MODEL,
    get_client,
    chunk_text,
    create_embeddings,
    load_text_from_file,
    save_index,
)


def main() -> None:
    file_path = sys.argv[1] if len(sys.argv) > 1 else "sample_knowledge.txt"
    client = get_client()

    print(f"Loading file: {file_path}")
    text = load_text_from_file(file_path)

    print("Splitting text into chunks...")
    chunks = chunk_text(text, chunk_size=500, overlap=100)
    if not chunks:
        raise ValueError("No chunks were created. Check whether the input file has text.")

    print(f"Total chunks created: {len(chunks)}")
    print(f"Creating embeddings using model: {DEFAULT_EMBEDDING_MODEL}")
    vectors = create_embeddings(client, chunks)

    print("Saving index to index.json...")
    save_index(chunks, vectors)

    print("Done. Your RAG knowledge index is ready.")


if __name__ == "__main__":
    main()
