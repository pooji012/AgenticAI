import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4.1-mini")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing in .env")

client = OpenAI(api_key=API_KEY)
prompt = """
Generate 3 strategies to grow a SaaS startup.
Evaluate pros and cons of each.
Select the best option.
"""
response = client.chat.completions.create(
    model=MODEL,
   temperature=0.7,
   messages = [
       {"role": "user", "content": prompt}
   ]
)
print(response.choices[0].message.content)