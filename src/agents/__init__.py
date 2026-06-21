"""
Agent framework with tools, skills, memory, and orchestration.

Provides a pluggable agent system with role-based configuration,
long-term memory, and multi-agent management.
"""
from .agent_core import Agent, AgentConfig, AgentRole, AgentState
from .agent_manager import AgentManager
from .memory import MemoryCategory, MemoryEntry, MemoryStore

__all__ = [
    "Agent",
    "AgentConfig",
    "AgentRole",
    "AgentState",
    "AgentManager",
    "MemoryStore",
    "MemoryEntry",
    "MemoryCategory",
]
