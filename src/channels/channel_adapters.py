"""
Channel adapters for different messaging platforms.
"""
import logging
from typing import Dict, Optional, Any, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseChannelAdapter(ABC):
    """Base class for channel adapters."""
    
    def __init__(self, channel_id: str, config: Dict):
        self.channel_id = channel_id
        self.config = config
        self._connected = False
    
    @abstractmethod
    async def connect(self): ...
    
    @abstractmethod
    async def disconnect(self): ...
    
    @abstractmethod
    async def send_message(self, chat_id: str, text: str, **kwargs) -> Any: ...
    
    @abstractmethod
    async def send_media(self, chat_id: str, media_type: str, media_id: str, **kwargs) -> Any: ...
    
    @abstractmethod
    async def edit_message(self, chat_id: str, message_id: int, text: str, **kwargs) -> Any: ...
    
    @abstractmethod
    async def delete_message(self, chat_id: str, message_id: int) -> bool: ...
    
    @property
    def is_connected(self) -> bool:
        return self._connected


class TelegramAdapter(BaseChannelAdapter):
    """Telegram Bot API adapter."""
    
    def __init__(self, channel_id: str, config: Dict):
        super().__init__(channel_id, config)
        self._app = None
        self._bot = None
    
    async def connect(self):
        try:
            from telegram.ext import Application
            self._app = Application.builder().token(self.config["token"]).build()
            await self._app.initialize()
            await self._app.start()
            self._bot = self._app.bot
            self._connected = True
            logger.info(f"Telegram adapter {self.channel_id} connected")
        except Exception as e:
            logger.error(f"Telegram connection failed: {e}")
            raise
    
    async def disconnect(self):
        if self._app:
            await self._app.stop()
            await self._app.shutdown()
        self._connected = False
    
    async def send_message(self, chat_id: str, text: str, **kwargs) -> Any:
        if self._bot:
            return await self._bot.send_message(chat_id=chat_id, text=text, **kwargs)
    
    async def send_photo(self, chat_id: str, photo: str, caption: str = "", **kwargs) -> Any:
        if self._bot:
            return await self._bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, **kwargs)
    
    async def send_document(self, chat_id: str, document: str, **kwargs) -> Any:
        if self._bot:
            return await self._bot.send_document(chat_id=chat_id, document=document, **kwargs)
    
    async def send_media(self, chat_id: str, media_type: str, media_id: str, **kwargs) -> Any:
        if media_type == "photo":
            return await self.send_photo(chat_id, media_id, **kwargs)
        elif media_type == "document":
            return await self.send_document(chat_id, media_id, **kwargs)
    
    async def edit_message(self, chat_id: str, message_id: int, text: str, **kwargs) -> Any:
        if self._bot:
            return await self._bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, **kwargs)
    
    async def delete_message(self, chat_id: str, message_id: int) -> bool:
        if self._bot:
            try:
                await self._bot.delete_message(chat_id=chat_id, message_id=message_id)
                return True
            except Exception:
                return False
        return False
    
    async def send_inline_keyboard(self, chat_id: str, text: str, buttons: List[List[Dict]], **kwargs) -> Any:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = []
        for row in buttons:
            keyboard_row = [InlineKeyboardButton(**btn) for btn in row]
            keyboard.append(keyboard_row)
        markup = InlineKeyboardMarkup(keyboard)
        return await self.send_message(chat_id, text, reply_markup=markup, **kwargs)


class SlackAdapter(BaseChannelAdapter):
    """Slack adapter."""
    
    async def connect(self):
        logger.info(f"Slack adapter {self.channel_id} connected")
        self._connected = True
    
    async def disconnect(self):
        self._connected = False
    
    async def send_message(self, chat_id: str, text: str, **kwargs) -> Any:
        logger.info(f"Slack send to {chat_id}: {text[:50]}...")
    
    async def send_media(self, chat_id: str, media_type: str, media_id: str, **kwargs) -> Any:
        pass
    
    async def edit_message(self, chat_id: str, message_id: int, text: str, **kwargs) -> Any:
        pass
    
    async def delete_message(self, chat_id: str, message_id: int) -> bool:
        return True


class WebAdapter(BaseChannelAdapter):
    """Web chat adapter."""
    
    async def connect(self):
        self._connected = True
    
    async def disconnect(self):
        self._connected = False
    
    async def send_message(self, chat_id: str, text: str, **kwargs) -> Any:
        return {"chat_id": chat_id, "text": text, "type": "web"}
    
    async def send_media(self, chat_id: str, media_type: str, media_id: str, **kwargs) -> Any:
        pass
    
    async def edit_message(self, chat_id: str, message_id: int, text: str, **kwargs) -> Any:
        pass
    
    async def delete_message(self, chat_id: str, message_id: int) -> bool:
        return True
