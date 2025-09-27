"""
human_agent.py
Wraps the robust Agent class to provide a human-like agent interface, with optional memory, feedback, and simulated delay.
Defaults to fast execution, but can be extended for more human-like behavior.
"""

from typing import Any, Optional
import time
from browser_use.agent.service import Agent

class HumanLikeAgent:
    def __init__(self, llm, memory=None, simulate_human: bool = False, delay: float = 0.0):
        """
        llm: Language model interface (should be compatible with Agent)
        memory: Optional list for storing context
        simulate_human: If True, adds delays and feedback for human-like behavior
        delay: Seconds to wait between steps if simulate_human is True
        """
        self.llm = llm
        self.memory = memory or []
        self.simulate_human = simulate_human
        self.delay = delay

    async def run(self, prompt: str, **agent_kwargs) -> Any:
        """
        Run the agent on a single prompt, using the robust Agent class.
        If simulate_human is enabled, adds delay and feedback.
        """
        agent = Agent(task=prompt, llm=self.llm, **agent_kwargs)
        if self.simulate_human and self.delay > 0:
            print("[HumanLikeAgent] Thinking...")
            time.sleep(self.delay)
        result = await agent.run()
        self.memory.append({"prompt": prompt, "result": result})
        return result

    def remember(self, info: str):
        self.memory.append(info)

    def recall(self):
        return self.memory


