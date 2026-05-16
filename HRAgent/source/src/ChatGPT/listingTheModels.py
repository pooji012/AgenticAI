import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4.1-mini")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing in .env")

client = OpenAI(api_key=API_KEY)

# Test the connection by listing the models available

try:
    models = client.models.list()
    print("Successfully Connected to OpenAI API:")
    print(f"Available Models: {len(models.data)} models found")
    for model in models.data:
        print(f" - {model.id}")

except Exception as e:
    print(f"❌ Error connecting to ChatGPT API: {e}")
    print("Please check your API key and internet connection.")
