"""
Core agent framework.
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class AgentState(Enum):
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    PROCESSING = "processing"
    STOPPING = "stopping"
    ERROR = "error"


class AgentRole(Enum):
    EXECUTIVE = "executive"
    CONTENT = "content"
    JEWELRY = "jewelry"
    RESEARCH = "research"
    SUPPORT = "support"
    CUSTOM = "custom"


@dataclass
class Tool:
    name: str
    description: str
    handler: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    requires_auth: bool = False
    category: str = "general"


@dataclass
class Skill:
    name: str
    description: str
    instructions: str
    tools: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)


@dataclass
class AgentConfig:
    agent_id: str
    name: str
    role: AgentRole
    business_id: str
    model: str = "gpt-4"
    system_prompt: str = ""
    channels: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    memory_enabled: bool = True
    max_context_length: int = 8192
    temperature: float = 0.7
    settings: Dict[str, Any] = field(default_factory=dict)


class Agent:
    """
    Production agent with multi-channel support, tools, skills, and memory.
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState.IDLE
        self._tools: Dict[str, Tool] = {}
        self._skills: Dict[str, Skill] = {}
        self._channels: Dict[str, Any] = {}
        self._memory = None
        self._conversation_history: Dict[str, List] = {}
        self._start_time = 0.0
        self._message_count = 0
        self._error_count = 0

    async def start(self):
        self.state = AgentState.STARTING
        self._start_time = time.time()
        logger.info(f"Agent {self.config.agent_id} starting...")
        self.state = AgentState.RUNNING
        logger.info(f"Agent {self.config.agent_id} started")

    async def stop(self):
        self.state = AgentState.STOPPING
        logger.info(f"Agent {self.config.agent_id} stopped")
        self.state = AgentState.IDLE

    def register_tool(self, tool: Tool):
        self._tools[tool.name] = tool

    def register_skill(self, skill: Skill):
        self._skills[skill.name] = skill

    def register_channel(self, channel_id: str, channel_adapter: Any):
        self._channels[channel_id] = channel_adapter

    async def process_message(self, channel_id: str, user_id: str, message: str, context: Dict = None) -> str:
        self.state = AgentState.PROCESSING
        self._message_count += 1
        try:
            history = self._conversation_history.get(f"{channel_id}:{user_id}", [])
            history.append({"role": "user", "content": message})
            response = await self._generate_response(message, history, context or {})
            history.append({"role": "assistant", "content": response})
            self._conversation_history[f"{channel_id}:{user_id}"] = history[-50:]
            self.state = AgentState.RUNNING
            return response
        except Exception as e:
            self._error_count += 1
            self.state = AgentState.ERROR
            logger.error(f"Agent {self.config.agent_id} error: {e}")
            return "I encountered an error processing your request."

    async def _generate_response(self, message: str, history: List, context: Dict) -> str:
        for tool_name, tool in self._tools.items():
            if tool_name in message.lower():
                try:
                    return await tool.handler(message, context)
                except Exception as e:
                    logger.error(f"Tool {tool_name} error: {e}")
        return f"I received your message: '{message}'. I'm {self.config.name}."

    def get_metrics(self) -> Dict:
        return {
            "agent_id": self.config.agent_id,
            "state": self.state.value,
            "uptime": time.time() - self._start_time,
            "message_count": self._message_count,
            "error_count": self._error_count,
            "tools_registered": len(self._tools),
            "skills_registered": len(self._skills),
        }
