import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

texts = [
    "Leave policy: 12 paid leaves per year.",
    "How to bake a chocolate cake.",
    "Vacation days and paid leave rules."
]

embeddings = client.embeddings.create(
    model=EMBEDDING_MODEL,
    input=texts
)

vectors = [item.embedding for item in embeddings.data]

print("vector Length:", len(vectors[0]))
print("Got vectors for the following texts:", len(vectors))