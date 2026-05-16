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


# Observe that the model can return structured data in a specific format when prompted correctly.
response = client.responses.create(
    model=MODEL,
    input= "Return a JSON object with the following format: {\"name\": \"\", \"age\": 0, \"city\": \"\"}. Fill in the values with your own information."
)

print(response.output_text)