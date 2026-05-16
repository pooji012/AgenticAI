from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv(".env")

langfuse = Langfuse()


PROMPTS = {
    "resume-review/system": """You are an expert HR resume reviewer. When given a resume, you must:
1. Score it using the score_resume tool
2. Identify strengths using the identify_strengths tool
3. Suggest improvements using the suggest_improvements tool
4. Provide a final summary combining all findings.""",

    "resume-review/score": """Score the following resume out of 10. Consider:
- Clarity and writing quality
- Structure and formatting
- Completeness (contact info, experience, skills, education)

Resume:
{{resume_text}}

Respond with: Score: X/10 followed by brief reasoning.""",

    "resume-review/strengths": """Identify the top 3 strengths in this resume. Be specific.

Resume:
{{resume_text}}

List them as:
1. ...
2. ...
3. ...""",

    "resume-review/improvements": """Suggest the top 3 improvements for this resume. Be actionable and specific.

Resume:
{{resume_text}}

List them as:
1. ...
2. ...
3. ...""",

    "resume-review/judge": """You are an impartial evaluator grading the quality of a resume review.

You will receive the original resume and the review the agent produced. Score the review on each of the following criteria from 0.0 to 1.0, and provide a short (one sentence) reason for each:

- relevance: Does the review address what is actually in the resume (no hallucinated content)?
- specificity: Are observations concrete and tied to resume details, rather than generic advice?
- actionability: Can the candidate apply the suggested improvements directly?
- coverage: Does the review include a numeric score, strengths, and improvements?

Original Resume:
{{resume_text}}

Agent Review:
{{review}}

Return your evaluation in the required structured format.""",
}


def seed():
    for name, content in PROMPTS.items():
        try:
            existing = langfuse.get_prompt(name, label="production")
            if existing.prompt == content:
                print(f"[skip]   {name} (unchanged)")
                continue
            langfuse.create_prompt(
                name=name,
                prompt=content,
                labels=["production"],
                type="text",
                commit_message="Updated via seed_prompts.py",
            )
            print(f"[update] {name} (new version)")
        except Exception:
            langfuse.create_prompt(
                name=name,
                prompt=content,
                labels=["production"],
                type="text",
                commit_message="Initial version",
            )
            print(f"[create] {name}")


if __name__ == "__main__":
    seed()
    print("\nDone.")