# AI-Powered Content Creation Agent

This project is created for the **Module 07 Multi-Agent Systems assignment**.

The goal of this project is to build a simple AI system for a digital marketing
company called **Innovate Marketing Solutions**. The system uses multiple AI
agents to create marketing content with less manual work.

The project is built using **CrewAI**.

## What This Project Does

This application creates marketing content such as:

- Blog posts
- Social media posts
- Website copy

The user gives a topic, audience, content type, and tone. Then the agents work
together to research the topic, write the content, improve it for SEO, and review
the final result.

The final content is saved in:

```text
outputs/final_content.txt
```

## Assignment Scenario

Innovate Marketing Solutions is a digital marketing company. The company creates
content and SEO material for technology startups.

The company has a problem: it needs to create a large amount of good quality
content quickly. Manual research, writing, and SEO optimization can take a lot of
time.

This project solves that problem by using a multi-agent AI system. Each agent has
a separate job in the content creation process.

## Agents Used In This Project

This project uses four agents.

## 1. Topic Researcher

**Role:** Topic Researcher

**Goal:** Research the topic and prepare useful notes for writing.

**Backstory:** This agent works like a marketing researcher. It understands
technology startups, customer needs, and SEO keywords.

**Main duties:**

- Understand the given topic
- Find audience pain points
- Suggest keyword ideas
- Suggest content angles
- Prepare a research brief

**Output:** A research brief.

## 2. Content Writer

**Role:** Content Writer

**Goal:** Write the first draft of the content.

**Backstory:** This agent works like a professional marketing writer. It writes
clear, useful, and original content for business audiences.

**Main duties:**

- Use the research brief
- Write the first draft
- Match the selected tone
- Write for the selected audience
- Create blog posts, social media posts, or website copy

**Output:** First draft of the content.

## 3. SEO Specialist

**Role:** SEO Specialist

**Goal:** Improve the content for search engines.

**Backstory:** This agent works like an SEO expert. It improves the content while
keeping it natural and easy to read.

**Main duties:**

- Add SEO title
- Add meta description
- Suggest URL slug
- Select primary and secondary keywords
- Improve headings and keyword placement

**Output:** SEO-optimized content.

## 4. Quality Reviewer

**Role:** Quality Reviewer

**Goal:** Check the final quality of the content.

**Backstory:** This agent works like a senior editor. It checks whether the
content is clear, useful, relevant, and ready for the client.

**Main duties:**

- Check relevance
- Check quality
- Check clarity
- Check tone
- Check for unsupported claims or bias
- Give final evaluation scores

**Output:** Final polished content with quality scores.

## Workflow

The agents work in this order:

1. The user gives a topic.
2. The Topic Researcher prepares a research brief.
3. The Content Writer writes the first draft.
4. The SEO Specialist improves the draft for SEO.
5. The Quality Reviewer checks and finalizes the content.
6. The final result is saved as a text file.

This is a **sequential workflow**, which means each agent completes its work
before the next agent starts.

## Files In This Project

```text
contentCreationAgent/
|
|-- main.py
|-- requirements.txt
|-- .env.example
|-- activate-crewai.ps1
|-- README.md
`-- outputs/
    `-- sample_content.txt
```

### File Explanation

**main.py**  
Main Python file. It contains the CrewAI agents, tasks, workflow, and output
saving logic.

**requirements.txt**  
Lists the Python packages needed for this project.

**.env.example**  
Shows the environment variables needed to run the project.

**activate-crewai.ps1**  
PowerShell helper file to activate the virtual environment and keep CrewAI
runtime files inside this project folder.

**outputs/sample_content.txt**  
Example content output for assignment reference.

## Setup Steps

Use **Python 3.12** for this project.

Do not use Python 3.14 for CrewAI right now. Some dependencies, such as `numpy`,
may fail to install because they try to build from source.

Open PowerShell in the project folder and run:

```powershell
cd contentCreationAgent
& "C:\Users\sarat\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\activate-crewai.ps1
pip install -r requirements.txt
```

If the `.venv` folder was already created with Python 3.14, delete it first and
create it again using Python 3.12:

```powershell
Remove-Item .venv -Recurse -Force
& "C:\Users\sarat\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\activate-crewai.ps1
pip install -r requirements.txt
```

## Environment Setup

Create a new file named `.env` inside the `contentCreationAgent` folder.

You can copy the values from `.env.example`:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
CREWAI_TRACING_ENABLED=false
```

Replace `your_openai_api_key_here` with your actual API key.

## How To Run

To run in interactive mode:

```powershell
python main.py
```

The program will ask:

- What topic should the agents research?
- Who is the target audience?
- What content type should be created?
- What tone should the content use?

To skip the questions and pass values directly:

```powershell
python main.py --topic "AI chatbots for ecommerce customer support" --audience "ecommerce founders" --content-type "blog post" --tone "friendly and expert"
```

To use all default values without questions:

```powershell
python main.py --no-interactive
```

## Input Options

You can change:

- `--topic`
- `--audience`
- `--content-type`
- `--tone`
- `--no-interactive`

Allowed content types are:

- `blog post`
- `social media post`
- `website copy`

## Example Command

```powershell
python main.py --topic "AI tools for small business marketing" --audience "startup founders" --content-type "blog post" --tone "professional and helpful"
```

## Output

After running the program, the final content will be saved in:

```text
outputs/final_content.txt
```

The output file includes:

- Topic details
- SEO title
- Meta description
- Suggested URL slug
- Primary keyword
- Secondary keywords
- Final content
- Relevance score
- Quality score

## Tools Used

This project uses:

- **Python** for programming
- **CrewAI** for multi-agent workflow
- **OpenAI model** through CrewAI's `LLM` class
- **python-dotenv** for loading the API key

## Testing And Evaluation

The final agent, Quality Reviewer, evaluates the content based on:

- Relevance
- Quality
- Clarity
- Tone match
- SEO readiness
- Bias or unsupported claims

The output includes simple scores such as:

```text
Relevance: 9/10
Quality: 8/10
```

## Future Improvements

This project can be improved by adding:

- Live search using DuckDuckGo or Google Search API
- Keyword research using SerpAPI
- SEO checking using an SEO API
- Human editor feedback
- More content formats

## Summary

This project meets the assignment requirement by creating a CrewAI-based
multi-agent system for marketing content creation.

It includes agent definitions, task design, workflow execution, SEO optimization,
quality review, and text file output.
