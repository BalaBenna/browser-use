from typing import Dict, Any

def ask_user(question: str) -> str:
    """
    Asks the human user for input. Use this tool only when you are stuck,
    have tried all other options, or need a specific piece of information
    that only a human can provide. Overusing this tool will result in failure.
    Example: "What is the password for the website?"
    """
    # This is a placeholder. The actual implementation will be in the chat server
    # where it will pause execution and wait for user input.
    # The server will inject the user's response as the return value of this function.
    return "" 

HUMAN_TOOLS = [
    {
        "name": "ask_user",
        "function": ask_user,
        "description": "Asks the human user for input when you are stuck or need clarification. Use this sparingly.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to ask the user."
                }
            },
            "required": ["question"]
        }
    }
]
