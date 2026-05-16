import os, json
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
embedding_model=os.getenv("EMBEDDING_MODEL")

def chunk_text(text, size=300):
    return [text[i:i+size] for i in range(0, len(text), size)]

#Read the document
with open('C:\\Batch Learning\\Prompt Engineering 3\\data\\PRACTICAL-GUIDE-TO-BUILDING-RETRIEVAL-AUGMENTED-GENERATION-RAG.pdf', 'r') as f:
    text = f.read()


#Chunk the document
chunks = chunk_text(text)

#Generate embeddings for each chunk
response = client.embeddings.create(
     model=embedding_model,
     input=chunks
    )

vectors = [item['embedding'] for item in response.data]

#Save the vectors and chunks to a JSON file
data = [
    {
        "chunks": chunks, 
        "vectors": vectors
     }
]

with open('index.json', 'w', encoding='utf-8') as f:
    json.dump(data, f)

print("Indexing completed and saved to index.json")    