import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4.1-mini")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing in .env")

client = OpenAI(api_key=API_KEY)

def ask_llm(user_text: str, system_text: str = "You are a helpful assistant.", temperature: float = 0.3, max_tokens: int = 300) -> str:
    """
     Note:
    - system_text sets the behavior rules for the AI / LLM
    - user_text is the user request /prompt / Instructions
    - temperature controls randomness of words being chosen
    """
    resp = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
        temperature=temperature,
        max_output_tokens=max_tokens
        
    )
    return resp.output_text
