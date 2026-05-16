import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

load_dotenv()

llm = LLM(model="openai/gpt-4o-mini", temperature=0.3)
# llm2 = LLM(model="openai/gpt-4o-mini", temperature=0.5)
# llm3 = LLM(model="openai/gpt-4o-mini", temperature=1)

writer = Agent(
    role="Story Editor",
    goal="Write stories for a children's book series.",
    backstory=(
        "You are a creative and imaginative story editor with a passion"
        "for crafting engaging narratives for children. "
        "You have a knack for creating vivid characters "
        "and captivating plots that inspire young readers."
    ),
    llm=llm,
    verbose=True,
)

rabbitStoryTask = Task(
    name="Write a story about the brave little rabbit",
    description=(
        "Write a story about the brave little rabbit who goes on adventures in the forest. "
        "The story should be engaging, imaginative, and suitable for children."
    ),
    expected_output="A captivating story about the brave little rabbit's adventures in the forest, with vivid characters and an engaging plot that inspires young readers.",
    agent=writer
)


crew = Crew(
    name="Story Writers",
    agents=[writer], 
    verbose=True, 
    tasks=[rabbitStoryTask],
    process=Process.sequential
)

result = crew.kickoff()
print(result.raw)