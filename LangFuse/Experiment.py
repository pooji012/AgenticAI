from datetime import datetime
from dotenv import load_dotenv

load_dotenv(".env")

from langfuse import Evaluation

from main import (
    run_agent,
    llm_judge,
    extract_resume_score,
    EXPECTED_TOOLS,
    langfuse,
)

DATASET_NAME = "resume-review-eval"


def task(*, item, **kwargs):
    """Run the agent on one dataset item. Output is consumed by evaluators."""
    resume_text = item.input["resume_text"]
    review, called = run_agent(resume_text)
    return {
        "review": review,
        "tools_called": sorted(called),
        "resume_text": resume_text,
    }


def eval_tools_completeness(*, input, output, expected_output, metadata, **kwargs):
    called = set(output["tools_called"])
    return Evaluation(
        name="tools_completeness",
        value=EXPECTED_TOOLS.issubset(called),
        data_type="BOOLEAN",
        comment=f"Called: {sorted(called)}",
    )


def eval_resume_score_in_range(*, input, output, expected_output, metadata, **kwargs):
    score = extract_resume_score(output["review"])
    if score is None:
        return Evaluation(
            name="score_in_expected_range",
            value=False,
            data_type="BOOLEAN",
            comment="no X/10 found",
        )

    expected = expected_output or {}
    lo = expected.get("expected_score_min", 0)
    hi = expected.get("expected_score_max", 10)
    in_range = lo <= score <= hi
    return Evaluation(
        name="score_in_expected_range",
        value=in_range,
        data_type="BOOLEAN",
        comment=f"score={score}, expected [{lo}, {hi}]",
    )


def eval_resume_score(*, input, output, expected_output, metadata, **kwargs):
    score = extract_resume_score(output["review"])
    if score is None:
        return []
    return Evaluation(
        name="resume_score",
        value=score,
        comment="X/10 from agent",
    )


def eval_judge(*, input, output, expected_output, metadata, **kwargs):
    verdict = llm_judge(output["resume_text"], output["review"])
    evaluations = []
    for criterion, result in verdict.model_dump().items():
        evaluations.append(Evaluation(
            name=f"judge_{criterion}",
            value=result["score"],
            comment=result["reason"],
        ))
    avg = sum(c["score"] for c in verdict.model_dump().values()) / 4
    evaluations.append(Evaluation(
        name="judge_overall",
        value=avg,
        comment="Mean of 4 judge criteria",
    ))
    return evaluations


def main():
    dataset = langfuse.get_dataset(DATASET_NAME)
    run_name = f"agent-eval-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    result = dataset.run_experiment(
        name="resume-review-agent-eval",
        run_name=run_name,
        description="Evaluate agent across varied resumes; checks tool use, score range, and LLM-judged quality.",
        task=task,
        evaluators=[
            eval_tools_completeness,
            eval_resume_score,
            eval_resume_score_in_range,
            eval_judge,
        ],
        max_concurrency=3,
    )

    print(result.format())
    print(f"\nDashboard: {result.dataset_run_url}")
    langfuse.flush()


if __name__ == "__main__":
    main()