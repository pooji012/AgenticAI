import os
from typing import List, Optional, Dict

import chromadb
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm


# ---------------------------------------------------
# 1. Load environment variables
# ---------------------------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file")

openai_client = OpenAI(api_key=OPENAI_API_KEY)


# ---------------------------------------------------
# 2. Embedding generation function
# ---------------------------------------------------
def generate_embeddings(text_list: List[str], model_name: str = "text-embedding-3-small") -> List[List[float]]:
    """
    Convert a list of texts into embeddings using OpenAI.
    """
    response = openai_client.embeddings.create(
        model=model_name,
        input=text_list
    )
    return [item.embedding for item in response.data]


# ---------------------------------------------------
# 3. Chroma-compatible embedding function
# ---------------------------------------------------
class OpenAIEmbeddingFunction:
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name

    def __call__(self, input: List[str]) -> List[List[float]]:
        response = openai_client.embeddings.create(
            model=self.model_name,
            input=input
        )
        return [item.embedding for item in response.data]

    def name(self) -> str:
        return "openai-embedding-function"


# ---------------------------------------------------
# 4. Create persistent ChromaDB client
# A Persistent client stores data on a disk.
# That means even if tthe programs is stopped and restarted, the data will still be there.
# ---------------------------------------------------
chroma_client = chromadb.PersistentClient(path="./chroma_db")

openai_ef = OpenAIEmbeddingFunction()

collection = chroma_client.get_or_create_collection(
    name="tech_docs",
    embedding_function=openai_ef
)


# ---------------------------------------------------
# 5. Sample documents
# ---------------------------------------------------
documents = [
    "ChromaDB supports metadata filtering and CRUD operations",
    "OpenAI embeddings capture semantic meaning for search applications",
    "HNSW indexing enables efficient approximate nearest neighbor search",
    "Retrieval evaluation requires precision@k and recall@k metrics",
    "Vector databases store embeddings for similarity search"
]

metadatas = [
    {"category": "chromadb", "source": "docs"},
    {"category": "embeddings", "source": "research"},
    {"category": "indexing", "source": "paper"},
    {"category": "evaluation", "source": "tutorial"},
    {"category": "vector-db", "source": "textbook"}
]

# Generate unique IDs for each document
# Each document needs a unique identifier (ID) to be stored in the collection. 
# #This allows us to reference and manage documents later on.
ids = [f"doc{i+1}" for i in range(len(documents))]


# ---------------------------------------------------
# 6. Insert documents
# Upsert means: Insert the document if it doesn't exist, or update it if it does.
# ---------------------------------------------------
collection.upsert(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print(f"Added/updated {len(ids)} documents in collection.")


# ---------------------------------------------------
# 7. Semantic search pipeline
# ---------------------------------------------------
def search_pipeline(query: str, n_results: int = 3, filters: Optional[Dict] = None) -> pd.DataFrame:
    """
    Run semantic search on the collection.
    """
    query_embedding = openai_ef([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=filters
    )

    return pd.DataFrame({
        "Document": results["documents"][0],
        "ID": results["ids"][0],
        "Distance": results["distances"][0],
        "Metadata": results["metadatas"][0]
    })


# ---------------------------------------------------
# 8. Example search
# ---------------------------------------------------
print("\n--- Search Example ---")
results_df = search_pipeline("How to measure search quality?", n_results=3)
print(results_df)


# ---------------------------------------------------
# 9. Ground truth for evaluation
# ---------------------------------------------------
test_queries = {
    "q1": {
        "text": "ChromaDB features",
        "relevant_ids": ["doc1"]
    },
    "q2": {
        "text": "Similarity search database",
        "relevant_ids": ["doc5"]
    },
    "q3": {
        "text": "Evaluation metrics for retrieval",
        "relevant_ids": ["doc4"]
    }
}


# ---------------------------------------------------
# 10. Evaluation function
# ---------------------------------------------------
def evaluate_retrieval(k: int = 3) -> pd.DataFrame:
    """
    Evaluate retrieval using Precision@k, Recall@k, and MRR.
    """
    rows = []

    for qid, data in tqdm(test_queries.items(), desc="Evaluating"):
        query_embedding = openai_ef([data["text"]])[0]

        search_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )

        retrieved_ids = search_results["ids"][0]
        relevant_set = set(data["relevant_ids"])
        retrieved_set = set(retrieved_ids)

        true_positives = len(relevant_set & retrieved_set)

        precision = true_positives / k
        recall = true_positives / len(relevant_set) if relevant_set else 0

        reciprocal_rank = 0
        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in relevant_set:
                reciprocal_rank = 1 / rank
                break

# k means matching nodes. Precision@k measures how many of those top k results are relevant, while Recall@k measures how many of the relevant documents were retrieved in those top k results. MRR (Mean Reciprocal Rank) gives us insight into how high the first relevant document appears in the search results, which is crucial for user experience.
        rows.append({
            "query": data["text"],
            "retrieved_ids": retrieved_ids,
            "precision@k": precision, # Out of top k results(top matching nodes), how many are relevant? This also measures the result cleanliness. If precision is low, it means there are many irrelevant results in the top k.
            "recall@k": recall, # Out of all relevant documents, how many were retrieved in the top k? This also measures the result completeness. If recall is low, it means many relevant documents are missing from the top k results.
            "mrr": reciprocal_rank # It checks how early the first relevant document appears in the search results. A higher MRR means that users are more likely to see relevant results at the top of their search results, which is crucial for user satisfaction.
            # Higher the MRR is the better, because it means that users are more likely to see relevant results at the top of their search results, which is crucial for user satisfaction.
       
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------
# 11. Run evaluation
# ---------------------------------------------------
print("\n--- Evaluation Results ---")
eval_results = evaluate_retrieval(k=2)
print(eval_results)

avg_metrics = pd.DataFrame({
    "Metric": ["Precision@2", "Recall@2", "MRR"],
    "Average Value": [
        eval_results["precision@k"].mean(),
        eval_results["recall@k"].mean(),
        eval_results["mrr"].mean()
    ]
})

print("\n--- Average Metrics ---")
print(avg_metrics)