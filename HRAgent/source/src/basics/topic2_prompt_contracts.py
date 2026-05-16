from utils_openai import ask_llm

SYSTEM = "You are a support assistant in your company."

weak_prompt = "Explain refund Policy."

strong_prompt = """
You are a support assistant.

Explain the refund policy of our company in 4 bullet points.
Rules:
- Answer in exactly 4 bullet points.
- If you are unsure, say: I don't know.
- Keep it simple for a beginner.
"""


print("\n--- Weak Prompt ---")

print(ask_llm(weak_prompt, SYSTEM, temperature=0.7, max_tokens=180))

print("\n--- Strong Prompt ---")
print(ask_llm(strong_prompt, SYSTEM, temperature=0.2, max_tokens=180))