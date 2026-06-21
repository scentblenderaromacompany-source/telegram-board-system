"""
Telegram forum topic management.
Based on Hermes forum topic support patterns.
"""
import logging
from typing import Dict, Optional, List, Any

logger = logging.getLogger(__name__)

class TelegramForumManager:
    """
    Manages Telegram supergroup forum topics.
    Supports Bot API 9.4+ forum topic creation and management.
    """
    
    def __init__(self, bot_adapter):
        self._bot = bot_adapter
        self._topics: Dict[int, Dict[str, Any]] = {}
    
    async def create_topic(self, chat_id: int, name: str, icon_color: int = None) -> Optional[Dict]:
        """Create a new forum topic."""
        try:
            from telegram import ForumTopic
            if self._bot._bot:
                topic = await self._bot._bot.create_forum_topic(
                    chat_id=chat_id,
                    name=name,
                    icon_color=icon_color,
                )
                topic_info = {
                    "message_thread_id": topic.message_thread_id,
                    "name": name,
                    "icon_color": icon_color,
                }
                self._topics[topic.message_thread_id] = topic_info
                return topic_info
        except Exception as e:
            logger.error(f"Failed to create forum topic: {e}")
        return None
    
    async def send_to_topic(self, chat_id: int, thread_id: int, text: str, **kwargs) -> Any:
        """Send a message to a specific forum topic."""
        return await self._bot.send_message(
            chat_id=chat_id,
            text=text,
            message_thread_id=thread_id,
            **kwargs,
        )
    
    async def close_topic(self, chat_id: int, thread_id: int) -> bool:
        """Close a forum topic."""
        try:
            if self._bot._bot:
                await self._bot._bot.close_forum_topic(chat_id=chat_id, message_thread_id=thread_id)
                return True
        except Exception as e:
            logger.error(f"Failed to close topic: {e}")
        return False
    
    async def reopen_topic(self, chat_id: int, thread_id: int) -> bool:
        try:
            if self._bot._bot:
                await self._bot._bot.reopen_forum_topic(chat_id=chat_id, message_thread_id=thread_id)
                return True
        except Exception as e:
            logger.error(f"Failed to reopen topic: {e}")
        return False
    
    async def edit_topic(self, chat_id: int, thread_id: int, name: str) -> bool:
        try:
            if self._bot._bot:
                await self._bot._bot.edit_forum_topic(chat_id=chat_id, message_thread_id=thread_id, name=name)
                return True
        except Exception as e:
            logger.error(f"Failed to edit topic: {e}")
        return False
    
    async def delete_topic(self, chat_id: int, thread_id: int) -> bool:
        try:
            if self._bot._bot:
                await self._bot._bot.delete_forum_topic(chat_id=chat_id, message_thread_id=thread_id)
                self._topics.pop(thread_id, None)
                return True
        except Exception as e:
            logger.error(f"Failed to delete topic: {e}")
        return False
    
    def get_topic(self, thread_id: int) -> Optional[Dict]:
        return self._topics.get(thread_id)
    
    def list_topics(self) -> List[Dict]:
        return list(self._topics.values())
