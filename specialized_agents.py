from file_tools import FILE_TOOLS
from search_tools import SEARCH_TOOLS
from code_execution_tools import CODE_EXECUTION_TOOLS
from human_tools import HUMAN_TOOLS
import logging

# Configure logging to avoid Unicode errors
logger = logging.getLogger(__name__)

# Optimized agent configuration for high efficiency
AGENT_CONFIG = {
    "headless": False,  # Show browser for video playback
    "disable_security": True,
    "disable_images": False,  # Enable images for video content
    "disable_javascript": False,
    "viewport_size": (1920, 1080),
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "timeout": 30,  # Reduced timeout for faster response
    "max_retries": 1,  # Single retry for faster execution
    "max_steps": 5,  # Limit steps for immediate execution
    "disable_logging": True,  # Disable verbose logging
}

# A dictionary to hold the configuration for our specialized agents
# Each agent has a specific role and a limited set of tools.
SPECIALIZED_AGENTS = {
    "research_agent": {
        "description": "A specialized agent for web searches and information gathering.",
        "tools": SEARCH_TOOLS,
        "config": {**AGENT_CONFIG, "max_steps": 3, "timeout": 30},  # Quick searches
    },
    "file_agent": {
        "description": "A specialized agent for reading and writing files.",
        "tools": FILE_TOOLS,
        "config": {**AGENT_CONFIG, "max_steps": 2, "timeout": 20},  # File operations are quick
    },
    "code_agent": {
        "description": "A specialized agent for writing and executing Python code.",
        "tools": CODE_EXECUTION_TOOLS,
        "config": {**AGENT_CONFIG, "max_steps": 5, "timeout": 90},  # Code execution may take longer
    },
    # The browser_agent uses the built-in browser tools.
    "browser_agent": {
        "description": "A specialized agent for web browsing and automation.",
        "tools": [], 
        "config": {**AGENT_CONFIG, "max_steps": 3, "timeout": 20},  # Quick browser operations
    },
    # A generalist agent that can ask for help.
    "human_interaction_agent": {
        "description": "A specialized agent for interacting with the user.",
        "tools": HUMAN_TOOLS,
        "config": {**AGENT_CONFIG, "max_steps": 1, "timeout": 15},  # Human interaction should be minimal
    },
}
