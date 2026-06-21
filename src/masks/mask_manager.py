"""
Mask manager for handling mask assignments and switching.
"""
import logging
from typing import Dict, List, Optional
from .mask_registry import Mask, MaskRegistry, MaskType
from .persona_engine import PersonaEngine

logger = logging.getLogger(__name__)

class MaskManager:
    def __init__(self, registry: MaskRegistry):
        self._registry = registry
        self._persona_engine = PersonaEngine(registry)
        self._assignments: Dict[str, str] = {}  # bot_id -> mask_id
        self._rotation: Dict[str, List[str]] = {}  # business_id -> [mask_ids]
    
    def assign_mask(self, bot_id: str, mask_id: str) -> bool:
        """Assign a mask to a bot."""
        mask = self._registry.get(mask_id)
        if mask:
            self._assignments[bot_id] = mask_id
            logger.info(f"Assigned mask {mask_id} to bot {bot_id}")
            return True
        return False
    
    def unassign_mask(self, bot_id: str):
        """Remove mask assignment from a bot."""
        self._assignments.pop(bot_id, None)
    
    def get_mask_for_bot(self, bot_id: str) -> Optional[Mask]:
        """Get the mask assigned to a bot."""
        mask_id = self._assignments.get(bot_id)
        if mask_id:
            return self._registry.get(mask_id)
        return None
    
    def set_rotation(self, business_id: str, mask_ids: List[str]):
        """Set mask rotation for a business."""
        self._rotation[business_id] = mask_ids
    
    def get_next_mask(self, business_id: str) -> Optional[Mask]:
        """Get next mask in rotation for a business."""
        mask_ids = self._rotation.get(business_id, [])
        if not mask_ids:
            return None
        
        # Simple round-robin - could be improved with state tracking
        # For now, return first mask
        return self._registry.get(mask_ids[0])
    
    def create_mask(
        self,
        mask_id: str,
        name: str,
        mask_type: MaskType,
        business_id: str,
        display_name: str,
        **kwargs,
    ) -> Mask:
        """Create and register a new mask."""
        from .mask_registry import Mask
        mask = Mask(
            mask_id=mask_id,
            name=name,
            mask_type=mask_type,
            business_id=business_id,
            display_name=display_name,
            **kwargs,
        )
        self._registry.register(mask)
        logger.info(f"Created mask: {name} ({mask_id}) for {business_id}")
        return mask
    
    def list_masks(self, business_id: Optional[str] = None) -> List[Mask]:
        """List masks, optionally filtered by business."""
        if business_id:
            return self._registry.list_by_business(business_id)
        return list(self._registry._masks.values())
    
    def apply_persona(self, bot_id: str, message: str) -> str:
        """Apply bot's mask persona to a message."""
        mask = self.get_mask_for_bot(bot_id)
        if mask:
            return self._persona_engine.apply_persona(mask, message)
        return message
    
    @property
    def persona_engine(self) -> PersonaEngine:
        """Access the persona engine."""
        return self._persona_engine
