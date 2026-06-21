"""
Tests for agent system.
"""
import pytest
from src.agents.agent_core import Agent, AgentConfig, AgentRole, AgentState
from src.agents.agent_manager import AgentManager
from src.agents.memory import MemoryStore, MemoryEntry, MemoryCategory
import tempfile
import os

def test_agent_role():
    assert AgentRole.EXECUTIVE.value == "executive"
    assert AgentRole.JEWELRY.value == "jewelry"

def test_agent_config():
    config = AgentConfig(
        agent_id="test",
        name="Test Agent",
        role=AgentRole.SUPPORT,
        business_id="biz",
    )
    assert config.agent_id == "test"

def test_agent_init():
    config = AgentConfig(
        agent_id="test",
        name="Test",
        role=AgentRole.SUPPORT,
        business_id="biz",
    )
    agent = Agent(config)
    assert agent.state == AgentState.IDLE

def test_agent_manager():
    manager = AgentManager()
    config = AgentConfig(
        agent_id="test",
        name="Test",
        role=AgentRole.SUPPORT,
        business_id="biz",
    )
    agent = Agent(config)
    manager.register(agent)
    assert "test" in manager.list_agents()

def test_memory_store():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = os.path.join(tmpdir, "test.json")
        store = MemoryStore(state_file)
        entry = MemoryEntry(
            content="test memory",
            category=MemoryCategory.USER_PREFERENCE,
        )
        import asyncio
        asyncio.run(store.store(entry))
        results = store.search("test")
        assert len(results) == 1
        assert results[0].content == "test memory"
