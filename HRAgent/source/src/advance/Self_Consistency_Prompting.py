import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4.1-mini")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing in .env")

client = OpenAI(api_key=API_KEY)

answers = []
for _ in range(5):
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.7,
        messages=[
            {
                "role": "user",
                "content": "Solve step by step: 17 * 23"
            }
        ]
    
    )
    answers.append(response.choices[0].message.content)

print(answers)

# After collecting multiple answers, we can use majority voting or other techniques to determine the most consistent answer among them.