# Competitive Analysis Agent with Agentic RAG

This project implements an AI-powered competitive analysis agent using Agentic RAG, LlamaIndex, and OpenAI.

## What it does

- Loads competitor data from `competitor_data.csv`.
- Cleans the text for better retrieval.
- Builds a LlamaIndex vector index using OpenAI embeddings.
- Uses a ReAct-style flow to reason about the query, choose sub-goals, retrieve context, and generate an answer.
- Keeps query history.
- Provides an interactive command-line interface.

## Setup

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create your `.env` file:

```powershell
Copy-Item .env.example .env
```

4. Add your OpenAI API key inside `.env`:

```text
OPENAI_API_KEY=your_real_key_here
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small
```

5. Run the agent:

```powershell
python main.py
```

## Example queries

```text
Compare the marketing strategies of NovaTech and BrightDesk
What are the advantages of SecureSync?
Analyze the financial weaknesses of FlowCart
Give me an overview of MarketPulse
history
exit
```
