"""
Channel manager for CRUD operations on channels.
"""
import logging
from typing import List, Optional
from .channel_registry import Channel, ChannelRegistry, ChannelType, ChannelStatus

logger = logging.getLogger(__name__)

class ChannelManager:
    def __init__(self, registry: ChannelRegistry):
        self._registry = registry
    
    def create_channel(
        self,
        channel_id: str,
        name: str,
        business_id: str,
        channel_type: ChannelType,
        description: str = "",
        bot_id: Optional[str] = None,
        rate_limit: int = 30,
    ) -> Channel:
        """Create and register a new channel."""
        channel = Channel(
            channel_id=channel_id,
            name=name,
            business_id=business_id,
            channel_type=channel_type,
            description=description,
            bot_id=bot_id,
            rate_limit=rate_limit,
        )
        self._registry.register(channel)
        logger.info(f"Created channel: {name} ({channel_id}) for {business_id}")
        return channel
    
    def get_channel(self, channel_id: str) -> Optional[Channel]:
        """Get a channel by ID."""
        return self._registry.get(channel_id)
    
    def list_channels(self, business_id: Optional[str] = None) -> List[Channel]:
        """List channels, optionally filtered by business."""
        if business_id:
            return self._registry.list_by_business(business_id)
        return list(self._registry._channels.values())
    
    def update_channel(self, channel_id: str, **kwargs) -> Optional[Channel]:
        """Update channel properties."""
        return self._registry.update(channel_id, **kwargs)
    
    def delete_channel(self, channel_id: str) -> bool:
        """Delete a channel."""
        return self._registry.delete(channel_id)
    
    def activate_channel(self, channel_id: str) -> Optional[Channel]:
        """Activate a channel."""
        return self._registry.update(channel_id, status=ChannelStatus.ACTIVE)
    
    def deactivate_channel(self, channel_id: str) -> Optional[Channel]:
        """Deactivate a channel."""
        return self._registry.update(channel_id, status=ChannelStatus.INACTIVE)
