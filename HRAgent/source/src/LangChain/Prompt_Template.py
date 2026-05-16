import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from rich import prompt

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("MODEL", "gpt-4o-mini"),
    temperature=0.3
)
#generate the prompt template
promptTemplate = "What is {topic} to a {age} year old in one sentence?"

#Prompt tempalte is like a sentence with placeholders/Variables that can be filled in with specific values. 
# In this case, the placeholders are {topic} and {age}. 
# We can use the format method to replace these placeholders with actual values.
prompt_text = promptTemplate.format(topic="LangChain", age=10) # .format() method is used to replace the placeholders/Variables in the 
                                                                #prompt template with the specified values.

#Utilize the Prompt
reply = llm.invoke(prompt_text)

print("Answer: " + reply.content)