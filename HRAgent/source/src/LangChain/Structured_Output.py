import os
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

load_dotenv()

#1. Define a Pydantic model to specify the structure of the output you want from the language model. 
# In this case, we create a model called "Person" with fields for name, age, and occupation.
class Person(BaseModel):
    name: str
    role: str
    experience_years: int
    skills: list[str]

#2. Parser that converts the model's output into an instance of the Person class structure.
parser = PydanticOutputParser(pydantic_object=Person)

#3. Model configuration
llm = ChatOpenAI(
    model=os.getenv("MODEL", "gpt-4o-mini"),
    temperature=0.0,
)

#4. Create a prompt template that instructs the model to generate output in the format defined by the Person class.
prompt = PromptTemplate(
    template="Extract details from this text:\n{text}\n\n{format_instructions}",
    input_variables=["text"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

#5. Give the text value
text = """
Rakesh Singh is an automation engineer with 10 years experience in Playwright, Selenium, Python. 
He has worked in various industries including finance, healthcare, and e-commerce.
"""

#6. Invoke the model with the prompt and the text input, and parse the output into a Person object.
raw = llm.invoke(prompt.format(text=text)).content

#7 Ask the parser to convert the raw output into a Person object and print it.
parsed = parser.parse(raw)
print(parsed)