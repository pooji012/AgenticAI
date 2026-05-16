import argparse
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent
os.environ.setdefault("CREWAI_STORAGE_DIR", str(PROJECT_ROOT / ".crewai-storage"))
os.environ["LOCALAPPDATA"] = str(PROJECT_ROOT / ".localappdata")
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")

from crewai import Agent, Crew, LLM, Process, Task


OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_FILE = OUTPUT_DIR / "final_content.txt"
CONTENT_TYPES = ("blog post", "social media post", "website copy")


def build_llm() -> LLM:
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return LLM(model=f"openai/{model_name}", temperature=0.4)


def create_agents(llm: LLM) -> tuple[Agent, Agent, Agent, Agent]:
    topic_researcher = Agent(
        role="Topic Researcher",
        goal=(
            "Research the assigned marketing topic, identify useful subtopics, "
            "audience needs, keyword opportunities, and source angles."
        ),
        backstory=(
            "You are a digital marketing researcher at Innovate Marketing Solutions. "
            "You understand technology startups, buyer intent, and how to turn a broad "
            "topic into practical research notes for content creators."
        ),
        llm=llm,
        verbose=True,
    )

    content_writer = Agent(
        role="Content Writer",
        goal=(
            "Create clear, original, useful marketing content from the research notes "
            "while matching the requested tone, audience, and content format."
        ),
        backstory=(
            "You are an experienced B2B technology content writer. You write in a "
            "structured, reader-friendly style and avoid generic filler."
        ),
        llm=llm,
        verbose=True,
    )

    seo_specialist = Agent(
        role="SEO Specialist",
        goal=(
            "Optimize the draft for search visibility using natural keyword placement, "
            "strong headings, a title tag, and a meta description."
        ),
        backstory=(
            "You are an SEO strategist who balances search optimization with human "
            "readability. You know how to improve on-page SEO without keyword stuffing."
        ),
        llm=llm,
        verbose=True,
    )

    quality_reviewer = Agent(
        role="Quality Reviewer",
        goal=(
            "Review the SEO-optimized content for relevance, quality, accuracy, tone, "
            "bias, and assignment completeness."
        ),
        backstory=(
            "You are a senior editor responsible for final approval. You make sure "
            "content is polished, helpful, brand-safe, and ready for a client."
        ),
        llm=llm,
        verbose=True,
    )

    return topic_researcher, content_writer, seo_specialist, quality_reviewer


def create_tasks(
    topic: str,
    audience: str,
    content_type: str,
    tone: str,
    agents: tuple[Agent, Agent, Agent, Agent],
) -> list[Task]:
    topic_researcher, content_writer, seo_specialist, quality_reviewer = agents

    research_task = Task(
        name="Topic research and keyword planning",
        description=(
            f"Research the topic: {topic}.\n"
            f"Target audience: {audience}.\n"
            "Gather useful information for a marketing content project. Include:\n"
            "- Main audience pain points\n"
            "- 5 to 8 SEO keyword ideas\n"
            "- Search intent for the primary keyword\n"
            "- Common questions readers may ask\n"
            "- Important talking points\n"
            "- Competitor-style content gaps or opportunities\n"
            "- Suggested content angle\n"
            "- Possible title ideas\n"
            "Use careful reasoning and general knowledge when live search tools are "
            "not available. Do not invent fake source names or fake statistics."
        ),
        expected_output=(
            "A structured research brief containing audience pain points, keyword ideas, "
            "search intent, reader questions, talking points, content angle, and title ideas."
        ),
        agent=topic_researcher,
    )

    writing_task = Task(
        name="Content drafting",
        description=(
            f"Using the research brief, write a {content_type} about {topic}.\n"
            f"Use a {tone} tone for {audience}.\n"
            "Make the content original, practical, well organized, and easy to read."
        ),
        expected_output=(
            "A complete first draft with a strong introduction, useful body sections, "
            "and a clear conclusion or call to action."
        ),
        agent=content_writer,
        context=[research_task],
    )

    seo_task = Task(
        name="SEO optimization",
        description=(
            "Improve the draft for SEO while keeping it natural for readers.\n"
            "Include:\n"
            "- SEO title tag\n"
            "- Meta description under 160 characters\n"
            "- Suggested URL slug\n"
            "- Primary keyword\n"
            "- Secondary keywords\n"
            "- Optimized final content with headings"
        ),
        expected_output=(
            "An SEO-ready version of the content with metadata, keywords, and optimized copy."
        ),
        agent=seo_specialist,
        context=[writing_task],
    )

    review_task = Task(
        name="Quality review and final approval",
        description=(
            "Review the SEO-ready content and produce the final version.\n"
            "Check for relevance, quality, clarity, factual caution, bias, tone, and "
            "assignment completeness.\n"
            "Return the final client-ready content followed by a short evaluation section "
            "scoring relevance and quality out of 10."
        ),
        expected_output=(
            "Final polished content plus a short evaluation section with relevance and "
            "quality scores."
        ),
        agent=quality_reviewer,
        context=[seo_task],
    )

    return [research_task, writing_task, seo_task, review_task]


def save_result(result: object, topic: str, audience: str, content_type: str, tone: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    raw_output = getattr(result, "raw", str(result))
    header = (
        "AI-Powered Content Creation Output\n"
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Topic: {topic}\n"
        f"Audience: {audience}\n"
        f"Content Type: {content_type}\n"
        f"Tone: {tone}\n"
        "\n"
        "----------------------------------------\n\n"
    )
    OUTPUT_FILE.write_text(header + raw_output, encoding="utf-8")
    return OUTPUT_FILE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Innovate Marketing Solutions content creation crew."
    )
    parser.add_argument(
        "--topic",
        default=None,
        help="Content topic to generate.",
    )
    parser.add_argument(
        "--audience",
        default=None,
        help="Target audience for the content.",
    )
    parser.add_argument(
        "--content-type",
        default=None,
        choices=CONTENT_TYPES,
        help="Type of marketing content to create.",
    )
    parser.add_argument(
        "--tone",
        default=None,
        help="Brand tone or writing style.",
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Use default values instead of asking questions in the terminal.",
    )
    return parser.parse_args()


def ask_with_default(question: str, default: str) -> str:
    answer = input(f"{question} [{default}]: ").strip()
    return answer or default


def ask_content_type(default: str = "blog post") -> str:
    print("\nChoose content type:")
    for index, content_type in enumerate(CONTENT_TYPES, start=1):
        print(f"{index}. {content_type}")

    answer = input(f"Enter 1-{len(CONTENT_TYPES)} or press Enter for {default}: ").strip()
    if not answer:
        return default

    if answer.isdigit():
        selected_index = int(answer)
        if 1 <= selected_index <= len(CONTENT_TYPES):
            return CONTENT_TYPES[selected_index - 1]

    normalized_answer = answer.lower()
    if normalized_answer in CONTENT_TYPES:
        return normalized_answer

    print(f"Invalid choice. Using default: {default}")
    return default


def collect_project_inputs(args: argparse.Namespace) -> argparse.Namespace:
    defaults = {
        "topic": "AI tools for small business marketing",
        "audience": "startup founders and small business marketing teams",
        "content_type": "blog post",
        "tone": "professional and helpful",
    }

    if args.no_interactive:
        args.topic = args.topic or defaults["topic"]
        args.audience = args.audience or defaults["audience"]
        args.content_type = args.content_type or defaults["content_type"]
        args.tone = args.tone or defaults["tone"]
        return args

    print("\nAI-Powered Content Creation Agent")
    print("Enter the content details. Press Enter to use the default value.\n")

    args.topic = args.topic or ask_with_default("What topic should the agents research?", defaults["topic"])
    args.audience = args.audience or ask_with_default("Who is the target audience?", defaults["audience"])
    args.content_type = args.content_type or ask_content_type(defaults["content_type"])
    args.tone = args.tone or ask_with_default("What tone should the content use?", defaults["tone"])

    print("\nStarting the CrewAI agents with these details:")
    print(f"Topic: {args.topic}")
    print(f"Audience: {args.audience}")
    print(f"Content Type: {args.content_type}")
    print(f"Tone: {args.tone}\n")

    return args


def main() -> None:
    load_dotenv()
    args = parse_args()
    args = collect_project_inputs(args)

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Copy .env.example to .env and add your key."
        )

    llm = build_llm()
    agents = create_agents(llm)
    tasks = create_tasks(
        topic=args.topic,
        audience=args.audience,
        content_type=args.content_type,
        tone=args.tone,
        agents=agents,
    )

    crew = Crew(
        name="Innovate Marketing Solutions Content Crew",
        agents=list(agents),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    output_path = save_result(
        result=result,
        topic=args.topic,
        audience=args.audience,
        content_type=args.content_type,
        tone=args.tone,
    )
    print(f"\nFinal content saved to: {output_path}")


if __name__ == "__main__":
    main()
