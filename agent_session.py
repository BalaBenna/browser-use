from typing import Dict, Any

class AgentSession:
    """
    Manages the state for a single, persistent agent session.
    This gives the agent a memory to perform multi-step tasks.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        # A dictionary to hold variables for the Python interpreter
        self.python_variables: Dict[str, Any] = {}
        # A list of files the agent has written in this session
        self.files_written: list[str] = []
        print(f"AgentSession '{self.session_id}' created.")

    def reset(self):
        """Resets the session state."""
        self.python_variables = {}
        self.files_written = []
        print(f"AgentSession '{self.session_id}' has been reset.")

# A simple manager to hold all active sessions in memory.
# In a production system, this would be a database.
class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, AgentSession] = {}

    def get_session(self, session_id: str) -> AgentSession:
        """Gets an existing session or creates a new one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = AgentSession(session_id)
        return self._sessions[session_id]

# Create a single, global session manager instance
SESSION_MANAGER = SessionManager()
