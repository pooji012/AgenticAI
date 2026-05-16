from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import DATA_DIR, OUTPUT_DIR
from src.pipeline import run_pipeline


st.set_page_config(page_title="Feedback AI Agent System", layout="wide")

st.markdown(
    """
    <style>
      div[data-testid="stSegmentedControl"] {
        background: #ffffff;
        border: 2px solid #b8c7dc;
        border-radius: 8px;
        padding: 12px 18px;
        margin: 4px 0 24px 0;
        box-shadow: 0 2px 8px rgba(23, 32, 51, 0.08);
      }
      div[data-testid="stSegmentedControl"] > label {
        display: none;
      }
      div[data-testid="stSegmentedControl"] div[role="radiogroup"] {
        justify-content: center;
        gap: 18px;
      }
      div[data-testid="stSegmentedControl"] button {
        font-weight: 700;
        min-width: 150px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

APP_REVIEW_COLUMNS = {"review_id", "platform", "rating", "review_text", "user_name", "date", "app_version"}
SUPPORT_EMAIL_COLUMNS = {"email_id", "subject", "body", "sender_email", "timestamp", "priority"}


def save_uploaded_csv(uploaded_file, destination: Path, required_columns: set[str]) -> tuple[bool, str]:
    if uploaded_file is None:
        return False, "No file uploaded."

    try:
        uploaded_file.seek(0)
        dataframe = pd.read_csv(uploaded_file)
    except Exception as exc:
        return False, f"Could not read CSV: {exc}"

    missing_columns = sorted(required_columns - set(dataframe.columns))
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(destination, index=False)
    return True, f"Saved {len(dataframe)} rows to {destination.name}."


with st.sidebar:
    st.header("Controls")
    st.subheader("Upload Input CSVs")
    app_reviews_upload = st.file_uploader(
        "App Store Reviews CSV",
        type=["csv"],
        help="Required columns: review_id, platform, rating, review_text, user_name, date, app_version",
    )
    support_emails_upload = st.file_uploader(
        "Support Emails CSV",
        type=["csv"],
        help="Required columns: email_id, subject, body, sender_email, timestamp, priority",
    )
    upload_clicked = st.button("Save Uploaded CSVs")
    run_clicked = st.button("Run AutoGen Agent Pipeline", type="primary")
    st.caption("Architecture: CSV Reader -> Classifier -> Bug/Feature Agents -> Ticket Creator -> Quality Critic")

if upload_clicked:
    reviews_ok, reviews_message = save_uploaded_csv(
        app_reviews_upload,
        DATA_DIR / "app_store_reviews.csv",
        APP_REVIEW_COLUMNS,
    )
    emails_ok, emails_message = save_uploaded_csv(
        support_emails_upload,
        DATA_DIR / "support_emails.csv",
        SUPPORT_EMAIL_COLUMNS,
    )

    if reviews_ok:
        st.success(reviews_message)
    else:
        st.error(f"App Store Reviews CSV: {reviews_message}")

    if emails_ok:
        st.success(emails_message)
    else:
        st.error(f"Support Emails CSV: {emails_message}")

if run_clicked:
    missing_inputs = [
        filename
        for filename in ("app_store_reviews.csv", "support_emails.csv")
        if not (DATA_DIR / filename).exists()
    ]
    if missing_inputs:
        st.error(f"Missing input file(s): {', '.join(missing_inputs)}. Upload the CSV files first.")
    else:
        with st.spinner("Agents are processing feedback..."):
            result = run_pipeline()
        st.success(f"Generated {len(result['tickets'])} tickets.")


def read_output(name: str) -> pd.DataFrame:
    path = OUTPUT_DIR / name
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def count_table(dataframe: pd.DataFrame, column: str, label: str) -> pd.DataFrame:
    return (
        dataframe[column]
        .fillna("Unknown")
        .value_counts()
        .rename_axis(label)
        .reset_index(name="Count")
    )


tickets = read_output("generated_tickets.csv")
logs = read_output("processing_log.csv")
metrics = read_output("metrics.csv")
selected_menu = st.segmented_control(
    "Menu",
    ["Dashboard", "Manual Override", "Processing Log", "Analytics"],
    default="Dashboard",
    label_visibility="collapsed",
)

if tickets.empty:
    st.info("Run the pipeline to generate tickets and metrics.")
else:
    metric_map = dict(zip(metrics["metric"], metrics["value"])) if not metrics.empty else {}

    if selected_menu == "Dashboard":
        metric_cols = st.columns(4)
        metric_cols[0].metric("Processed", metric_map.get("processed_feedback", len(tickets)))
        metric_cols[1].metric("Approved", metric_map.get("approved_tickets", 0))
        metric_cols[2].metric("Manual Review", metric_map.get("needs_manual_review", 0))
        metric_cols[3].metric("Accuracy", metric_map.get("classification_accuracy", "N/A"))

        st.subheader("Generated Tickets")
        st.dataframe(tickets, use_container_width=True, hide_index=True)

    elif selected_menu == "Manual Override":
        st.subheader("Edit or Approve Tickets")
        editable = st.data_editor(
            tickets,
            use_container_width=True,
            hide_index=True,
            column_config={
                "priority": st.column_config.SelectboxColumn("priority", options=["Critical", "High", "Medium", "Low"]),
                "status": st.column_config.SelectboxColumn("status", options=["Approved", "Pending Review", "Needs Manual Review"]),
            },
        )
        if st.button("Save Manual Overrides"):
            OUTPUT_DIR.mkdir(exist_ok=True)
            editable.to_csv(OUTPUT_DIR / "generated_tickets.csv", index=False)
            st.success("Manual overrides saved to outputs/generated_tickets.csv")

    elif selected_menu == "Processing Log":
        st.subheader("Agent Processing History")
        st.dataframe(logs, use_container_width=True, hide_index=True)

    elif selected_menu == "Analytics":
        st.subheader("Feedback Analysis")

        total_tickets = len(tickets)
        average_confidence = round(tickets["confidence"].mean(), 2) if "confidence" in tickets else 0
        average_quality = round(tickets["quality_score"].mean(), 2) if "quality_score" in tickets else 0
        critical_high = tickets[tickets["priority"].isin(["Critical", "High"])].shape[0]

        summary_cols = st.columns(4)
        summary_cols[0].metric("Total Tickets", total_tickets)
        summary_cols[1].metric("Critical / High", critical_high)
        summary_cols[2].metric("Avg Confidence", average_confidence)
        summary_cols[3].metric("Avg Quality", average_quality)

        left, right = st.columns(2)
        with left:
            st.subheader("Tickets by Category")
            category_counts = count_table(tickets, "category", "Category")
            st.bar_chart(category_counts, x="Category", y="Count")
        with right:
            st.subheader("Tickets by Priority")
            priority_counts = count_table(tickets, "priority", "Priority")
            st.bar_chart(priority_counts, x="Priority", y="Count")

        left, right = st.columns(2)
        with left:
            st.subheader("Tickets by Source")
            source_counts = count_table(tickets, "source_type", "Source")
            st.bar_chart(source_counts, x="Source", y="Count")
        with right:
            st.subheader("Tickets by Status")
            status_counts = count_table(tickets, "status", "Status")
            st.bar_chart(status_counts, x="Status", y="Count")

        left, right = st.columns(2)
        with left:
            st.subheader("Average Confidence by Category")
            confidence_by_category = (
                tickets.groupby("category", as_index=False)["confidence"]
                .mean()
                .rename(columns={"category": "Category", "confidence": "Average Confidence"})
            )
            st.bar_chart(confidence_by_category, x="Category", y="Average Confidence")
        with right:
            st.subheader("Average Quality Score by Priority")
            quality_by_priority = (
                tickets.groupby("priority", as_index=False)["quality_score"]
                .mean()
                .rename(columns={"priority": "Priority", "quality_score": "Average Quality Score"})
            )
            st.bar_chart(quality_by_priority, x="Priority", y="Average Quality Score")

        st.subheader("Category and Priority Analysis")
        category_priority = pd.crosstab(tickets["category"], tickets["priority"])
        st.dataframe(category_priority, use_container_width=True)
