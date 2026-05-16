# Intelligent User Feedback Analysis and Action System

This project is an AutoGen-style multi-agent AI system for analyzing user feedback from app store reviews and support emails. It reads CSV files, classifies feedback, extracts useful details, creates structured tickets, reviews ticket quality, stores results, and provides a Streamlit dashboard for monitoring and manual overrides.

## Project Architecture

The system follows this agent workflow:

1. CSV Reader Agent reads feedback from CSV files.
2. Feedback Classifier Agent classifies each item as Bug, Feature Request, Praise, Complaint, or Spam.
3. Bug Analyzer Agent extracts technical details for bug reports.
4. Feature Extractor Agent extracts requested features and user impact.
5. Ticket Creator Agent creates structured tickets.
6. Quality Critic Agent reviews tickets for completeness and consistency.
7. Streamlit UI displays tickets, logs, metrics, analytics, and manual override controls.

Storage and output components:

- ChromaDB vector store: stores feedback, ticket, and product documentation embeddings.
- SQLite database: stores processed feedback and generated tickets.
- CSV output files: stores final ticket, processing log, and metrics files.

## Folder Structure

```text
FinalAgenticAIProject/
  app.py
  run_pipeline.py
  requirements.txt
  README.md
  .env
  data/
    app_store_reviews.csv
    support_emails.csv
    expected_classifications.csv
    product_docs.md
  outputs/
    generated_tickets.csv
    processing_log.csv
    metrics.csv
  src/
    agents.py
    config.py
    models.py
    pipeline.py
    storage.py
    vector_store.py
  storage/
    feedback_system.db
    chroma/
```

## Installation Steps

Open PowerShell and go to the project folder:

```powershell
cd "C:\Users\sarat\OneDrive\Desktop\Pooji work\Project\FinalAgenticAIProject"
```

Optional but recommended: create a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install all required packages:

```powershell
pip install -r requirements.txt
```

If AutoGen is not installed correctly, install it directly:

```powershell
pip install pyautogen autogen-agentchat
```

## Environment File Setup

Create or open the `.env` file in the project root:

```text
FinalAgenticAIProject/.env
```

Add your OpenAI API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```


Important:

- Do not share your `.env` file publicly.
- Do not commit real API keys to GitHub.
- The current implementation can run locally without an API key because it uses deterministic classification logic for repeatable demo results.
- The `.env` setup is included so the project can be extended to use live OpenAI model calls through AutoGen.

## Step 1: Prepare Input Data

The project already includes sample CSV files:

```text
data/app_store_reviews.csv
data/support_emails.csv
data/expected_classifications.csv
data/product_docs.md
```

You can edit these files to add more reviews, support emails, or expected classifications.

## Step 2: Run the Agent Pipeline

Run:

```powershell
python run_pipeline.py
```

This command performs the full workflow:

1. Loads app store reviews and support emails.
2. Loads product documentation into ChromaDB.
3. Classifies each feedback item.
4. Sends bugs to the Bug Analyzer Agent.
5. Sends feature requests to the Feature Extractor Agent.
6. Creates structured tickets.
7. Reviews tickets using the Quality Critic Agent.
8. Saves data to SQLite, ChromaDB, and CSV files.

Expected terminal output:

```text
Pipeline completed.
Tickets generated: 18
Output files written to outputs/
```

## Step 3: Check Generated Output Files

After running the pipeline, check these files:

```text
outputs/generated_tickets.csv
outputs/processing_log.csv
outputs/metrics.csv
```

Output descriptions:

- `generated_tickets.csv`: final structured ticket list.
- `processing_log.csv`: agent decision history and processing steps.
- `metrics.csv`: processed count, approved tickets, manual review count, accuracy, and quality score.

## Step 4: Run the Streamlit Dashboard

Run:

```powershell
streamlit run app.py
```

Then open this URL in your browser:

```text
http://localhost:8501
```

Dashboard features:

- Run the AutoGen agent pipeline.
- View generated tickets.
- Edit ticket category, priority, status, and details.
- Save manual overrides.
- View processing logs.
- View category and priority analytics.
- View the activity diagram.

## Step 5: Manual Override Workflow

In the Streamlit dashboard:

1. Open the Manual Override tab.
2. Edit ticket fields if needed.
3. Change status to Approved or Needs Manual Review.
4. Click Save Manual Overrides.
5. Updated tickets are saved to:

```text
outputs/generated_tickets.csv
```

## Step 6: Demo and Testing Checklist

Use this checklist while presenting the capstone:

1. Show input CSV files in the `data/` folder.
2. Run `python run_pipeline.py`.
3. Open `outputs/generated_tickets.csv`.
4. Open `outputs/processing_log.csv`.
5. Open `outputs/metrics.csv`.
6. Run `streamlit run app.py`.
7. Show dashboard metrics.
8. Show manual override editing.
9. Explain ChromaDB vector storage and SQLite persistence.
10. Explain each agent responsibility.

## Verify the Code

Run a compile check:

```powershell
python -m compileall src app.py run_pipeline.py
```

Run the pipeline again:

```powershell
python run_pipeline.py
```

## Troubleshooting

If `streamlit` is not recognized:

```powershell
python -m streamlit run app.py
```

If packages are missing:

```powershell
pip install -r requirements.txt
```

If ChromaDB or SQLite files need to be regenerated, delete the `storage/` folder and run:

```powershell
python run_pipeline.py
```

If output files are missing, run:

```powershell
python run_pipeline.py
```

## Notes About AutoGen

The project imports AutoGen's `AssistantAgent` class and maps every workflow step to an agent profile. The current pipeline uses deterministic local logic so the capstone demo is stable and does not fail because of API limits or missing keys. The `.env` file is prepared for adding real OpenAI-powered AutoGen calls later.
