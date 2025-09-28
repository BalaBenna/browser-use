from file_tools import FILE_TOOLS
from search_tools import SEARCH_TOOLS
from code_execution_tools import CODE_EXECUTION_TOOLS
from human_tools import HUMAN_TOOLS

# A dictionary to hold the configuration for our specialized agents
# Each agent has a specific role and a limited set of tools.
SPECIALIZED_AGENTS = {
    "research_agent": {
        "description": "A specialized agent for web searches and information gathering.",
        "tools": SEARCH_TOOLS,
    },
    "file_agent": {
        "description": "A specialized agent for reading and writing files.",
        "tools": FILE_TOOLS,
    },
    "code_agent": {
        "description": "A specialized agent for writing and executing Python code.",
        "tools": CODE_EXECUTION_TOOLS,
    },
    # The browser_agent uses the built-in browser tools.
    "browser_agent": {
        "description": "A specialized agent for web browsing and automation.",
        "tools": [], 
    },
    # A generalist agent that can ask for help.
    "human_interaction_agent": {
        "description": "A specialized agent for interacting with the user.",
        "tools": HUMAN_TOOLS,
    },
}
