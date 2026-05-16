from utils_openai import ask_llm

SYSTEM = "You are a teacher, Explain in very simple words."

prompt = "Define 'Gen AI development' in 2 lines for a beginner."

for temp in[0.1, 0.3, 0.7, 1.0]:
  
  print("\n"  + "="*55)
  print(f"Temperature: {temp}")
  print("="*55)
  print(ask_llm(prompt, system_text=SYSTEM, temperature=temp, max_tokens=120))