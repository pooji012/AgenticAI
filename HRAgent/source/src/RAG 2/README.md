# Simple RAG Project for Teaching

This project is intentionally small and easy to explain in class.
It shows the full Retrieval-Augmented Generation flow using Python and the OpenAI API.

## Project Files

- `01_build_index.py` -> reads a file, chunks it, creates embeddings, and saves `index.json`
- `02_ask_rag.py` -> loads `index.json`, retrieves top chunks, and generates an answer
- `rag_utils.py` -> reusable helper functions
- `sample_knowledge.txt` -> starter knowledge base for classroom practice
- `requirements.txt` -> Python packages to install
- `.env.example` -> sample environment variables

## Step-by-Step Setup

### 1) Create virtual environment

#### Windows
```bash
python -m venv .venv
.venv\Scripts\activate
```

#### Mac/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install packages
```bash
pip install -r requirements.txt
```

### 3) Add environment variables
Create a `.env` file in the same folder and paste:
```env
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_MODEL=text-embedding-3-small
CHAT_MODEL=gpt-4o-mini
```

### 4) Build the index
```bash
python 01_build_index.py sample_knowledge.txt
```
This creates `index.json`.

You can also use your own files:
```bash
python 01_build_index.py my_notes.txt
python 01_build_index.py document.pdf
python 01_build_index.py document.docx
```

### 5) Ask questions
```bash
python 02_ask_rag.py
```
Then type a question such as:
- `What is RAG?`
- `Why do we use chunking?`
- `How do embeddings help retrieval?`

## How the Pipeline Works

1. A document is loaded.
2. The document is split into overlapping chunks.
3. Each chunk becomes an embedding vector.
4. Chunks and vectors are saved in `index.json`.
5. The user asks a question.
6. The question is also converted into an embedding.
7. Cosine similarity is used to find the most similar chunks.
8. Those chunks are sent as context to the LLM.
9. The LLM answers using the retrieved context.

## Why This Version Is Good for Teaching

- It avoids too much framework complexity.
- The code is separated into logical files.
- You can show each RAG stage clearly.
- It supports `.txt`, `.pdf`, and `.docx`.
- Students can see retrieval before generation.
- It is easy to extend later with FAISS or LangChain.

## Common Errors

### `OPENAI_API_KEY was not found`
Your `.env` file is missing or the variable name is wrong.

### `File not found`
The input file path is wrong or the file is not in the project folder.

### `index.json not found`
Run `python 01_build_index.py sample_knowledge.txt` first.

## Next Improvement Ideas

- Replace JSON with FAISS for larger datasets
- Add metadata like filename and page number
- Use smarter chunking by sentence or paragraph
- Add citations in answers
- Build a Streamlit UI on top of this backend
