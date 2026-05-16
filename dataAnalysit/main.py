import os
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from openai import OpenAI


DATA_FILE = Path(__file__).with_name("competitor_data.csv")
DEFAULT_EMBED_MODEL = "text-embedding-3-small"
DEFAULT_GENERATE_MODEL = "gpt-4o-mini"


def clean_text(value: object) -> str:
    """Normalize text before indexing while keeping it readable."""
    if pd.isna(value):
        return ""

    text = str(value).strip()
    text = re.sub(r"[^a-zA-Z0-9.,;:!?()&%$\\-\\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


@dataclass
class ReasoningPlan:
    intent: str
    competitors: list[str]
    sub_goals: list[str]
    top_k: int


class CompetitiveAnalysisAgent:
    def __init__(self, data_path: Path = DATA_FILE) -> None:
        load_dotenv()

        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Missing OPENAI_API_KEY. Create a .env file from .env.example and add your OpenAI API key."
            )
        if self.api_key.startswith("your_"):
            raise ValueError(
                "OPENAI_API_KEY still contains the placeholder value. Replace it with your real OpenAI API key."
            )

        self.data_path = data_path
        self.embed_model = os.getenv("OPENAI_EMBED_MODEL", DEFAULT_EMBED_MODEL)
        self.generate_model = os.getenv("OPENAI_CHAT_MODEL", DEFAULT_GENERATE_MODEL)
        self.history: list[dict[str, object]] = []
        self.reasoning_log: list[str] = []
        self.client = OpenAI(api_key=self.api_key)

        self.dataframe = self._load_and_prepare_data()
        self.index = self._build_index()
        self.query_engine = self.index.as_retriever(similarity_top_k=3)

    def _load_and_prepare_data(self) -> pd.DataFrame:
        if not self.data_path.exists():
            raise FileNotFoundError(f"Could not find data file: {self.data_path}")

        dataframe = pd.read_csv(self.data_path)
        expected_columns = [
            "Competitor Name",
            "Product Description",
            "Marketing Strategy",
            "Financial Summary",
        ]

        missing_columns = [col for col in expected_columns if col not in dataframe.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        for column in expected_columns:
            dataframe[column] = dataframe[column].apply(clean_text)

        dataframe["combined_text"] = dataframe.apply(
            lambda row: (
                f"Competitor Name: {row['Competitor Name']}\n"
                f"Product Description: {row['Product Description']}\n"
                f"Marketing Strategy: {row['Marketing Strategy']}\n"
                f"Financial Summary: {row['Financial Summary']}"
            ),
            axis=1,
        )
        return dataframe

    def _build_index(self) -> VectorStoreIndex:
        Settings.embed_model = OpenAIEmbedding(
            api_key=self.api_key,
            model=self.embed_model,
        )
        Settings.llm = None

        documents = [
            Document(
                text=row["combined_text"],
                metadata={"competitor": row["Competitor Name"]},
            )
            for _, row in self.dataframe.iterrows()
        ]
        return VectorStoreIndex.from_documents(documents)

    def _detect_competitors(self, query: str) -> list[str]:
        query_lower = query.lower()
        competitors = self.dataframe["Competitor Name"].tolist()
        return [name for name in competitors if name.lower() in query_lower]

    def _create_reasoning_plan(self, query: str) -> ReasoningPlan:
        query_lower = query.lower()
        competitors = self._detect_competitors(query)

        if any(word in query_lower for word in ["compare", "versus", "vs", "difference"]):
            intent = "comparison"
            sub_goals = [
                "Identify competitors mentioned in the query",
                "Retrieve relevant product, marketing, and financial context",
                "Compare similarities, differences, strengths, and risks",
                "Generate practical business insights",
            ]
            top_k = 5
        elif any(word in query_lower for word in ["advantage", "strength", "benefit", "good"]):
            intent = "strengths"
            sub_goals = [
                "Retrieve competitor context",
                "Identify positive differentiators",
                "Explain why those strengths matter",
                "Generate practical recommendations",
            ]
            top_k = 3
        elif any(word in query_lower for word in ["weakness", "risk", "problem", "threat"]):
            intent = "weaknesses"
            sub_goals = [
                "Retrieve competitor context",
                "Identify risks, gaps, or disadvantages",
                "Explain business impact",
                "Suggest possible response strategies",
            ]
            top_k = 3
        elif any(word in query_lower for word in ["financial", "revenue", "profit", "margin"]):
            intent = "financial_analysis"
            sub_goals = [
                "Retrieve financial summaries",
                "Analyze revenue, profitability, and margin signals",
                "Connect financial patterns to competitive position",
            ]
            top_k = 4
        else:
            intent = "overview"
            sub_goals = [
                "Retrieve relevant competitor information",
                "Summarize product, marketing, and financial details",
                "Generate concise competitive insight",
            ]
            top_k = 3

        return ReasoningPlan(
            intent=intent,
            competitors=competitors,
            sub_goals=sub_goals,
            top_k=top_k,
        )

    def _retrieve_context(self, query: str, top_k: int) -> str:
        self.query_engine = self.index.as_retriever(similarity_top_k=top_k)
        retrieved_nodes = self.query_engine.retrieve(query)

        if not retrieved_nodes:
            return "No relevant competitor context was found."

        context_blocks = []
        for index, node in enumerate(retrieved_nodes, start=1):
            competitor = node.metadata.get("competitor", "Unknown")
            context_blocks.append(
                f"Retrieved Document {index} - {competitor}\n{node.text}"
            )
        return "\n\n".join(context_blocks)

    def _generate_response(self, query: str, plan: ReasoningPlan, context: str) -> str:
        prompt = f"""
You are a competitive analysis consultant.

User query:
{query}

Detected intent:
{plan.intent}

Competitors explicitly mentioned:
{", ".join(plan.competitors) if plan.competitors else "None detected"}

Reasoning sub-goals:
{chr(10).join(f"- {goal}" for goal in plan.sub_goals)}

Retrieved competitor context:
{context}

Write a clear, practical answer. Include:
1. Direct answer to the query.
2. Evidence from the retrieved context.
3. Actionable business insights.
4. Any limitations if the data is incomplete.
""".strip()

        try:
            response = self.client.responses.create(
                model=self.generate_model,
                input=prompt,
            )
            return response.output_text
        except Exception as error:
            return f"Generation failed because of an API error: {error}"

    def reason_and_act(self, query: str) -> str:
        self.reasoning_log = []
        self.reasoning_log.append(f"Thought: Received query: {query}")

        plan = self._create_reasoning_plan(query)
        self.reasoning_log.append(f"Thought: Detected intent: {plan.intent}")

        if plan.competitors:
            self.reasoning_log.append(
                f"Thought: Competitors detected: {', '.join(plan.competitors)}"
            )
        else:
            self.reasoning_log.append(
                "Thought: No exact competitor name was detected, so retrieval will search across all data."
            )

        for goal in plan.sub_goals:
            self.reasoning_log.append(f"Sub-goal: {goal}")

        self.reasoning_log.append(
            f"Action: Retrieve relevant documents using top_k={plan.top_k}"
        )
        context = self._retrieve_context(query, plan.top_k)

        self.reasoning_log.append("Action: Generate final response with OpenAI")
        answer = self._generate_response(query, plan, context)

        self.history.append(
            {
                "query": query,
                "intent": plan.intent,
                "answer": answer,
                "reasoning": self.reasoning_log.copy(),
            }
        )
        return answer

    def show_recent_history(self, limit: int = 5) -> str:
        if not self.history:
            return "No query history yet."

        recent_items = self.history[-limit:]
        lines = []
        for number, item in enumerate(recent_items, start=1):
            lines.append(
                f"{number}. Query: {item['query']}\n"
                f"   Intent: {item['intent']}\n"
                f"   Answer preview: {str(item['answer'])[:160]}..."
            )
        return "\n".join(lines)

    def show_reasoning(self) -> str:
        if not self.reasoning_log:
            return "No reasoning steps yet."
        return "\n".join(self.reasoning_log)


def run_cli() -> None:
    print("Competitive Analysis Agent")
    print("Type a question, 'history', 'reasoning', or 'exit'.")
    print()

    try:
        agent = CompetitiveAnalysisAgent()
    except Exception as error:
        print(f"Startup error: {error}")
        return

    while True:
        query = input("Ask > ").strip()

        if not query:
            continue

        command = query.lower()
        if command in {"exit", "quit"}:
            print("Goodbye.")
            break

        if command == "history":
            print(agent.show_recent_history())
            print()
            continue

        if command == "reasoning":
            print(agent.show_reasoning())
            print()
            continue

        answer = agent.reason_and_act(query)
        print()
        print(answer)
        print()
        print("Reasoning steps:")
        print(agent.show_reasoning())
        print()


if __name__ == "__main__":
    run_cli()
