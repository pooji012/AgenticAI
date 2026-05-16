from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("MODEL", "gpt-4o-mini")

model = ChatOpenAI(model=MODEL)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant that explains complex topics in simple terms."),
        ("user", "Explain {topic} in simple terms.")
    ]
)

chain = prompt | model

print(chain.invoke({"topic": "LangChain"}).content)