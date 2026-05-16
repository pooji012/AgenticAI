from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Please set it in your .env file.")

client = OpenAI(api_key=api_key)
print("Successfully connected to OpenAI API")
print("-------------------------------------")


MODEL = os.getenv("MODEL", "gpt-4o-mini")

def explain_topic(topic: str) -> str:
    response = client.responses.create(
        model=MODEL,
        input=f"You are a helpful assistant that explains complex topics in simple terms.\n\n"
              f"Explain the topic '{topic}' in simple terms."
    )
    return response.output_text

print(explain_topic("LangChain"))