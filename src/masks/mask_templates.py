"""
Pre-built mask templates for common use cases.
"""
from typing import Dict, List
from .mask_registry import Mask, MaskType

class MaskTemplateLibrary:
    """
    Library of pre-built mask templates.
    """
    
    TEMPLATES = {
        "customer_support": {
            "mask_type": MaskType.SUPPORT,
            "response_style": "support",
            "tone": "helpful",
            "emoji_enabled": False,
            "bio": "Customer support agent for your business",
            "restricted_words": [],
        },
        "sales_rep": {
            "mask_type": MaskType.SALES,
            "response_style": "sales",
            "tone": "enthusiastic",
            "emoji_enabled": True,
            "bio": "Sales representative - here to help you find the perfect product",
            "restricted_words": [],
        },
        "jewelry_expert": {
            "mask_type": MaskType.CUSTOM,
            "response_style": "heritage",
            "tone": "warm",
            "emoji_enabled": True,
            "bio": "Caspers Heritage Jewelry expert - each piece tells a story",
            "restricted_words": [],
            "settings": {
                "business": "caspers_heritage",
                "specialties": ["vintage", "estate", "fine jewelry", "appraisals"],
            },
        },
        "content_creator": {
            "mask_type": MaskType.CONTENT,
            "response_style": "friendly",
            "tone": "creative",
            "emoji_enabled": True,
            "bio": "Content creation assistant",
            "restricted_words": [],
        },
        "tech_support": {
            "mask_type": MaskType.SUPPORT,
            "response_style": "technical",
            "tone": "precise",
            "emoji_enabled": False,
            "bio": "Technical support specialist",
            "restricted_words": [],
        },
        "monitor_bot": {
            "mask_type": MaskType.MONITOR,
            "response_style": "professional",
            "tone": "neutral",
            "emoji_enabled": False,
            "bio": "System monitoring and alerting",
            "restricted_words": [],
        },
    }
    
    @classmethod
    def get_template(cls, name: str) -> Dict:
        return cls.TEMPLATES.get(name, cls.TEMPLATES["customer_support"])
    
    @classmethod
    def list_templates(cls) -> List[str]:
        return list(cls.TEMPLATES.keys())
    
    @classmethod
    def create_mask_from_template(cls, mask_id: str, name: str, business_id: str, template_name: str, **overrides) -> Mask:
        template = cls.get_template(template_name)
        merged = {**template, **overrides}
        return Mask(
            mask_id=mask_id,
            name=name,
            mask_type=merged.get("mask_type", MaskType.CUSTOM),
            business_id=business_id,
            display_name=name,
            bio=merged.get("bio", ""),
            response_style=merged.get("response_style", "professional"),
            tone=merged.get("tone", "friendly"),
            emoji_enabled=merged.get("emoji_enabled", True),
            restricted_words=merged.get("restricted_words", []),
            settings=merged.get("settings", {}),
        )
