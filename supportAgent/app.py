"""Streamlit UI for the Customer Support Triage Agent assignment."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from support_triage_agent import SupportTriageAgent

load_dotenv()

st.set_page_config(
    page_title="Support Triage Agent",
    page_icon=":headphones:",
    layout="wide",
)


@st.cache_resource
def get_agent() -> SupportTriageAgent:
    return SupportTriageAgent()


def init_state() -> None:
    defaults = {
        "processed_files": [],
        "tickets": [],
        "triage_df": pd.DataFrame(),
        "chat_messages": [],
        "selected_draft": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


agent = get_agent()
init_state()

st.title("Customer Support Triage Agent")
st.caption("Agno-style triage workflow: upload logs and policies, analyze tickets, search context, and draft replies.")

with st.sidebar:
    st.header("Knowledge Base")
    uploaded_files = st.file_uploader(
        "Upload support logs or policy documents",
        type=["csv", "txt", "pdf"],
        accept_multiple_files=True,
    )

    if st.button("Process Uploads", type="primary", use_container_width=True):
        if not uploaded_files:
            st.warning("Upload at least one CSV, TXT, or PDF file.")
        else:
            all_tickets = []
            summaries = []
            with st.spinner("Reading files and building searchable chunks..."):
                for uploaded_file in uploaded_files:
                    result = agent.ingest_uploaded_file(
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                    )
                    summaries.append(result)
                    all_tickets.extend(result["tickets"])

            st.session_state.processed_files.extend(summaries)
            st.session_state.tickets.extend(all_tickets)

            if all_tickets:
                new_df = agent.analyze_tickets(all_tickets)
                st.session_state.triage_df = pd.concat(
                    [st.session_state.triage_df, new_df],
                    ignore_index=True,
                )

            st.success("Files processed.")

    if st.button("Clear Local Knowledge", use_container_width=True):
        agent.clear_knowledge()
        st.session_state.processed_files = []
        st.session_state.tickets = []
        st.session_state.triage_df = pd.DataFrame()
        st.session_state.chat_messages = []
        st.session_state.selected_draft = ""
        st.success("Local knowledge cleared.")

    if st.session_state.processed_files:
        st.divider()
        st.subheader("Processed Files")
        for item in st.session_state.processed_files[-8:]:
            st.write(
                f"{item['file_name']} - {item['chunks_added']} chunks, "
                f"{item['tickets_found']} tickets"
            )

dashboard_tab, triage_tab, chat_tab, search_tab = st.tabs(
    ["Dashboard", "Ticket Triage", "Supervisor Chat", "Semantic Search"]
)

with dashboard_tab:
    st.subheader("Summary Dashboard")
    triage_df = st.session_state.triage_df

    if triage_df.empty:
        st.info("Upload a CSV or TXT support log to see ticket analytics.")
    else:
        metric_cols = st.columns(4)
        metric_cols[0].metric("Tickets", len(triage_df))
        metric_cols[1].metric("Escalations", int(triage_df["escalation_needed"].sum()))
        metric_cols[2].metric("Negative", int((triage_df["sentiment"] == "negative").sum()))
        metric_cols[3].metric("High Urgency", int((triage_df["urgency"] == "high").sum()))

        left, right = st.columns(2)
        with left:
            st.markdown("**Complaint Types**")
            st.bar_chart(triage_df["intent"].value_counts())
        with right:
            st.markdown("**Urgency Levels**")
            st.bar_chart(triage_df["urgency"].value_counts())

        st.markdown("**Recent Triage Results**")
        st.dataframe(
            triage_df[
                [
                    "ticket_id",
                    "timestamp",
                    "intent",
                    "sentiment",
                    "urgency",
                    "route_to",
                    "escalation_needed",
                ]
            ],
            use_container_width=True,
        )

with triage_tab:
    st.subheader("Analyze One Customer Ticket")
    issue = st.text_area(
        "Customer issue",
        placeholder="Example: My order is delayed and I need a refund immediately.",
        height=140,
    )
    if st.button("Triage Ticket", type="primary"):
        if not issue.strip():
            st.warning("Enter a customer issue first.")
        else:
            result = agent.triage_ticket(issue)
            st.session_state.selected_draft = result.draft_response
            st.success(f"Ticket created: {result.ticket_id}")
            cols = st.columns(5)
            cols[0].metric("Intent", result.intent)
            cols[1].metric("Sentiment", result.sentiment)
            cols[2].metric("Urgency", result.urgency)
            cols[3].metric("Route", result.route_to)
            cols[4].metric("Escalate", "Yes" if result.escalation_needed else "No")

    st.markdown("**Editable Draft Response**")
    st.session_state.selected_draft = st.text_area(
        "Draft",
        value=st.session_state.selected_draft,
        height=160,
        label_visibility="collapsed",
    )

with chat_tab:
    st.subheader("Ask About Trends, Complaints, Or Policies")

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask: What are the top 3 customer pain points this month?"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching uploaded support context..."):
                answer = agent.answer_query(prompt)
            st.markdown(answer)

        st.session_state.chat_messages.append({"role": "assistant", "content": answer})

with search_tab:
    st.subheader("Semantic Search")
    query = st.text_input(
        "Search uploaded tickets and policy chunks",
        placeholder="Find refund issues with negative sentiment",
    )
    top_k = st.slider("Results", min_value=1, max_value=10, value=5)

    if st.button("Search"):
        if not query.strip():
            st.warning("Enter a search query.")
        else:
            results = agent.search(query, top_k=top_k)
            if not results:
                st.info("No matching chunks found yet.")
            for item in results:
                with st.expander(
                    f"{item.get('source')} | {item.get('kind')} | score {item.get('score')}",
                    expanded=True,
                ):
                    st.write(item.get("text", ""))
                    st.caption(f"Metadata: {item.get('metadata', {})}")
