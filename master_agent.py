from browser_use import Agent, ChatGoogle
from specialized_agents import SPECIALIZED_AGENTS
from typing import Dict, Any, List
import json

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

    async def run(self):
        """
        Runs the Master Agent to solve a complex task by planning and delegating.
        """
        await self._send_message_to_client("master_agent", "Creating a plan to solve the task...")
        plan = await self._create_plan()
        self.history.append({"step": "Create Plan", "result": plan})

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

    async def _create_plan(self) -> Dict[str, Any]:
        """
        Creates a plan to solve the task.
        """
        planning_prompt = f"""
        You are a master agent. Create a plan to solve the following task: "{self.task}"
        Break the task into steps, and for each step, specify the specialized agent to use.
        Available agents: {list(SPECIALIZED_AGENTS.keys())}
        
        Your response MUST be a JSON object with a single key, "steps", which is a list of objects,
        each with "agent" and "task" keys.
        Example:
        {{
            "steps": [
                {{
                    "agent": "research_agent",
                    "task": "Find the capital of France."
                }}
            ]
        }}
        """
        planning_agent = self._create_agent(planning_prompt)
        result = await planning_agent.run()
        clean_result = _extract_final_response(result)
        try:
            # The plan is expected to be a clean JSON string from the LLM.
            return json.loads(clean_result)
        except json.JSONDecodeError:
            await self._send_message_to_client("master_agent", "Error: The planning agent returned an invalid plan. I will try to proceed without a plan.")
            return {"steps": []}

    async def _execute_sub_task(self, agent_name: str, task: str) -> Any:
        """
        Executes a sub-task with a specialized agent and returns the raw result object.
        """
        agent_config = SPECIALIZED_AGENTS.get(agent_name)
        if not agent_config:
            return f"Error: Agent '{agent_name}' not found."

        specialized_agent = self._create_agent(task)
        
        # Register the tools for the specialized agent.
        for tool in agent_config["tools"]:
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

    def _create_agent(self, task: str) -> Agent:
        """
        Creates a new agent with the specified task.
        """
        return Agent(
            task=task,
            llm=ChatGoogle(model='gemini-flash-latest'),
            headless=True,
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

