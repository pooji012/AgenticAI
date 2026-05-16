"""Streamlit UI for the TechTrend customer support agent."""

import uuid

import streamlit as st
from dotenv import load_dotenv

from agent import (
    get_pending_tickets,
    get_user_history,
    resolve_ticket,
    run_customer_support_agent,
)

load_dotenv()

DEFAULT_USER_ID = "customer_001"

st.set_page_config(
    page_title="TechTrend Support Agent",
    page_icon=":telephone_receiver:",
    layout="wide",
)


def reset_conversation() -> None:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.chat_messages = []


if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "last_resolution" not in st.session_state:
    st.session_state.last_resolution = ""

st.title("TechTrend Innovations Customer Support")
st.caption("LangGraph agent with OpenAI, short-term memory, long-term memory, and human review.")

user_id = DEFAULT_USER_ID

left_col, right_col = st.columns([2, 1])

with left_col:
    header_col, action_col = st.columns([3, 1])
    with header_col:
        st.subheader("Customer Chat")
    with action_col:
        if st.button("Start New Conversation", use_container_width=True):
            reset_conversation()
            st.rerun()

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a support question"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Checking support history..."):
                try:
                    result = run_customer_support_agent(
                        user_message=prompt,
                        user_id=user_id,
                        thread_id=st.session_state.thread_id,
                        api_key=None,
                    )
                    response = result["response"]
                    st.markdown(response)
                    if result.get("ticket_id"):
                        st.info(f"Escalated to human review: `{result['ticket_id']}`")
                except Exception as exc:
                    response = f"Error: {exc}"
                    st.error(response)

        st.session_state.chat_messages.append({"role": "assistant", "content": response})

with right_col:
    st.subheader("Long-Term Memory")
    history = get_user_history(user_id)
    if history:
        for item in reversed(history[-5:]):
            st.markdown(
                f"**{item['status']}**  \n"
                f"{item['timestamp']}  \n"
                f"Issue: {item['issue']}  \n"
                f"Outcome: {item['outcome']}"
            )
    else:
        st.caption("No customer history yet.")

    st.divider()
    st.subheader("Human Review Queue")
    tickets = get_pending_tickets(user_id)
    if tickets:
        ticket_map = {ticket["ticket_id"]: ticket for ticket in tickets}
        selected_ticket_id = st.selectbox("Pending tickets", list(ticket_map.keys()))
        selected_ticket = ticket_map[selected_ticket_id]

        st.markdown(f"**Reason:** {selected_ticket['reason']}")
        st.markdown(f"**Issue:** {selected_ticket['issue']}")

        human_response = st.text_area(
            "Approved human response",
            placeholder="Write the response a human support agent approves.",
            key=f"human_response_{selected_ticket_id}",
        )

        if st.button("Approve and Resolve", type="primary"):
            if not human_response.strip():
                st.warning("Enter a response before resolving the ticket.")
            else:
                resolved = resolve_ticket(selected_ticket_id, human_response.strip())
                st.session_state.last_resolution = (
                    f"{resolved['ticket_id']} resolved: {resolved['human_response']}"
                )
                st.success("Ticket resolved.")
                st.rerun()
    else:
        st.caption("No pending tickets.")

    if st.session_state.last_resolution:
        st.divider()
        st.subheader("Latest Resolution")
        st.write(st.session_state.last_resolution)
