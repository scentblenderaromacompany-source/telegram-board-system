"""
Message router for directing messages to appropriate channels and bots.
"""
import logging
from typing import Dict, Optional, Callable, Any
from .channel_registry import ChannelRegistry, ChannelType

logger = logging.getLogger(__name__)

class MessageRouter:
    def __init__(self, registry: ChannelRegistry):
        self._registry = registry
        self._routes: Dict[str, str] = {}  # business_id -> channel_id
        self._handlers: Dict[str, Callable] = {}  # channel_id -> handler
    
    def set_route(self, business_id: str, channel_id: str):
        """Set default route for a business."""
        self._routes[business_id] = channel_id
        logger.info(f"Set route: {business_id} -> {channel_id}")
    
    def register_handler(self, channel_id: str, handler: Callable):
        """Register a message handler for a channel."""
        self._handlers[channel_id] = handler
    
    def resolve_channel(
        self,
        business_id: str,
        channel_type: Optional[ChannelType] = None,
    ) -> Optional[str]:
        """Resolve the target channel for a business."""
        # Check explicit route first
        if business_id in self._routes:
            return self._routes[business_id]
        
        # Find by business and type
        channels = self._registry.list_by_business(business_id)
        if channel_type:
            channels = [ch for ch in channels if ch.channel_type == channel_type]
        
        if channels:
            return channels[0].channel_id
        return None
    
    async def route_message(
        self,
        business_id: str,
        chat_id: str,
        text: str,
        channel_type: Optional[ChannelType] = None,
        **kwargs,
    ) -> bool:
        """Route a message to the appropriate channel."""
        channel_id = self.resolve_channel(business_id, channel_type)
        if not channel_id:
            logger.warning(f"No channel found for {business_id}")
            return False
        
        handler = self._handlers.get(channel_id)
        if handler:
            await handler(channel_id, chat_id, text, **kwargs)
            return True
        
        logger.warning(f"No handler for channel {channel_id}")
        return False
    
    def get_routes(self) -> Dict[str, str]:
        """Get all configured routes."""
        return dict(self._routes)
