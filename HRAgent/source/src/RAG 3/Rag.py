# ==============================
# STEP 0: IMPORT LIBRARIES
# ==============================

import os                     # Used to read environment variables (API key)
import numpy as np            # Used for mathematical operations (vectors)
from dotenv import load_dotenv  # Used to load API key from .env file
from openai import OpenAI     # OpenAI client to call APIs


# ==============================
# STEP 1: LOAD API KEY
# ==============================

load_dotenv()  # This loads variables from .env file

# Create OpenAI client using API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ==============================
# STEP 2: CREATE DOCUMENTS (YOUR DATA)
# ==============================

# These are your "knowledge base"
# Think of this as your own mini Google / database
documents = [
    """Retrieval-Augmented Generation, usually called RAG, is a design pattern that helps a language model answer questions using external knowledge.

A normal LLM answers from what it learned during training. A RAG system first searches a knowledge source, finds relevant pieces of text, and then gives those pieces to the model as context.

The standard RAG flow is:
1. Load a document or a collection of documents.
2. Split the content into smaller chunks.
3. Convert each chunk into an embedding.
4. Store the embeddings in an index or vector database.
5. When a user asks a question, convert the question into an embedding.
6. Compare the question embedding with the stored chunk embeddings.
7. Retrieve the most similar chunks.
8. Send the question and retrieved chunks to the LLM.
9. Generate an answer grounded in the retrieved context.

Why is chunking needed? Because documents are often too large to send to the model at once, and smaller chunks improve retrieval precision.

Why are embeddings used? Because embeddings convert meaning into numbers, allowing us to compare semantic similarity.

RAG improves factual grounding, helps with private data, and reduces hallucinations. However, RAG is only as good as the source data, chunking strategy, retrieval quality, and prompt design.

A simple classroom demo of RAG can be built with a plain text file, OpenAI embeddings, cosine similarity, and a final answer-generation step using a chat model.
"""
]

# ==============================
# STEP 2.1:Simple Chunking function
# ==============================

def chunk_text(text, chunk_size=40, overlap=10):
    #split full texts into words
    words = text.split()

    #Empty List to store all the chunks
    chunks=[]

    #start position
    start =0

    while start < len(words):

        #End the position of current chunk
        end = start + chunk_size

        #Join selceted words into a string
        chunk = " ".join(words[start:end])

        #store the chunk only if not empty
        if chunk.strip():
            chunks.append(chunk)
    
    #Move start forwars, but let us keep someoverlap
    start += chunk_size-overlap

# ==============================
# STEP 2.2: SPLIT BIG DOCUMENTS INTO CHUNKS
# ==============================

chunks = chunk_text(documents, chunk_size=40, overlap=10)

# print chunks so we can understand what happened

print("Chunks Created: \n")
for i, chunk in enumerate(chunks):
    print(f"chunk {i+1}: ")
    print(chunk)
    print("-"*50)


# ==============================
# STEP 3: CONVERT Chunks / Document → EMBEDDINGS
# ==============================

# Here we send all documents to OpenAI
# OpenAI converts each sentence into a vector (numbers)

embedding_response = client.embeddings.create(
    model="text-embedding-3-small",  # embedding model
    input=chunks                  # list of texts
)

# Extract embeddings (vectors)
# Each document now has a vector representation
vectors = [item.embedding for item in embedding_response.data]

# Print to understand
print("Total documents:", len(documents))
print("Vector length of one document:", len(vectors[0]))


# ==============================
# STEP 4: TAKE USER QUESTION
# ==============================

# Ask a question
question = input("\nAsk your question: ")


# ==============================
# STEP 5: CONVERT QUESTION → EMBEDDING
# ==============================

# Convert user question into vector
query_response = client.embeddings.create(
    model="text-embedding-3-small",
    input=[question]
)

# Extract vector
query_vector = query_response.data[0].embedding


# ==============================
# STEP 6: COSINE SIMILARITY FUNCTION - 
# ==============================

# This function compares two vectors
# It tells how similar they are

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# ==============================
# STEP 7: FIND BEST MATCH
# ==============================

# Compare question vector with all document vectors
scores = [
    cosine_similarity(query_vector, vector)
    for vector in vectors
]

# for Autiability

# Find index of highest score (most similar)
best_index = int(np.argmax(scores))

# Get best matching text
best_chunk = documents[best_index]


# ==============================
# STEP 8: SHOW RETRIEVED RESULT
# ==============================

print("\nBest matching document:")
print(best_chunk)


# ==============================
# STEP 9: SEND TO OPENAI (FINAL ANSWER)
# ==============================

# We give ONLY the relevant context to AI
prompt = f"""
Answer the question using ONLY the context below.

Context:
{best_chunk}

Question:
{question}
"""

# Generate response
response = client.responses.create(
    model="gpt-4.1-mini",   # fast and good model
    input=prompt
)

# Print final answer
print("\nFinal Answer:\n")
print(response.output_text)