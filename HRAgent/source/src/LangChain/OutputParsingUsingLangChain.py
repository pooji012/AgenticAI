import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Please set it in your .env file.")

model_name = os.getenv("MODEL", "gpt-4o-mini")

# This is the LangChain LLM wrapper (what the chain needs)
llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    temperature=0.2,
)

# Parser expects valid JSON, so we must instruct the model accordingly
parser = JsonOutputParser()

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant. Output ONLY valid JSON. No extra text."),
        ("user",
         "Explain {topic} in simple terms.\n"
         "Return JSON with this structure:\n"
         "{\n"
         '  "topic": string,\n'
         '  "summary": string,\n'
         '  "key_points": [string, string, string, string, string]\n'
         "}\n")
    ]
)

chain = prompt | llm | parser

result = chain.invoke({"topic": "Model List of OpenAI"})
print(result)
