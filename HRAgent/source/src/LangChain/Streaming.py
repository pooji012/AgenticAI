import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("MODEL", "gpt-4o-mini"),
    temperature=0.3,
    api_key=os.getenv("OPENAI_API_KEY"),
    streaming=True
)

llm.invoke(
    "Write 5 bullet points on why streaming is useful in LangChain.",
    config={"callbacks": [StreamingStdOutCallbackHandler()]}
)

print("Done streaming.")