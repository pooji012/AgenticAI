import os
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4.1-mini")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing in .env")

client = OpenAI(api_key=API_KEY)


def count_tokens(text: str, model="gpt-4.1-mini") -> int:
    """Count the number of tokens in a given text for a specific model."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        tokens = encoding.encode(text)
        return len(tokens) #len caunt tokens in a given text for a specific model."""
    except Exception as e:
        print(f"Error counting tokens: {e}")
        return -1
    

#Test the token counting function
sample_text = """Write a comprehensive analysis of artificial intelligence including:
    1. Definition and core concepts
    2. Historical development and milestones
    3. Current applications across industries
    4. Future implications and challenges
    5. Ethical considerations and societal impact
    Provide detailed explanations with real-world examples."""


print(f"Sample Text:\n{sample_text}\n")
token_count = count_tokens(sample_text)
print(f"Token Count for Sample Text: {token_count}")