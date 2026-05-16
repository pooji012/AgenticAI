"""HR Agent tools: Policy RAG and Employee DB lookup."""
import os
import sqlite3
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "hr_database.db")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
POLICIES_DIR = os.path.join(BASE_DIR, "policies")


# ── Build / load the vector store ────────────────────────────────────────────
def get_vectorstore():
    embeddings = OpenAIEmbeddings()
    if os.path.exists(CHROMA_DIR) and os.listdir(CHROMA_DIR):
        return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

    loader = DirectoryLoader(POLICIES_DIR, glob="*.txt", loader_cls=TextLoader)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_DIR)
    return vectorstore


_vectorstore = None


def _get_vs():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = get_vectorstore()
    return _vectorstore


# ── Tool 1: Policy RAG ──────────────────────────────────────────────────────
@tool
def search_hr_policies(query: str) -> str:
    """Search company HR policies (leave, WFH, expenses, performance reviews).
    Use this tool when the user asks about any company policy or rule."""
    vs = _get_vs()
    results = vs.similarity_search(query, k=4)
    if not results:
        return "No relevant policy found."
    return "\n\n---\n\n".join(
        f"[Source: {doc.metadata.get('source', 'policy')}]\n{doc.page_content}"
        for doc in results
    )


# ── Tool 2: Employee DB ─────────────────────────────────────────────────────
@tool
def query_employee_database(sql: str) -> str:
    """Run a SQL query on the employee database.
    Table: employees(emp_id, name, department, designation, email, phone,
    date_of_joining, salary, manager, location, leave_balance, status).
    Use SELECT queries to look up employee information.
    NEVER use UPDATE, DELETE, or DROP statements."""
    sql_upper = sql.strip().upper()
    if any(kw in sql_upper for kw in ["UPDATE", "DELETE", "DROP", "INSERT", "ALTER"]):
        return "Error: Only SELECT queries are allowed."
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql)
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return "No results found."
        result_lines = []
        for row in rows:
            result_lines.append(
                " | ".join(f"{k}: {row[k]}" for k in row.keys())
            )
        return "\n".join(result_lines)
    except Exception as e:
        return f"Database error: {e}"


ALL_TOOLS = [search_hr_policies, query_employee_database]
