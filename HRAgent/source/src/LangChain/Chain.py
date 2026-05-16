import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("MODEL", "gpt-4o-mini"),
    temperature=0.3,
)

prompt_text = PromptTemplate.from_template("Explain {topic} in 2 bullet points.")


# 1st Build the chain by connecting the prompt template to the language model and then to the output parser.
# 2nd Call the Model with the prompt template and the specific topic you want to explain. The output will be parsed as a string by the StrOutputParser.
# 3rd convert the output to a string and print it.
chain = prompt_text | llm | StrOutputParser()

result = chain.invoke(prompt_text.format(topic="quantum physics"))

print(result)