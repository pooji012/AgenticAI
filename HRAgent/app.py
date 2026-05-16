"""Streamlit UI for the HR Agent."""
import streamlit as st
import uuid
import os
import sys

# Ensure the project directory is on the path
sys.path.insert(0, os.path.dirname(__file__))

from db_setup import init_db, DB_PATH

# Initialize database if it doesn't exist
if not os.path.exists(DB_PATH):
    init_db()

from agent import chat

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="HR Agent", page_icon="👥", layout="centered")

st.title("👥 HR Agent")
st.caption("Ask me about company policies, employee details, leave balances, and more.")

# ── Session state ────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("About")
    st.markdown(
        """
        This HR Agent can help you with:
        - **Leave Policy** — annual, sick, casual, maternity
        - **WFH Policy** — eligibility, days, core hours
        - **Expense Policy** — limits, submission, reimbursement
        - **Performance Reviews** — cycle, ratings, increments
        - **Employee Lookup** — salary, department, manager, leave balance
        """
    )
    st.divider()
    st.markdown("**Sample questions:**")
    st.markdown("- How many casual leaves do I get?")
    st.markdown("- What is Rahul Sharma's leave balance?")
    st.markdown("- Who works in the Engineering department?")
    st.markdown("- What is the WFH policy?")
    st.markdown("- What are the expense limits for hotels?")
    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

# ── Chat history ─────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── User input ───────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask your HR question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = chat(prompt, session_id=st.session_state.session_id)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
