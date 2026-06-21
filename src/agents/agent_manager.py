"""
Agent manager for orchestrating multiple agents.
"""
import logging
from typing import Dict, List, Optional
from .agent_core import Agent, AgentConfig, AgentRole

logger = logging.getLogger(__name__)


class AgentManager:
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._routing: Dict[str, str] = {}

    def register(self, agent: Agent):
        self._agents[agent.config.agent_id] = agent

    def unregister(self, agent_id: str):
        self._agents.pop(agent_id, None)

    def get(self, agent_id: str) -> Optional[Agent]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())

    def list_by_role(self, role: AgentRole) -> List[Agent]:
        return [a for a in self._agents.values() if a.config.role == role]

    def list_by_business(self, business_id: str) -> List[Agent]:
        return [a for a in self._agents.values() if a.config.business_id == business_id]

    def set_routing(self, business_id: str, agent_id: str):
        self._routing[business_id] = agent_id

    def resolve_agent(self, business_id: str, role: Optional[AgentRole] = None) -> Optional[Agent]:
        if business_id in self._routing:
            agent = self._agents.get(self._routing[business_id])
            if agent:
                return agent
        candidates = self.list_by_business(business_id)
        if role:
            candidates = [a for a in candidates if a.config.role == role]
        return candidates[0] if candidates else None

    async def start_all(self):
        for agent_id, agent in self._agents.items():
            try:
                await agent.start()
            except Exception as e:
                logger.error(f"Failed to start agent {agent_id}: {e}")

    async def stop_all(self):
        for agent_id, agent in self._agents.items():
            try:
                await agent.stop()
            except Exception as e:
                logger.error(f"Failed to stop agent {agent_id}: {e}")

    def get_status(self) -> Dict:
        return {agent_id: agent.get_metrics() for agent_id, agent in self._agents.items()}
