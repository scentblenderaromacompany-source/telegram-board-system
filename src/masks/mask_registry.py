"""
Bot mask registry for managing different bot identities.
"""
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from pathlib import Path

class MaskType(Enum):
    SUPPORT = "support"
    SALES = "sales"
    CONTENT = "content"
    MONITOR = "monitor"
    CUSTOM = "custom"

@dataclass
class Mask:
    mask_id: str
    name: str
    mask_type: MaskType
    business_id: str
    display_name: str
    avatar_url: Optional[str] = None
    bio: str = ""
    response_style: str = "professional"
    tone: str = "friendly"
    emoji_enabled: bool = True
    sticker_packs: List[str] = field(default_factory=list)
    vocabulary: List[str] = field(default_factory=list)
    restricted_words: List[str] = field(default_factory=list)
    settings: Dict = field(default_factory=dict)

class MaskRegistry:
    def __init__(self, state_file: str = "config/masks.json"):
        self._masks: Dict[str, Mask] = {}
        self._state_file = Path(state_file)
        self._load()
    
    def _load(self):
        if self._state_file.exists():
            data = json.loads(self._state_file.read_text())
            for m_data in data.get("masks", []):
                m_data["mask_type"] = MaskType(m_data["mask_type"])
                mask = Mask(**m_data)
                self._masks[mask.mask_id] = mask
    
    def _save(self):
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        data = {"masks": []}
        for mask in self._masks.values():
            d = {
                "mask_id": mask.mask_id,
                "name": mask.name,
                "mask_type": mask.mask_type.value,
                "business_id": mask.business_id,
                "display_name": mask.display_name,
                "avatar_url": mask.avatar_url,
                "bio": mask.bio,
                "response_style": mask.response_style,
                "tone": mask.tone,
                "emoji_enabled": mask.emoji_enabled,
                "sticker_packs": mask.sticker_packs,
                "vocabulary": mask.vocabulary,
                "restricted_words": mask.restricted_words,
                "settings": mask.settings,
            }
            data["masks"].append(d)
        self._state_file.write_text(json.dumps(data, indent=2))
    
    def register(self, mask: Mask) -> Mask:
        self._masks[mask.mask_id] = mask
        self._save()
        return mask
    
    def get(self, mask_id: str) -> Optional[Mask]:
        return self._masks.get(mask_id)
    
    def list_by_business(self, business_id: str) -> List[Mask]:
        return [m for m in self._masks.values() if m.business_id == business_id]
    
    def list_by_type(self, mask_type: MaskType) -> List[Mask]:
        return [m for m in self._masks.values() if m.mask_type == mask_type]
    
    def delete(self, mask_id: str) -> bool:
        if mask_id in self._masks:
            del self._masks[mask_id]
            self._save()
            return True
        return False
