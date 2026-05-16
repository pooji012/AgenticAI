from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv(".env")

langfuse = Langfuse()

DATASET_NAME = "resume-review-eval"

ITEMS = [
    {
        "id": "resume-strong-senior",
        "input": {
            "resume_text": """
Sarah Chen
sarah.chen@email.com | linkedin.com/in/sarahchen | github.com/schen | +1-555-0142

SUMMARY
Senior backend engineer with 8 years of experience scaling distributed systems.
Led a team of 6 engineers at FinTechCo, reduced infrastructure costs by 38%.

EXPERIENCE
Staff Engineer - FinTechCo (2020 - Present)
- Designed event-driven payment pipeline processing 12M txns/day
- Migrated monolith to microservices, cut p99 latency from 800ms to 120ms
- Mentored 4 junior engineers; 2 promoted to senior in 18 months

Senior Backend Engineer - DataCorp (2017 - 2020)
- Built real-time analytics platform on Kafka + ClickHouse
- Open-sourced rate-limiting library (3.2k GitHub stars)

EDUCATION
M.S. Computer Science - Carnegie Mellon (2017)
B.S. Computer Science - UC Berkeley (2015)

SKILLS
Go, Python, Rust, Kafka, Kubernetes, PostgreSQL, AWS, system design
"""
        },
        "expected_output": {
            "expected_score_min": 8.5,
            "expected_strengths": ["quantified impact", "leadership", "scale"],
        },
    },
    {
        "id": "resume-mid-level",
        "input": {
            "resume_text": """
John Doe
john.doe@email.com | LinkedIn: linkedin.com/in/johndoe | +1-555-0100

SUMMARY
Software engineer with 3 years of experience in Python and web development.

EXPERIENCE
Software Engineer - TechCorp (2022 - Present)
- Built REST APIs using FastAPI and PostgreSQL
- Reduced API response time by 40% through caching

Junior Developer - StartupXYZ (2021 - 2022)
- Developed React frontend components
- Wrote unit tests with pytest

EDUCATION
B.Sc. Computer Science - State University (2021)

SKILLS
Python, FastAPI, React, PostgreSQL, Git, Docker
"""
        },
        "expected_output": {
            "expected_score_min": 6.0,
            "expected_score_max": 8.0,
            "expected_strengths": ["quantified results"],
        },
    },
    {
        "id": "resume-weak-junior",
        "input": {
            "resume_text": """
Mike Smith
mike@email.com

I am a hardworking developer looking for opportunities. I am a fast learner
and a team player.

EXPERIENCE
Worked at a company - 2023
- Did some coding
- Helped with projects

Internship - 2022
- Wrote some code
- Used computers

SKILLS
Programming, Computers, Microsoft Office
"""
        },
        "expected_output": {
            "expected_score_max": 4.5,
            "expected_improvements": ["specifics", "quantified impact", "concrete tech"],
        },
    },
    {
        "id": "resume-missing-sections",
        "input": {
            "resume_text": """
Alice Wong
alice.wong@email.com

EXPERIENCE
ML Engineer - AcmeAI (2021 - Present)
- Trained recommendation models
- Improved CTR by 15%

ML Engineer Intern - BigTech (2020)
- Worked on NLP pipeline
"""
        },
        "expected_output": {
            "expected_score_max": 6.5,
            "expected_improvements": ["add education", "add skills section", "more detail"],
        },
    },
]


def seed():
    try:
        langfuse.create_dataset(
            name=DATASET_NAME,
            description="Sample resumes spanning strong/mid/weak/incomplete for agent eval",
        )
        print(f"[create] dataset '{DATASET_NAME}'")
    except Exception as e:
        print(f"[exists] dataset '{DATASET_NAME}' ({e.__class__.__name__})")

    for item in ITEMS:
        langfuse.create_dataset_item(
            dataset_name=DATASET_NAME,
            id=item["id"],
            input=item["input"],
            expected_output=item["expected_output"],
        )
        print(f"[upsert] {item['id']}")


if __name__ == "__main__":
    seed()
    langfuse.flush()
    print("\nDone.")