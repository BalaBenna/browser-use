import os
import json
from typing import Dict, Any

MEMORY_DIR = "long_term_memory"

def _get_memory_path(session_id: str) -> str:
    """Gets the path to the memory file for a given session."""
    if not os.path.exists(MEMORY_DIR):
        os.makedirs(MEMORY_DIR)
    return os.path.join(MEMORY_DIR, f"{session_id}.json")

def save_to_memory(session_id: str, key: str, value: Any) -> str:
    """Saves a key-value pair to the agent's long-term memory."""
    try:
        memory_path = _get_memory_path(session_id)
        if os.path.exists(memory_path):
            with open(memory_path, 'r', encoding='utf-8') as f:
                memory = json.load(f)
        else:
            memory = {}
        
        memory[key] = value
        
        with open(memory_path, 'w', encoding='utf-8') as f:
            json.dump(memory, f, indent=4)
            
        return f"Successfully saved '{key}' to memory."
    except Exception as e:
        return f"Error saving to memory: {e}"

def load_from_memory(session_id: str, key: str) -> Any:
    """Loads a value from the agent's long-term memory."""
    try:
        memory_path = _get_memory_path(session_id)
        if not os.path.exists(memory_path):
            return f"No memory found for session '{session_id}'."
            
        with open(memory_path, 'r', encoding='utf-8') as f:
            memory = json.load(f)
            
        value = memory.get(key)
        
        if value is None:
            return f"No value found for key '{key}' in memory."
            
        return value
    except Exception as e:
        return f"Error loading from memory: {e}"

MEMORY_TOOLS = [
    {
        "name": "save_to_memory",
        "function": save_to_memory,
        "description": "Saves a value to the agent's long-term memory. Use this to remember important information for later use.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "The key to store the value under."
                },
                "value": {
                    "type": "any",
                    "description": "The value to store."
                }
            },
            "required": ["key", "value"]
        }
    },
    {
        "name": "load_from_memory",
        "function": load_from_memory,
        "description": "Loads a value from the agent's long-term memory. Use this to recall information you have saved before.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "The key of the value to load."
                }
            },
            "required": ["key"]
        }
    }
]
