from datetime import datetime

from utils_openai import ask_llm


#--------------------------
# Tool 1: Calculator
#--------------------------

def calculator(expression: str) -> str:

    """
   This is not AI. This is a simple calculator tool that can evaluate basic math expressions.
   This is pure python  deterministic code, not AI. We can use it as a tool in our AI applications.
    """

    allowed = "0123456789+-*/(). "

    if any(c not in allowed for c in expression):
        return "Rejected: Only basic math expressions are allowed."
    
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"
    

print("\n--- Calculator Tool ---")
print(calculator("2 + 3 * 4"))  # Should return 14
print(calculator("10 / 2 - 1")) # Should return 4.0
print(calculator("5 + (6 - 2) * 3")) # Should return 17


#--------------------------
# Tool 2: Time Tool
#--------------------------

def current_time():
    """
    Another deterministic tool that returns the current time. This is not AI, just a simple function.
    """

    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")

print("\n--- Time Tool ---")
print("Current Time: "+current_time())


def route(user_input: str):
    """
    This function decides:
    - Should we use a tool?
    - Or call the LLM?
    """

    if any(char.isdigit() for char in user_input):
        return "calculator"

    if "time" in user_input.lower():
        return "time"

    return "llm"


def handle_request(user_input: str):

    decision = route(user_input)

    if decision == "calculator":
        print("Tool selected: Calculator")
        return calculator(user_input)

    if decision == "time":
        print("Tool selected: Time")
        return current_time()

    print("Using LLM for response")
    return ask_llm(user_input)


# Try examples
questions = [
    "12*(5+3)",
    "What is the current time?",
    "Explain what Recurssion is in simple terms."
]

for q in questions:
    print("\nUser:", q)
    print("Answer:", handle_request(q))