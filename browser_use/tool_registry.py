"""
tool_registry.py
Defines a registry for agent tools (web, file, API, code, etc.) and a base interface for tool integration.
"""

from typing import Any, Dict, Callable

class Tool:
    def __init__(self, name: str, func: Callable, description: str = ""):
        self.name = name
        self.func = func
        self.description = description

    def run(self, *args, **kwargs) -> Any:
        return self.func(*args, **kwargs)

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def run(self, name: str, *args, **kwargs) -> Any:
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found.")
        return self.tools[name].run(*args, **kwargs)

    def list_tools(self):
        return list(self.tools.keys())
