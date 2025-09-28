import io
import sys
from contextlib import redirect_stdout
from typing import Dict, Any

def execute_python_code(code: str, session_variables: Dict[str, Any]) -> str:
    """
    Executes a string of Python code in a sandboxed environment.
    The environment has access to a stateful dictionary of variables.
    
    :param code: The Python code to execute.
    :param session_variables: A dictionary of variables that persist across calls.
    :return: The output of the code (stdout) or an error message.
    """
    # A simple security check to prevent obvious malicious code.
    # For a production system, a more robust sandboxing solution is needed.
    if "__import__" in code or "os" in code or "sys" in code:
        return "Error: Use of restricted modules is not allowed."

    # Create a string buffer to capture stdout
    buffer = io.StringIO()

    try:
        # Redirect stdout to the buffer
        with redirect_stdout(buffer):
            # Execute the code with the session's variables
            exec(code, session_variables)
        
        # Get the output from the buffer
        output = buffer.getvalue()
        
        # If there is no output, return a success message
        if not output:
            return "Code executed successfully with no output."
        return output

    except Exception as e:
        return f"Error executing code: {e}"
    finally:
        # It's good practice to clean up the buffer
        buffer.close()

CODE_EXECUTION_TOOLS = [
    {
        "name": "execute_python_code",
        "function": execute_python_code,
        "description": "Executes a block of Python code and returns its output. You can use this to perform calculations, manipulate data, and more. Variables defined in one call will be available in subsequent calls within the same session.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code to execute."
                }
            },
            "required": ["code"]
        }
    }
]
