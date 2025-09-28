from googleapiclient.discovery import build
import os
from typing import List, Dict, Any
import json

def web_search(query: str) -> str:
    """Searches the web for a given query using Google Custom Search API."""
    try:
        service = build("customsearch", "v1", developerKey=os.getenv("GOOGLE_API_KEY"))
        res = service.cse().list(q=query, cx=os.getenv("CUSTOM_SEARCH_ENGINE_ID"), num=5).execute()
        # Format the results into a JSON string
        return json.dumps(res.get('items', []))
    except Exception as e:
        # Return the error as a string
        return f"Error performing search: {e}"

SEARCH_TOOLS = [
    {
        "name": "web_search",
        "function": web_search,
        "description": "Searches the web for a given query and returns the top 5 results.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to search for."
                }
            },
            "required": ["query"]
        }
    }
]
