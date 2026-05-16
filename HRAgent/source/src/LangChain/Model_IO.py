import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI( # creates a ChatOpenAI instance with the specified model and temperature
    model=os.getenv("MODEL", "gpt-4o-mini"),
    temperature=0.3,
)

# invokes the model with the given prompt and stores the response in the variable 'reply'
reply = llm.invoke("What is LangChain in one sentence?") 

# prints the content string of the "reply" json to the console
print(reply.content)