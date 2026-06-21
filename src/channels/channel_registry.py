"""
Channel registry for managing Telegram channels across businesses.
"""
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from pathlib import Path

class ChannelType(Enum):
    BROADCAST = "broadcast"
    SUPPORT = "support"
    INTERNAL = "internal"
    MONITORING = "monitoring"

class ChannelStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

@dataclass
class Channel:
    channel_id: str
    name: str
    business_id: str
    channel_type: ChannelType
    status: ChannelStatus = ChannelStatus.ACTIVE
    description: str = ""
    bot_id: Optional[str] = None
    rate_limit: int = 30
    settings: Dict = field(default_factory=dict)

class ChannelRegistry:
    def __init__(self, state_file: str = "config/channels.json"):
        self._channels: Dict[str, Channel] = {}
        self._state_file = Path(state_file)
        self._load()
    
    def _load(self):
        """Load channels from state file."""
        if self._state_file.exists():
            data = json.loads(self._state_file.read_text())
            for ch_data in data.get("channels", []):
                ch = Channel(**ch_data)
                self._channels[ch.channel_id] = ch
    
    def _save(self):
        """Persist channels to state file."""
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        data = {"channels": [self._to_dict(ch) for ch in self._channels.values()]}
        self._state_file.write_text(json.dumps(data, indent=2))
    
    def _to_dict(self, ch: Channel) -> Dict:
        return {
            "channel_id": ch.channel_id,
            "name": ch.name,
            "business_id": ch.business_id,
            "channel_type": ch.channel_type.value,
            "status": ch.status.value,
            "description": ch.description,
            "bot_id": ch.bot_id,
            "rate_limit": ch.rate_limit,
            "settings": ch.settings,
        }
    
    def register(self, channel: Channel) -> Channel:
        self._channels[channel.channel_id] = channel
        self._save()
        return channel
    
    def get(self, channel_id: str) -> Optional[Channel]:
        return self._channels.get(channel_id)
    
    def list_by_business(self, business_id: str) -> List[Channel]:
        return [ch for ch in self._channels.values() if ch.business_id == business_id]
    
    def list_by_type(self, channel_type: ChannelType) -> List[Channel]:
        return [ch for ch in self._channels.values() if ch.channel_type == channel_type]
    
    def update(self, channel_id: str, **kwargs) -> Optional[Channel]:
        ch = self._channels.get(channel_id)
        if ch:
            for key, value in kwargs.items():
                if hasattr(ch, key):
                    setattr(ch, key, value)
            self._save()
        return ch
    
    def delete(self, channel_id: str) -> bool:
        if channel_id in self._channels:
            del self._channels[channel_id]
            self._save()
            return True
        return False
