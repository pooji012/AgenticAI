# TechTrend Customer Support Agent

This project implements the Module 04 assignment: a LangGraph customer support agent for TechTrend Innovations using OpenAI as the LLM.

## Features

- OpenAI-powered customer support responses
- LangGraph `StateGraph` workflow
- `AgentState` with `user_id`, `thread_id`, `messages`, `user_history`, and metadata
- Short-term memory using graph state and LangGraph checkpointing
- Long-term memory stored in `support_memory.json`
- Message trimming that keeps the last 5 important messages
- Greeting filtering
- Human-in-the-loop escalation with a review queue
- Streamlit user interface

## Setup

Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

You can also paste the API key into the Streamlit sidebar.

## Run

```bash
streamlit run app.py
```

## Workflow

```text
User query
  -> AgentState
  -> trim/filter messages
  -> fetch long-term user history
  -> classify simple vs complex request
  -> OpenAI response OR human-review ticket
  -> save outcome to long-term memory
  -> show response in UI
```

## Files Created At Runtime

- `support_memory.json`: stores long-term customer history.
- `human_review_queue.json`: stores pending and resolved human-review tickets.

