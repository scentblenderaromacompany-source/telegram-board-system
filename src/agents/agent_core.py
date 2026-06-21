"""
Core agent framework with 9Router AI integration.
"""
import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

import httpx

logger = logging.getLogger(__name__)

# 9Router configuration
NINE_ROUTER_URL = os.getenv("TBS_9ROUTER_URL", "https://r6nmz69.abc-tunnel.us/v1")
NINE_ROUTER_KEY = os.getenv("TBS_9ROUTER_KEY", "sk-94d9c38354c67d27-xo9t07-d57cbd5d")


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
    model: str = "if/kimi-k2-thinking"
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
    Uses 9Router for AI model calls with automatic fallback.
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
        self._client: Optional[httpx.AsyncClient] = None

    async def start(self):
        self.state = AgentState.STARTING
        self._start_time = time.time()
        self._client = httpx.AsyncClient(
            base_url=NINE_ROUTER_URL,
            headers={
                "Authorization": f"Bearer {NINE_ROUTER_KEY}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
        logger.info("Agent %s starting (model: %s)", self.config.agent_id, self.config.model)
        self.state = AgentState.RUNNING
        logger.info("Agent %s started", self.config.agent_id)

    async def stop(self):
        self.state = AgentState.STOPPING
        if self._client:
            await self._client.aclose()
        logger.info("Agent %s stopped", self.config.agent_id)
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
            logger.error("Agent %s error: %s", self.config.agent_id, e)
            return "I encountered an error processing your request."

    async def _generate_response(self, message: str, history: List, context: Dict) -> str:
        # Check for tool triggers first
        for tool_name, tool in self._tools.items():
            if tool_name in message.lower():
                try:
                    return await tool.handler(message, context)
                except Exception as e:
                    logger.error("Tool %s error: %s", tool_name, e)

        # Call 9Router AI API
        messages = []
        if self.config.system_prompt:
            messages.append({"role": "system", "content": self.config.system_prompt})
        messages.extend(history[-20:])  # Keep last 20 messages for context

        try:
            response = await self._client.post(
                "/chat/completions",
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": self.config.temperature,
                    "max_tokens": 1024,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.error("9Router API error: %s", e.response.status_code)
            return f"AI service temporarily unavailable (HTTP {e.response.status_code})."
        except Exception as e:
            logger.error("9Router connection error: %s", e)
            return "AI service temporarily unavailable. Please try again."

    def get_metrics(self) -> Dict:
        return {
            "agent_id": self.config.agent_id,
            "state": self.state.value,
            "model": self.config.model,
            "uptime": time.time() - self._start_time,
            "message_count": self._message_count,
            "error_count": self._error_count,
            "tools_registered": len(self._tools),
            "skills_registered": len(self._skills),
        }
