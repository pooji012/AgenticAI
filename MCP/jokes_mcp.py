import random
import uvicorn
from fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware

mcp = FastMCP("Jokes MCP")

JOKES = [
    {"id": 1, "category": "programming", "joke": "Why do programmers prefer dark mode? Because light attracts bugs!"},
    {"id": 2, "category": "programming", "joke": "How many programmers does it take to change a light bulb? None — it's a hardware problem."},
    {"id": 3, "category": "programming", "joke": "A SQL query walks into a bar, walks up to two tables and asks... 'Can I join you?'"},
    {"id": 4, "category": "programming", "joke": "Why do Java developers wear glasses? Because they don't C#!"},
    {"id": 5, "category": "programming", "joke": "What's a programmer's favorite hangout spot? The Foo Bar."},
    {"id": 6, "category": "general", "joke": "Why don't scientists trust atoms? Because they make up everything!"},
    {"id": 7, "category": "general", "joke": "I told my wife she was drawing her eyebrows too high. She looked surprised."},
    {"id": 8, "category": "general", "joke": "What do you call a fake noodle? An impasta!"},
    {"id": 9, "category": "general", "joke": "Why can't you give Elsa a balloon? Because she'll let it go."},
    {"id": 10, "category": "general", "joke": "Did you hear about the mathematician who's afraid of negative numbers? He'll stop at nothing to avoid them."},
    {"id": 11, "category": "dad", "joke": "I'm reading a book about anti-gravity. It's impossible to put down!"},
    {"id": 12, "category": "dad", "joke": "What do you call cheese that isn't yours? Nacho cheese!"},
    {"id": 13, "category": "dad", "joke": "I would tell you a construction joke, but I'm still working on it."},
    {"id": 14, "category": "dad", "joke": "Why did the scarecrow win an award? Because he was outstanding in his field!"},
    {"id": 15, "category": "dad", "joke": "I only know 25 letters of the alphabet. I don't know why."},
]


@mcp.tool()
def get_random_joke() -> str:
    """Get a random joke from the collection."""
    joke = random.choice(JOKES)
    return f"[#{joke['id']} | {joke['category'].upper()}] {joke['joke']}"


@mcp.tool()
def get_joke_by_id(joke_id: int) -> str:
    """Get a specific joke by its ID.

    Args:
        joke_id: The ID of the joke (1 to 15).
    """
    joke = next((j for j in JOKES if j["id"] == joke_id), None)
    if not joke:
        return f"No joke found with ID {joke_id}. Valid IDs are 1 to {len(JOKES)}."
    return f"[#{joke['id']} | {joke['category'].upper()}] {joke['joke']}"


@mcp.tool()
def get_jokes_by_category(category: str) -> str:
    """Get all jokes from a specific category.

    Args:
        category: Category name — one of 'programming', 'general', or 'dad'.
    """
    filtered = [j for j in JOKES if j["category"].lower() == category.lower()]
    if not filtered:
        available = list({j["category"] for j in JOKES})
        return f"No jokes found for category '{category}'. Available: {', '.join(available)}."
    lines = [f"  #{j['id']}: {j['joke']}" for j in filtered]
    return f"[{category.upper()} JOKES]\n" + "\n".join(lines)


@mcp.tool()
def list_joke_categories() -> str:
    """List all available joke categories and how many jokes each has."""
    from collections import Counter
    counts = Counter(j["category"] for j in JOKES)
    lines = [f"  {cat}: {count} joke(s)" for cat, count in sorted(counts.items())]
    return "Available categories:\n" + "\n".join(lines)


@mcp.tool()
def get_all_jokes() -> str:
    """Get all jokes in the collection."""
    lines = [f"  #{j['id']} [{j['category'].upper()}]: {j['joke']}" for j in JOKES]
    return f"All {len(JOKES)} jokes:\n" + "\n".join(lines)


if __name__ == "__main__":
    app = mcp.http_app(transport="http", stateless_http=True)
    app_with_cors = CORSMiddleware(
        app=app,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    uvicorn.run(app_with_cors, host="0.0.0.0", port=8000)
