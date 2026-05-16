import os, json
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, "index.json")

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Load API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Safe defaults
embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
gen_model = os.getenv("MODEL", "gpt-4.1-mini")

# 1️ Load index
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

chunks = data["chunks"]
vectors = np.array(data["vectors"])

# 2️ Ask question
question = input("Ask your question: ")

# 3️ Embed question
response = client.embeddings.create(
    model=embedding_model,
    input=[question]
)

query_vector = np.array(response.data[0].embedding)

# 4️ Cosine similarity
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

similarities = [
    cosine_similarity(query_vector, np.array(vector))
    for vector in vectors
]

best_match_index = int(np.argmax(similarities))
best_match_chunk = chunks[best_match_index]

print("\nBest matching chunk:\n")
print(best_match_chunk)

# 5️ Generate grounded answer
prompt = f"""
Answer the question using ONLY the context below.

Context:
{best_match_chunk}

Question:
{question}
"""

response = client.responses.create(
    model=gen_model,
    input=prompt
)

print("\nGenerated Answer:\n")
print(response.output_text)