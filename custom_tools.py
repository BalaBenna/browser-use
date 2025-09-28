import os
import subprocess
import ast
from agent_session import AgentSession

# A simple whitelist of allowed shell commands for security
ALLOWED_SHELL_COMMANDS = ["ls", "dir", "echo", "cat", "head", "tail"]

def list_files(directory: str = ".") -> str:
    """
    Lists all files and directories in the specified directory.
    """
    try:
        files = os.listdir(directory)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {e}"

def read_file(file_path: str) -> str:
    """
    Reads the content of a specified file.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(file_path: str, content: str, session: AgentSession) -> str:
    """
    Writes content to a specified file and tracks it in the session.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        session.files_written.append(file_path)
        return f"File '{file_path}' written successfully."
    except Exception as e:
        return f"Error writing file: {e}"

def execute_python_code(code: str, session: AgentSession) -> str:
    """
    Executes a string of Python code using the session's context
    and returns the result. This maintains state between calls.
    """
    try:
        # Execute the code using the session's variable dictionary
        # This allows code to build on previous executions
        exec(code, session.python_variables)
        return "Code executed successfully."
    except Exception as e:
        return f"Error executing code: {e}"

def run_shell_command(command: str) -> str:
    """
    Runs a shell command and returns its output.
    Only allows commands from a predefined whitelist for security.
    """
    try:
        command_parts = command.split()
        if command_parts[0] not in ALLOWED_SHELL_COMMANDS:
            return f"Error: Command '{command_parts[0]}' is not allowed."

        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e.stderr}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def ask_user(question: str) -> str:
    """
    Asks the user for input. This is used when the agent is stuck
    or needs additional information from the user.
    """
    # This function will be handled by the websocket server,
    # which will send the question to the frontend.
    # The function itself doesn't need to do anything.
    return f"Asking user: {question}"

# A list of all custom tools to be registered with the agent
CUSTOM_TOOLS = [
    {"name": "list_files", "description": "Lists files in a directory.", "function": list_files},
    {"name": "read_file", "description": "Reads the content of a file.", "function": read_file},
    {"name": "write_file", "description": "Writes content to a file.", "function": write_file},
    {"name": "execute_python_code", "description": "Executes Python code.", "function": execute_python_code},
    {"name": "run_shell_command", "description": "Runs a shell command.", "function": run_shell_command},
    {"name": "ask_user", "description": "Asks the user for input.", "function": ask_user},
]
