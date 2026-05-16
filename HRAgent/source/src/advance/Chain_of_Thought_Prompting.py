import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4.1-mini")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing in .env")

client = OpenAI(api_key=API_KEY)

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {
            "role": "system",
            "content": "You are a a careful reasoning assistant."
        },
        {
            "role": "user",
            "content": "Solve step by step: 12 pens at ₹15 each. Total revenue?"
        }
    ]
)
print(response.choices[0].message.content)