# HR Agent

An AI-powered HR Assistant built with LangGraph, OpenAI, and Langfuse. It answers employee queries about company policies and employee details through a Streamlit chat interface.

## Architecture

```
Users → Streamlit App → HR Agent (LangGraph)
                              ├── Memory (follow-up questions)
                              └── Tools
                                    ├── Policies - RAG (ChromaDB)
                                    └── Employee Details - SQLite
```

- **LangGraph** — Agent orchestration with conditional tool calling loop
- **OpenAI (GPT-4o)** — LLM for reasoning and responses
- **Langfuse** — Tracing and observability for every agent invocation
- **ChromaDB** — Vector store for HR policy document retrieval (RAG)
- **SQLite** — Employee database with 15 sample records
- **MemorySaver** — Conversation memory for follow-up questions
- **Streamlit** — Chat UI for user interaction

## Project Structure

```
HR Agent/
├── app.py                  # Streamlit chat UI
├── agent.py                # LangGraph agent with memory + Langfuse tracing
├── tools.py                # RAG (policy search) + SQLite (employee lookup) tools
├── db_setup.py             # Seeds SQLite database with sample employee data
├── hr_database.db          # SQLite database (auto-generated)
├── chroma_db/              # ChromaDB vector store (auto-generated)
├── policies/               # HR policy documents
│   ├── leave_policy.txt
│   ├── work_from_home_policy.txt
│   ├── expense_policy.txt
│   └── performance_review_policy.txt
├── .env                    # API keys (OpenAI + Langfuse)
├── requirements.txt
└── README.md
```

## Setup

### 1. Install dependencies

```bash
cd "HR Agent"
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your-openai-api-key

# Langfuse is optional — remove or leave these blank to run without tracing
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_BASE_URL=http://your-langfuse-server:port
```

Langfuse tracing is **optional**. If `LANGFUSE_SECRET_KEY` is not set, the agent runs without tracing.

### 3. Initialize the database

```bash
python db_setup.py
```

This creates `hr_database.db` with 15 sample employees across Engineering, HR, Finance, Marketing, Sales, and Management departments.

### 4. Run the application

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

The ChromaDB vector store is built automatically on first run by embedding the policy documents from the `policies/` folder.

## Sample Questions

**Policy queries (uses RAG):**
- How many casual leaves do I get?
- What is the WFH policy?
- What are the hotel expense limits?
- How does the performance review rating work?
- What is the maternity leave policy?

**Employee queries (uses SQLite):**
- What is Rahul Sharma's leave balance?
- Who works in the Engineering department?
- Show me all employees in Bangalore
- Who is Priya Mehta's manager?

**Follow-up questions (uses memory):**
- Ask "What is Rahul Sharma's leave balance?" then follow up with "What is his salary?" — the agent remembers the context.

## Langfuse Tracing

All agent interactions are traced in Langfuse. Each chat message creates a trace with:
- LLM calls (input/output, tokens, latency)
- Tool calls (policy search, database queries)
- Full conversation flow

View traces at your Langfuse dashboard URL configured in `.env`.
