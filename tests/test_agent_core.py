"""
Comprehensive isolated tests for src/agents/agent_core.py.
"""
import asyncio

import pytest

from src.agents.agent_core import (
    Agent,
    AgentConfig,
    AgentRole,
    AgentState,
    Tool,
    Skill,
)


class TestAgentRole:
    def test_values(self):
        assert AgentRole.EXECUTIVE.value == "executive"
        assert AgentRole.CONTENT.value == "content"
        assert AgentRole.JEWELRY.value == "jewelry"
        assert AgentRole.RESEARCH.value == "research"
        assert AgentRole.SUPPORT.value == "support"
        assert AgentRole.CUSTOM.value == "custom"

    def test_count(self):
        assert len(AgentRole) == 6


class TestAgentState:
    def test_values(self):
        assert AgentState.IDLE.value == "idle"
        assert AgentState.STARTING.value == "starting"
        assert AgentState.RUNNING.value == "running"
        assert AgentState.PROCESSING.value == "processing"
        assert AgentState.STOPPING.value == "stopping"
        assert AgentState.ERROR.value == "error"


class TestTool:
    def test_creation(self):
        async def handler(msg, ctx):
            return "result"

        t = Tool(
            name="search",
            description="Search tool",
            handler=handler,
            parameters={"query": {"type": "string"}},
            requires_auth=True,
            category="utility",
        )
        assert t.name == "search"
        assert t.description == "Search tool"
        assert t.handler is handler
        assert t.requires_auth is True
        assert t.category == "utility"

    def test_defaults(self):
        async def handler(msg, ctx):
            pass

        t = Tool(name="t", description="d", handler=handler)
        assert t.parameters == {}
        assert t.requires_auth is False
        assert t.category == "general"


class TestSkill:
    def test_creation(self):
        s = Skill(
            name="jewelry_expert",
            description="Jewelry knowledge",
            instructions="You are a jewelry expert...",
            tools=["search", "lookup"],
            triggers=["jewelry", "ring"],
        )
        assert s.name == "jewelry_expert"
        assert len(s.tools) == 2
        assert len(s.triggers) == 2

    def test_defaults(self):
        s = Skill(name="s", description="d", instructions="i")
        assert s.tools == []
        assert s.triggers == []


class TestAgentConfig:
    def test_creation(self):
        c = AgentConfig(
            agent_id="agent1",
            name="Executive",
            role=AgentRole.EXECUTIVE,
            business_id="openclaw",
        )
        assert c.agent_id == "agent1"
        assert c.name == "Executive"
        assert c.role == AgentRole.EXECUTIVE
        assert c.business_id == "openclaw"
        assert c.model == "gpt-4"
        assert c.system_prompt == ""
        assert c.channels == []
        assert c.tools == []
        assert c.skills == []
        assert c.memory_enabled is True
        assert c.max_context_length == 8192
        assert c.temperature == 0.7


class TestAgent:
    def test_init(self):
        c = AgentConfig(
            agent_id="agent1",
            name="Test Agent",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        agent = Agent(c)
        assert agent.state == AgentState.IDLE
        assert agent._tools == {}
        assert agent._skills == {}
        assert agent._channels == {}
        assert agent._memory is None
        assert agent._conversation_history == {}
        assert agent._start_time == 0.0
        assert agent._message_count == 0
        assert agent._error_count == 0

    def test_start_stop(self):
        c = AgentConfig(
            agent_id="agent1",
            name="Test",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        agent = Agent(c)
        asyncio.run(agent.start())
        assert agent.state == AgentState.RUNNING
        asyncio.run(agent.stop())
        assert agent.state == AgentState.IDLE

    def test_register_tool(self):
        c = AgentConfig(
            agent_id="agent1",
            name="Test",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        agent = Agent(c)
        t = Tool(name="search", description="Search", handler=lambda m, c: None)
        agent.register_tool(t)
        assert "search" in agent._tools

    def test_register_skill(self):
        c = AgentConfig(
            agent_id="agent1",
            name="Test",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        agent = Agent(c)
        s = Skill(name="jewelry", description="Jewelry", instructions="Expert")
        agent.register_skill(s)
        assert "jewelry" in agent._skills

    def test_register_channel(self):
        c = AgentConfig(
            agent_id="agent1",
            name="Test",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        agent = Agent(c)
        agent.register_channel("telegram", "adapter")
        assert "telegram" in agent._channels

    def test_process_message(self):
        c = AgentConfig(
            agent_id="agent1",
            name="TestBot",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        agent = Agent(c)
        result = asyncio.run(
            agent.process_message("chat1", "user1", "hello")
        )
        assert "hello" in result
        assert "TestBot" in result

    def test_process_message_with_tool(self):
        c = AgentConfig(
            agent_id="agent1",
            name="TestBot",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        agent = Agent(c)

        async def search_tool(msg, ctx):
            return "search result"

        agent.register_tool(Tool(name="search", description="Search", handler=search_tool))
        result = asyncio.run(
            agent.process_message("chat1", "user1", "use search tool")
        )
        assert result == "search result"

    def test_process_message_tool_error(self):
        c = AgentConfig(
            agent_id="agent1",
            name="TestBot",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        agent = Agent(c)

        async def failing_tool(msg, ctx):
            raise ValueError("tool failed")

        agent.register_tool(Tool(name="fail", description="Fail", handler=failing_tool))
        result = asyncio.run(
            agent.process_message("chat1", "user1", "use fail tool")
        )
        assert "received" in result.lower() or "error" in result.lower()

    def test_conversation_history(self):
        c = AgentConfig(
            agent_id="agent1",
            name="TestBot",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        agent = Agent(c)
        asyncio.run(
            agent.process_message("chat1", "user1", "hello")
        )
        asyncio.run(
            agent.process_message("chat1", "user1", "world")
        )
        key = "chat1:user1"
        assert key in agent._conversation_history
        history = agent._conversation_history[key]
        assert len(history) == 4

    def test_conversation_history_trimming(self):
        c = AgentConfig(
            agent_id="agent1",
            name="TestBot",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        agent = Agent(c)
        for i in range(60):
            asyncio.run(
                agent.process_message("chat1", "user1", f"msg {i}")
            )
        key = "chat1:user1"
        assert len(agent._conversation_history[key]) <= 50

    def test_get_metrics(self):
        c = AgentConfig(
            agent_id="agent1",
            name="Test",
            role=AgentRole.SUPPORT,
            business_id="biz",
        )
        agent = Agent(c)
        asyncio.run(agent.start())
        metrics = agent.get_metrics()
        assert metrics["agent_id"] == "agent1"
        assert metrics["state"] == "running"
        assert metrics["uptime"] >= 0
        assert metrics["message_count"] == 0
        assert metrics["error_count"] == 0
