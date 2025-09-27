"""
memory.py
Provides short-term and long-term memory for the agent, with optional vector/semantic search.
"""

import os
import json
from typing import List, Dict, Any, Optional

class AgentMemory:
    def __init__(self, memory_file: Optional[str] = None):
        self.short_term: List[Dict[str, Any]] = []
        self.memory_file = memory_file or os.path.expanduser("~/.browser_use_agent_memory.json")
        self._load_long_term()

    def remember(self, item: Dict[str, Any]):
        self.short_term.append(item)
        self._save_long_term(item)

    def recall_short_term(self) -> List[Dict[str, Any]]:
        return self.short_term

    def recall_long_term(self) -> List[Dict[str, Any]]:
        try:
            with open(self.memory_file, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_long_term(self, item: Dict[str, Any]):
        memory = self.recall_long_term()
        memory.append(item)
        with open(self.memory_file, "w") as f:
            json.dump(memory, f, indent=2)

    def _load_long_term(self):
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, "w") as f:
                json.dump([], f)
