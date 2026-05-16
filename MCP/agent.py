import asyncio
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

# Path to the MCP server script
MCP_SERVER_PATH = os.path.join(os.path.dirname(__file__), "app.py")


async def run_agent(user_input: str):
    # Connect to the DateTime MCP server via stdio
    async with MultiServerMCPClient(
        {
            "datetime": {
                "command": "python",
                "args": [MCP_SERVER_PATH],
                "transport": "stdio",
            }
        }
    ) as client:
        tools = client.get_tools()

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        agent = create_react_agent(llm, tools)

        response = await agent.ainvoke({"messages": [{"role": "user", "content": user_input}]})

        # Print the final answer
        final_message = response["messages"][-1]
        print(f"\nAgent: {final_message.content}")


if __name__ == "__main__":
    print("DateTime MCP Agent (powered by LangGraph + OpenAI)")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue
        asyncio.run(run_agent(user_input))
