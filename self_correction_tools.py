from browser_use import Agent, ChatGoogle
from typing import Dict, Any

async def critique_work(task: str, history: str) -> str:
    """
    Critiques the agent's work on a given task.

    :param task: The original task the agent was trying to solve.
    :param history: The history of the agent's actions and results.
    :return: A critique of the agent's work and suggestions for improvement.
    """
    critique_prompt = f"""
    You are a quality assurance agent. Your job is to critique the work of another agent.
    The agent was given the following task: "{task}"

    Here is the history of the agent's actions:
    {history}

    Please provide a constructive critique of the agent's work.
    - Did the agent succeed at the task?
    - Did the agent make any mistakes?
    - How could the agent have done a better job?
    - What should the agent do next to correct its mistakes and complete the task?
    """

    # Use an agent to generate the critique
    critique_agent = Agent(
        task=critique_prompt,
        llm=ChatGoogle(model='gemini-flash-latest'),
        headless=True, # No browser needed for this task
    )

    result = await critique_agent.run()
    
    if hasattr(result, '__str__'):
        return str(result)
    return repr(result)

SELF_CORRECTION_TOOLS = [
    {
        "name": "critique_work",
        "function": critique_work,
        "description": "Critiques the agent's work on a given task. Use this to review your work, identify mistakes, and formulate a plan for self-correction.",
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "The original task the agent was trying to solve."
                },
                "history": {
                    "type": "string",
                    "description": "The history of the agent's actions and results."
                }
            },
            "required": ["task", "history"]
        }
    }
]
