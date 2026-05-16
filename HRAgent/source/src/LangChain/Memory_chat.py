import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("MODEL", "gpt-4o-mini"),
    temperature=0.3,
    api_key=os.getenv("OPENAI_API_KEY"),
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant that provides information about the user."),
        MessagesPlaceholder("history"),
        ("human", "{input}"),
    ]
)

chain = prompt | llm | StrOutputParser()

store: dict[str, InMemoryChatMessageHistory] = {}

def get_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

chat = RunnableWithMessageHistory(
    chain,
    get_history,
    input_messages_key="input",
    history_messages_key="history",
)

session_id = "user123"

result = chat.invoke(
    {"input": "Hi, I am Rakesh"},
    config={"configurable": {"session_id": session_id}},
)
print(result)

result = chat.invoke(
    {"input": "What is my name?"},
    config={"configurable": {"session_id": session_id}},
)
print(result)