"""
Bot identity (mask) management and persona engine.

Provides mask templates, registry, and context-aware persona switching
for multi-identity bot operations.
"""
from .mask_manager import MaskManager
from .mask_registry import Mask, MaskType, MaskRegistry
from .mask_templates import MaskTemplateLibrary
from .persona_engine import PersonaEngine

__all__ = [
    "MaskRegistry",
    "Mask",
    "MaskType",
    "MaskManager",
    "PersonaEngine",
    "MaskTemplateLibrary",
]
