import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import AIMessage
from langchain.agents import create_agent as create_react_agent
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from pydantic import BaseModel, Field

load_dotenv(".env")

langfuse = Langfuse()
langfuse_handler = CallbackHandler()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

EXPECTED_TOOLS = {"score_resume", "identify_strengths", "suggest_improvements"}


class JudgeCriterion(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    reason: str


class JudgeVerdict(BaseModel):
    relevance: JudgeCriterion
    specificity: JudgeCriterion
    actionability: JudgeCriterion
    coverage: JudgeCriterion


def render(name: str, **vars) -> str:
    return langfuse.get_prompt(name, label="production").compile(**vars)


@tool
def score_resume(resume_text: str) -> str:
    """Score a resume out of 10 based on clarity, structure, and completeness."""
    return llm.invoke(render("resume-review/score", resume_text=resume_text)).content


@tool
def identify_strengths(resume_text: str) -> str:
    """Identify the top 3 strengths in the resume."""
    return llm.invoke(render("resume-review/strengths", resume_text=resume_text)).content


@tool
def suggest_improvements(resume_text: str) -> str:
    """Suggest the top 3 improvements for the resume."""
    return llm.invoke(render("resume-review/improvements", resume_text=resume_text)).content


tools = [score_resume, identify_strengths, suggest_improvements]

agent = None


def get_agent():
    global agent
    if agent is None:
        agent = create_react_agent(
            llm,
            tools,
            system_prompt=langfuse.get_prompt(
                "resume-review/system", label="production"
            ).prompt,
        )
    return agent


def extract_resume_score(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", text)
    return float(match.group(1)) if match else None


def tools_called(messages) -> set[str]:
    called = set()
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                called.add(tc["name"])
    return called


def judge_quality(resume_text: str, review: str) -> float | None:
    raw = llm.invoke(
        render("resume-review/judge", resume_text=resume_text, review=review)
    ).content
    match = re.search(r"\d+(?:\.\d+)?", raw)
    if not match:
        return None
    return max(0.0, min(1.0, float(match.group(0))))


def llm_judge(resume_text: str, review: str) -> JudgeVerdict:
    judge = llm.with_structured_output(JudgeVerdict)
    return judge.invoke(
        render("resume-review/judge", resume_text=resume_text, review=review)
    )


def score_run(trace_id: str, messages, final_output: str, resume_text: str):
    resume_score = extract_resume_score(final_output)
    if resume_score is not None:
        langfuse.create_score(
            trace_id=trace_id,
            name="resume_score",
            value=resume_score,
            data_type="NUMERIC",
            comment="Score (X/10) extracted from agent output",
        )

    called = tools_called(messages)
    complete = EXPECTED_TOOLS.issubset(called)
    langfuse.create_score(
        trace_id=trace_id,
        name="tools_completeness",
        value=complete,
        data_type="BOOLEAN",
        comment=f"Called: {sorted(called)}; expected: {sorted(EXPECTED_TOOLS)}",
    )

    try:
        verdict = llm_judge(resume_text, final_output)
        verdict_data = verdict.model_dump()
        quality = sum(
            criterion["score"] for criterion in verdict_data.values()
        ) / len(verdict_data)
        langfuse.create_score(
            trace_id=trace_id,
            name="review_quality",
            value=quality,
            data_type="NUMERIC",
            comment="LLM-as-judge rating (0.0-1.0) on specificity, actionability, coverage",
        )
    except Exception:
        quality = judge_quality(resume_text, final_output)
        if quality is not None:
            langfuse.create_score(
                trace_id=trace_id,
                name="review_quality",
                value=quality,
                data_type="NUMERIC",
                comment="LLM-as-judge rating (0.0-1.0) on specificity, actionability, coverage",
            )


def run_agent(resume_text: str) -> tuple[str, set[str]]:
    result = get_agent().invoke(
        {"messages": [("human", f"Please review this resume:\n\n{resume_text}")]},
        config={"callbacks": [langfuse_handler]},
    )
    final_output = result["messages"][-1].content
    called = tools_called(result["messages"])
    trace_id = langfuse_handler.last_trace_id
    if trace_id:
        score_run(trace_id, result["messages"], final_output, resume_text)
    langfuse.flush()
    return final_output, called


def review_resume(resume_text: str) -> str:
    final_output, _ = run_agent(resume_text)
    return final_output


if __name__ == "__main__":
    sample_resume = """
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

    print("=== Resume Review Agent ===\n")
    review = review_resume(sample_resume)
    print("\n=== Final Review ===")
    print(review)
