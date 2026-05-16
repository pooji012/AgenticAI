# Customer Support Triage Agent

This folder contains the Module 06 assignment implementation for an e-commerce
Customer Support Triage Agent.

## What It Does

- Uploads `.csv`, `.txt`, and `.pdf` files
- Extracts support tickets and policy text
- Chunks uploaded content
- Stores chunks in a local searchable knowledge base
- Detects ticket intent, sentiment, urgency, topic, and routing team
- Suggests editable support replies
- Supports semantic-style search over uploaded complaints and policies
- Provides a supervisor chat interface for summaries and trends

## Setup

```powershell
cd supportAgent
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Optional `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

The app still works without an API key using local triage rules and local search.

## Run

```powershell
streamlit run app.py
```

#Tested with assignment dataset 
these are columns in .CSV folder
Ticket ID	
Customer Name	
Customer Email	
Customer Age	
Customer Gender
Product Purchased	
Date of Purchase	
Ticket Type	
Ticket Subject	
Ticket Description	
Ticket Status	
Resolution	
Ticket Priority	
Ticket Channel	
First Response Time	
Time to Resolution	
Customer Satisfaction Rating
