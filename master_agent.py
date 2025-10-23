from browser_use import Agent, ChatGoogle
from specialized_agents import SPECIALIZED_AGENTS
from typing import Dict, Any, List
import json
import asyncio
import logging
from error_handler import SafeLogger
# from cognitive_engine import CognitiveEngine, TaskComplexity
# from memory_system import MemorySystem
# from advanced_tools import AdvancedToolEcosystem

def _extract_final_response(result: Any) -> str:
    """
    Extracts the final, human-readable response from the agent's result object.
    """
    if not result:
        return "No result from agent."

    # The result object is an AgentHistoryList, which has an 'all_results' attribute.
    if hasattr(result, 'all_results'):
        # The final response is in the ActionResult where is_done is True.
        for action_result in reversed(result.all_results):
            if action_result.is_done and action_result.extracted_content:
                return action_result.extracted_content
        
        # Fallback: if no 'done' action, return the content of the last action.
        if result.all_results:
            last_result = result.all_results[-1]
            if hasattr(last_result, 'extracted_content') and last_result.extracted_content:
                return last_result.extracted_content

    # If all else fails, return the string representation of the result.
    return str(result)

class MasterAgent:
    def __init__(self, task: str, websocket):
        self.task = task
        self.websocket = websocket
        self.history = []
        self.shared_browser_session = None
        self.logger = SafeLogger(__name__)
        
        # Initialize basic components (removed complex memory system)
        # self.cognitive_engine = CognitiveEngine()
        # self.memory_system = MemorySystem()
        # self.tool_ecosystem = AdvancedToolEcosystem()
        
        # Enhanced state tracking
        self.execution_context = {}
        self.learning_enabled = True
        self.adaptive_mode = True

    async def run(self):
        """
        Runs the Master Agent to solve a complex task by planning and delegating.
        """
        try:
            await self._send_message_to_client("master_agent", "Creating a plan to solve the task...")
            plan = await self._create_plan()
            self.history.append({"step": "Create Plan", "result": str(plan)})

            # Create a shared browser session for efficiency
            await self._initialize_shared_session()

            for i, step in enumerate(plan.get("steps", [])):
                agent_name = step.get("agent")
                task = step.get("task")

                if not agent_name or not task:
                    continue

                await self._send_message_to_client("master_agent", f"Step {i+1}: Delegating task to {agent_name}: {task}")
                
                # Execute the task with the specialized agent.
                raw_result = await self._execute_sub_task(agent_name, task)
                # Parse the result to get a clean response.
                clean_result = _extract_final_response(raw_result)
                self.history.append({"step": f"Delegate to {agent_name}", "result": clean_result})

                await self._send_message_to_client(agent_name, f"Task completed. Result: {clean_result}")

            final_report_raw = await self._generate_final_report()
            final_report_clean = _extract_final_response(final_report_raw)
            await self._send_message_to_client("master_agent", f"Final Report: {final_report_clean}")
            return final_report_clean
            
        finally:
            # Clean up the shared browser session
            await self._cleanup_shared_session()

    async def _create_plan(self) -> Dict[str, Any]:
        """
        Creates a direct plan to solve the task immediately.
        """
        # For most tasks, use browser_agent directly
        task_lower = self.task.lower()
        
        if any(keyword in task_lower for keyword in ['play', 'youtube', 'video', 'song', 'music', 'watch']):
            return {
                "steps": [
                    {
                        "agent": "browser_agent",
                        "task": f"Open YouTube and {self.task}"
                    }
                ]
            }
        elif any(keyword in task_lower for keyword in ['book', 'flight', 'ticket', 'travel', 'hotel']):
            return {
                "steps": [
                    {
                        "agent": "browser_agent", 
                        "task": f"Help with booking: {self.task}"
                    }
                ]
            }
        elif any(keyword in task_lower for keyword in ['search', 'find', 'research', 'look up']):
            return {
                "steps": [
                    {
                        "agent": "browser_agent",
                        "task": f"Search and find information: {self.task}"
                    }
                ]
            }
        else:
            # Default to browser agent for any web-related task
            return {
                "steps": [
                    {
                        "agent": "browser_agent",
                        "task": f"Complete this task: {self.task}"
                    }
                ]
            }

    async def _execute_sub_task(self, agent_name: str, task: str) -> Any:
        """
        Executes a sub-task with a specialized agent and returns the raw result object.
        """
        agent_config = SPECIALIZED_AGENTS.get(agent_name)
        if not agent_config:
            return f"Error: Agent '{agent_name}' not found."

        specialized_agent = self._create_agent(task, agent_name)
        
        # Register the tools for the specialized agent (if any)
        tools = agent_config.get("tools", [])
        if tools:
            for tool in tools:
                specialized_agent.tools.registry.action(f"{agent_name} tool")(tool["function"])

        return await specialized_agent.run()

    async def _generate_final_report(self) -> str:
        """
        Generates a final report based on the history of the agent's actions.
        """
        if not self.history:
            return "The task could not be completed because no plan was executed."

        report = "The task has been completed. Here is a summary of the actions taken:\n\n"
        for item in self.history:
            report += f"Step: {item['step']}\nResult: {item['result']}\n\n"
        
        return report

    async def _initialize_shared_session(self):
        """
        Initialize a shared browser session for efficiency.
        """
        try:
            # Skip shared session for now due to import issues
            # We'll use individual agent sessions instead
            self.shared_browser_session = None
            self.logger.info("Using individual agent sessions for better compatibility")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize shared session: {e}")
            self.shared_browser_session = None

    async def _cleanup_shared_session(self):
        """
        Clean up the shared browser session.
        """
        if self.shared_browser_session:
            try:
                await self.shared_browser_session.close()
                self.shared_browser_session = None
            except Exception as e:
                self.logger.warning(f"Failed to cleanup shared session: {e}")

    def _create_agent(self, task: str, agent_name: str = "browser_agent") -> Agent:
        """
        Creates a new agent with the specified task and optimized configuration.
        """
        agent_config = SPECIALIZED_AGENTS.get(agent_name, {}).get("config", {})
        
        return Agent(
            task=task,
            llm=ChatGoogle(model='gemini-flash-latest'),
            **agent_config
        )

    async def _send_message_to_client(self, agent: str, message: str):
        """
        Sends a message to the client through the WebSocket.
        """
        if self.websocket:
            await self.websocket.send_json({
                "type": "agent_message",
                "agent": agent,
                "message": message,
            })

