"""
Comprehensive isolated tests for src/agents/agent_manager.py.
"""
import asyncio

import pytest

from src.agents.agent_core import Agent, AgentConfig, AgentRole, AgentState
from src.agents.agent_manager import AgentManager


class TestAgentManager:
    def test_empty(self):
        am = AgentManager()
        assert am.list_agents() == []

    def test_register(self):
        am = AgentManager()
        config = AgentConfig(
            agent_id="agent1",
            name="Agent1",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        agent = Agent(config)
        am.register(agent)
        assert "agent1" in am.list_agents()

    def test_get(self):
        am = AgentManager()
        config = AgentConfig(
            agent_id="agent1",
            name="Agent1",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        agent = Agent(config)
        am.register(agent)
        assert am.get("agent1") is agent

    def test_get_nonexistent(self):
        am = AgentManager()
        assert am.get("nonexistent") is None

    def test_unregister(self):
        am = AgentManager()
        config = AgentConfig(
            agent_id="agent1",
            name="Agent1",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        agent = Agent(config)
        am.register(agent)
        am.unregister("agent1")
        assert am.get("agent1") is None

    def test_unregister_nonexistent(self):
        am = AgentManager()
        am.unregister("nonexistent")

    def test_list_by_role(self):
        am = AgentManager()
        c1 = AgentConfig(agent_id="a1", name="A1", role=AgentRole.SUPPORT, business_id="biz")
        c2 = AgentConfig(agent_id="a2", name="A2", role=AgentRole.EXECUTIVE, business_id="biz")
        c3 = AgentConfig(agent_id="a3", name="A3", role=AgentRole.SUPPORT, business_id="biz")
        am.register(Agent(c1))
        am.register(Agent(c2))
        am.register(Agent(c3))
        support_agents = am.list_by_role(AgentRole.SUPPORT)
        assert len(support_agents) == 2

    def test_list_by_business(self):
        am = AgentManager()
        c1 = AgentConfig(agent_id="a1", name="A1", role=AgentRole.SUPPORT, business_id="biz1")
        c2 = AgentConfig(agent_id="a2", name="A2", role=AgentRole.SUPPORT, business_id="biz2")
        c3 = AgentConfig(agent_id="a3", name="A3", role=AgentRole.SUPPORT, business_id="biz1")
        am.register(Agent(c1))
        am.register(Agent(c2))
        am.register(Agent(c3))
        assert len(am.list_by_business("biz1")) == 2
        assert len(am.list_by_business("biz2")) == 1

    def test_set_routing(self):
        am = AgentManager()
        c1 = AgentConfig(agent_id="a1", name="A1", role=AgentRole.SUPPORT, business_id="biz1")
        am.register(Agent(c1))
        am.set_routing("biz1", "a1")
        agent = am.resolve_agent("biz1")
        assert agent is not None
        assert agent.config.agent_id == "a1"

    def test_resolve_agent_fallback(self):
        am = AgentManager()
        c1 = AgentConfig(agent_id="a1", name="A1", role=AgentRole.SUPPORT, business_id="biz1")
        am.register(Agent(c1))
        agent = am.resolve_agent("biz1")
        assert agent is not None

    def test_resolve_agent_with_role(self):
        am = AgentManager()
        c1 = AgentConfig(agent_id="a1", name="A1", role=AgentRole.SUPPORT, business_id="biz1")
        c2 = AgentConfig(agent_id="a2", name="A2", role=AgentRole.EXECUTIVE, business_id="biz1")
        am.register(Agent(c1))
        am.register(Agent(c2))
        agent = am.resolve_agent("biz1", AgentRole.EXECUTIVE)
        assert agent.config.agent_id == "a2"

    def test_resolve_agent_not_found(self):
        am = AgentManager()
        assert am.resolve_agent("nonexistent") is None

    def test_start_stop_all(self):
        am = AgentManager()
        c1 = AgentConfig(agent_id="a1", name="A1", role=AgentRole.SUPPORT, business_id="biz")
        c2 = AgentConfig(agent_id="a2", name="A2", role=AgentRole.SUPPORT, business_id="biz")
        am.register(Agent(c1))
        am.register(Agent(c2))
        asyncio.run(am.start_all())
        assert am.get("a1").state == AgentState.RUNNING
        assert am.get("a2").state == AgentState.RUNNING
        asyncio.run(am.stop_all())
        assert am.get("a1").state == AgentState.IDLE
        assert am.get("a2").state == AgentState.IDLE

    def test_get_status(self):
        am = AgentManager()
        c1 = AgentConfig(agent_id="a1", name="A1", role=AgentRole.SUPPORT, business_id="biz")
        am.register(Agent(c1))
        status = am.get_status()
        assert "a1" in status
        assert "agent_id" in status["a1"]
