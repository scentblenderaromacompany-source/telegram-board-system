"""
Async message queue for reliable message delivery.
"""
import asyncio
from dataclasses import dataclass, field
from typing import Callable, Any, Optional
from enum import Enum

class Priority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

@dataclass(order=True)
class Message:
    priority: Priority
    chat_id: str = field(compare=False)
    text: str = field(compare=False)
    bot_id: str = field(compare=False)
    reply_to: Optional[str] = field(default=None, compare=False)
    metadata: dict = field(default_factory=dict, compare=False)

class MessageQueue:
    def __init__(self, max_size: int = 1000):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_size)
        self._handlers: dict = {}
        self._running = False
    
    def register_handler(self, bot_id: str, handler: Callable):
        self._handlers[bot_id] = handler
    
    async def enqueue(self, message: Message):
        await self._queue.put(message)
    
    async def start(self):
        self._running = True
        while self._running:
            try:
                msg = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                handler = self._handlers.get(msg.bot_id)
                if handler:
                    await handler(msg)
            except asyncio.TimeoutError:
                continue
    
    def stop(self):
        self._running = False
