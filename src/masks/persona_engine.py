"""
Enhanced persona engine with context-aware responses, sentiment analysis,
and adaptive tone matching. Inspired by TRAPAGENT Eve persona system.
"""
import re
import logging
from typing import Dict, Optional, List, Tuple
from .mask_registry import Mask, MaskRegistry

logger = logging.getLogger(__name__)

class PersonaEngine:
    """
    Advanced persona engine with:
    - Context-aware response generation
    - Sentiment detection
    - Tone adaptation
    - A/B testing support
    """
    
    def __init__(self, registry: MaskRegistry):
        self._registry = registry
        self._style_templates = self._default_templates()
        self._sentiment_patterns = self._build_sentiment_patterns()
        self._ab_variants: Dict[str, List[Dict]] = {}
    
    def _default_templates(self) -> Dict[str, Dict]:
        return {
            "professional": {
                "greeting": "Hello! How can I assist you today?",
                "farewell": "Thank you for reaching out. Have a great day!",
                "fallback": "I'm not sure I understand. Could you rephrase that?",
                "tone": "formal",
                "emoji": False,
                "max_length": 4096,
                "response_style": "concise",
            },
            "friendly": {
                "greeting": "Hey there! How can I help?",
                "farewell": "Thanks for chatting! See you soon!",
                "fallback": "Hmm, I'm not quite sure what you mean. Can you tell me more?",
                "tone": "casual",
                "emoji": True,
                "max_length": 4096,
                "response_style": "warm",
            },
            "support": {
                "greeting": "Welcome to support! I'm here to help.",
                "farewell": "Glad I could help! Let us know if you need anything else.",
                "fallback": "Let me look into that for you. Can you provide more details?",
                "tone": "helpful",
                "emoji": False,
                "max_length": 4096,
                "response_style": "thorough",
            },
            "sales": {
                "greeting": "Welcome! Interested in our products?",
                "farewell": "Thanks for your interest! Feel free to reach out anytime.",
                "fallback": "Great question! Let me find the best option for you.",
                "tone": "enthusiastic",
                "emoji": True,
                "max_length": 4096,
                "response_style": "persuasive",
            },
            "technical": {
                "greeting": "Ready to help with technical questions.",
                "farewell": "Technical support session ended.",
                "fallback": "Could you provide more technical details or error messages?",
                "tone": "precise",
                "emoji": False,
                "max_length": 4096,
                "response_style": "detailed",
            },
            "heritage": {
                "greeting": "Welcome to Caspers Heritage! Each piece tells a story.",
                "farewell": "Thank you for your interest in our curated collection.",
                "fallback": "Let me find the perfect piece for you.",
                "tone": "warm",
                "emoji": True,
                "max_length": 4096,
                "response_style": "storytelling",
            },
        }
    
    def _build_sentiment_patterns(self) -> Dict[str, List[str]]:
        return {
            "positive": ["great", "love", "awesome", "excellent", "perfect", "amazing", "wonderful", "fantastic"],
            "negative": ["bad", "hate", "terrible", "awful", "horrible", "worst", "annoying", "frustrated"],
            "question": ["?", "how", "what", "why", "when", "where", "who", "can you", "could you"],
            "urgent": ["urgent", "asap", "immediately", "now", "quickly", "emergency", "critical"],
            "confused": ["confused", "don't understand", "unclear", "what do you mean", "explain"],
        }
    
    def detect_sentiment(self, text: str) -> Dict[str, float]:
        """Detect sentiment in text."""
        text_lower = text.lower()
        scores = {}
        for sentiment, patterns in self._sentiment_patterns.items():
            count = sum(1 for p in patterns if p in text_lower)
            scores[sentiment] = min(count / max(len(text.split()), 1), 1.0)
        return scores
    
    def get_style_template(self, style: str) -> Dict:
        return self._style_templates.get(style, self._style_templates["professional"])
    
    def apply_persona(self, mask: Mask, message: str, context: Dict = None) -> str:
        """Apply persona rules to outgoing message with context awareness."""
        template = self.get_style_template(mask.response_style)
        
        if mask.restricted_words:
            for word in mask.restricted_words:
                message = re.sub(re.escape(word), "***", message, flags=re.IGNORECASE)
        
        if mask.emoji_enabled and template.get("emoji"):
            message = self._apply_contextual_emoji(message, context)
        
        if len(message) > template.get("max_length", 4096):
            message = message[:template["max_length"] - 3] + "..."
        
        return message
    
    def _apply_contextual_emoji(self, message: str, context: Dict = None) -> str:
        """Apply emoji based on message context."""
        if not context:
            return message
        
        sentiment = context.get("sentiment", {})
        if sentiment.get("positive", 0) > 0.3:
            if "!" in message:
                return message
        elif sentiment.get("urgent", 0) > 0.3:
            return message
        elif sentiment.get("question", 0) > 0.3:
            return message
        
        return message
    
    def get_greeting(self, mask: Mask, context: Dict = None) -> str:
        template = self.get_style_template(mask.response_style)
        name = mask.display_name
        greeting = template["greeting"]
        if context and context.get("time_of_day"):
            hour = context["time_of_day"]
            if hour < 12:
                greeting = f"Good morning! {greeting}"
            elif hour < 17:
                greeting = f"Good afternoon! {greeting}"
            else:
                greeting = f"Good evening! {greeting}"
        return f"{name}: {greeting}"
    
    def get_farewell(self, mask: Mask) -> str:
        template = self.get_style_template(mask.response_style)
        return f"{mask.display_name}: {template['farewell']}"
    
    def get_fallback(self, mask: Mask, sentiment: Dict = None) -> str:
        template = self.get_style_template(mask.response_style)
        fallback = template["fallback"]
        if sentiment and sentiment.get("confused", 0) > 0.3:
            fallback = "I notice you might be confused. Let me try explaining differently."
        return f"{mask.display_name}: {fallback}"
    
    def register_style(self, name: str, template: Dict):
        self._style_templates[name] = template
        logger.info(f"Registered style template: {name}")
    
    def register_ab_variant(self, style: str, variants: List[Dict]):
        """Register A/B testing variants for a style."""
        self._ab_variants[style] = variants
    
    def get_ab_variant(self, style: str, user_id: int) -> Optional[Dict]:
        """Get A/B test variant for a user."""
        variants = self._ab_variants.get(style)
        if not variants:
            return None
        idx = user_id % len(variants)
        return variants[idx]
