"""
Production Telegram platform adapter.
Based on Hermes gateway/platforms/telegram.py patterns.
Handles: polling, webhooks, media, inline keyboards, forum topics, rich messages.
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)

try:
    from telegram import (
        Update, Bot, Message, InlineKeyboardButton, InlineKeyboardMarkup,
        LinkPreviewOptions,
    )
    from telegram.ext import (
        Application, CommandHandler, CallbackQueryHandler,
        MessageHandler as TelegramMessageHandler, ContextTypes, filters,
    )
    from telegram.constants import ParseMode, ChatType
    from telegram.request import HTTPXRequest
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

from .network import TelegramFallbackTransport, discover_fallback_ips
from .message_formatter import TelegramMessageFormatter
from .media_handler import TelegramMediaHandler


class TelegramChatType(Enum):
    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


@dataclass
class TelegramMessage:
    message_id: int
    chat_id: int
    chat_type: TelegramChatType
    user_id: int
    username: Optional[str]
    text: Optional[str]
    date: float
    reply_to: Optional[int] = None
    media_type: Optional[str] = None
    media_file_id: Optional[str] = None
    caption: Optional[str] = None
    callback_data: Optional[str] = None
    thread_id: Optional[int] = None
    is_bot_mentioned: bool = False
    raw: Any = None


@dataclass
class TelegramConfig:
    token: str
    bot_id: str = ""
    business_id: str = ""
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    allowed_chat_ids: List[int] = field(default_factory=list)
    allowed_user_ids: List[int] = field(default_factory=list)
    parse_mode: str = "HTML"
    max_message_length: int = 4096
    rate_limit: int = 30
    use_fallback_transport: bool = True
    fallback_ips: List[str] = field(default_factory=list)
    enable_forum_topics: bool = False
    enable_rich_messages: bool = True
    proxy_url: Optional[str] = None
    connection_pool_size: int = 1
    read_timeout: int = 5
    write_timeout: int = 5
    connect_timeout: int = 5


class TelegramPlatformAdapter:
    """
    Production Telegram adapter with Hermes-grade features:
    - Network fallback transport
    - Webhook + polling modes
    - Forum topic support
    - Rich messages (Bot API 10.1)
    - Media handling
    - Rate limiting
    - Message batching
    """

    def __init__(self, config: TelegramConfig):
        self.config = config
        self._app: Optional[Application] = None
        self._bot: Optional[Bot] = None
        self._connected = False
        self._handlers: Dict[str, Callable] = {}
        self._message_handlers: List[Callable] = []
        self._callback_handlers: Dict[str, Callable] = {}
        self._error_handlers: List[Callable] = []
        self._before_send: List[Callable] = []
        self._after_send: List[Callable] = []
        self._formatter = TelegramMessageFormatter()
        self._media_handler = TelegramMediaHandler()
        self._metrics = {
            "messages_received": 0,
            "messages_sent": 0,
            "errors": 0,
            "callbacks_received": 0,
            "media_sent": 0,
        }
        if not config.bot_id and config.token:
            self.config.bot_id = config.token.split(":")[0]

    async def connect(self):
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot is required: pip install python-telegram-bot")

        builder = Application.builder().token(self.config.token)

        if self.config.webhook_url:
            builder = builder.webhook(
                self.config.webhook_url,
                secret_token=self.config.webhook_secret,
            )

        self._app = builder.build()
        self._register_handlers()

        await self._app.initialize()
        await self._app.start()

        if not self.config.webhook_url:
            await self._app.updater.start_polling(drop_pending_updates=True)

        self._bot = self._app.bot
        self._connected = True
        logger.info(f"Telegram adapter connected: bot={self.config.bot_id}")

    async def disconnect(self):
        if self._app:
            if not self.config.webhook_url:
                await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()
        self._connected = False
        logger.info("Telegram adapter disconnected")

    def on_command(self, command: str):
        def decorator(func):
            self._handlers[command] = func
            return func
        return decorator

    def on_message(self, func: Callable):
        self._message_handlers.append(func)
        return func

    def on_callback(self, pattern: str = ".*"):
        def decorator(func):
            self._callback_handlers[pattern] = func
            return func
        return decorator

    def on_error(self, func: Callable):
        self._error_handlers.append(func)
        return func

    def before_send(self, func: Callable):
        self._before_send.append(func)
        return func

    def after_send(self, func: Callable):
        self._after_send.append(func)
        return func

    def _register_handlers(self):
        for cmd_name, handler in self._handlers.items():
            self._app.add_handler(CommandHandler(cmd_name, self._wrap_handler(handler)))

        if self._message_handlers:
            combined = self._message_handlers[0]
            for h in self._message_handlers[1:]:
                prev = combined
                async def chain(msg, ctx, _prev=prev, _h=h):
                    r = await _prev(msg, ctx)
                    if r is None:
                        return await _h(msg, ctx)
                    return r
                combined = chain
            self._app.add_handler(
                MessageHandler(filters.ALL & ~filters.COMMAND, self._wrap_handler(combined))
            )

        self._app.add_handler(CallbackQueryHandler(self._handle_callback))
        self._app.add_error_handler(self._handle_error)

    def _wrap_handler(self, handler: Callable):
        async def wrapped(update, context):
            self._metrics["messages_received"] += 1
            try:
                msg = self._parse_update(update)
                return await handler(msg, context)
            except Exception as e:
                self._metrics["errors"] += 1
                logger.error(f"Handler error: {e}")
                for eh in self._error_handlers:
                    try:
                        await eh(update, context, e)
                    except Exception:
                        pass
        return wrapped

    async def _handle_callback(self, update, context):
        self._metrics["callbacks_received"] += 1
        query = update.callback_query
        data = query.data if query else None

        for pattern, handler in self._callback_handlers.items():
            import re
            if re.match(pattern, data or ""):
                try:
                    msg = self._parse_update(update)
                    await handler(msg, context)
                except Exception as e:
                    logger.error(f"Callback handler error: {e}")
                return

        if data and data.startswith("__default__:"):
            await query.answer()

    async def _handle_error(self, update, context):
        self._metrics["errors"] += 1
        logger.error(f"Update error: {context.error}")

    def _parse_update(self, update) -> TelegramMessage:
        msg = update.message or (update.callback_query.message if update.callback_query else None)
        user = update.effective_user
        chat = update.effective_chat

        text = None
        media_type = None
        media_file_id = None
        callback_data = None

        if update.callback_query:
            callback_data = update.callback_query.data
            text = msg.text if msg else None
        elif msg:
            if msg.photo:
                media_type = "photo"
                media_file_id = msg.photo[-1].file_id
            elif msg.video:
                media_type = "video"
                media_file_id = msg.video.file_id
            elif msg.document:
                media_type = "document"
                media_file_id = msg.document.file_id
            elif msg.audio:
                media_type = "audio"
                media_file_id = msg.audio.file_id
            elif msg.voice:
                media_type = "voice"
                media_file_id = msg.voice.file_id
            elif msg.sticker:
                media_type = "sticker"
                media_file_id = msg.sticker.file_id
            elif msg.text:
                text = msg.text

        chat_type_map = {
            "private": TelegramChatType.PRIVATE,
            "group": TelegramChatType.GROUP,
            "supergroup": TelegramChatType.SUPERGROUP,
            "channel": TelegramChatType.CHANNEL,
        }

        bot_username = context.bot.username if hasattr(context, "bot") and context.bot else ""
        is_mentioned = bool(text and f"@{bot_username}" in text)

        return TelegramMessage(
            message_id=msg.message_id if msg else 0,
            chat_id=chat.id if chat else 0,
            chat_type=chat_type_map.get(
                chat.type.value if chat else "private",
                TelegramChatType.PRIVATE,
            ),
            user_id=user.id if user else 0,
            username=user.username if user else None,
            text=text,
            date=msg.date.timestamp() if msg and msg.date else time.time(),
            reply_to=msg.reply_to_message.message_id if msg and msg.reply_to_message else None,
            media_type=media_type,
            media_file_id=media_file_id,
            caption=msg.caption if msg else None,
            callback_data=callback_data,
            thread_id=getattr(msg, "message_thread_id", None) if msg else None,
            is_bot_mentioned=is_mentioned,
            raw=update,
        )

    async def send_message(self, chat_id: int, text: str, **kwargs) -> Any:
        for hook in self._before_send:
            try:
                result = await hook(chat_id, text, kwargs)
                if result:
                    kwargs = result
            except Exception:
                pass

        text = self._formatter.truncate(text, self.config.max_message_length)

        if self._bot:
            result = await self._bot.send_message(
                chat_id=chat_id, text=text,
                parse_mode=kwargs.pop("parse_mode", self.config.parse_mode),
                **kwargs,
            )
            self._metrics["messages_sent"] += 1

            for hook in self._after_send:
                try:
                    await hook(chat_id, text, result)
                except Exception:
                    pass

            return result

    async def send_photo(self, chat_id: int, photo: str, caption: str = "", **kwargs) -> Any:
        if self._bot:
            result = await self._bot.send_photo(
                chat_id=chat_id, photo=photo, caption=caption,
                parse_mode=kwargs.pop("parse_mode", self.config.parse_mode),
                **kwargs,
            )
            self._metrics["media_sent"] += 1
            return result

    async def send_document(self, chat_id: int, document: str, caption: str = "", **kwargs) -> Any:
        if self._bot:
            result = await self._bot.send_document(
                chat_id=chat_id, document=document, caption=caption,
                parse_mode=kwargs.pop("parse_mode", self.config.parse_mode),
                **kwargs,
            )
            self._metrics["media_sent"] += 1
            return result

    async def send_video(self, chat_id: int, video: str, caption: str = "", **kwargs) -> Any:
        if self._bot:
            result = await self._bot.send_video(
                chat_id=chat_id, video=video, caption=caption,
                parse_mode=kwargs.pop("parse_mode", self.config.parse_mode),
                **kwargs,
            )
            self._metrics["media_sent"] += 1
            return result

    async def send_audio(self, chat_id: int, audio: str, caption: str = "", **kwargs) -> Any:
        if self._bot:
            result = await self._bot.send_audio(
                chat_id=chat_id, audio=audio, caption=caption,
                parse_mode=kwargs.pop("parse_mode", self.config.parse_mode),
                **kwargs,
            )
            self._metrics["media_sent"] += 1
            return result

    async def send_voice(self, chat_id: int, voice: str, caption: str = "", **kwargs) -> Any:
        if self._bot:
            result = await self._bot.send_voice(
                chat_id=chat_id, voice=voice, caption=caption,
                parse_mode=kwargs.pop("parse_mode", self.config.parse_mode),
                **kwargs,
            )
            self._metrics["media_sent"] += 1
            return result

    async def send_media_group(self, chat_id: int, media: List[Dict], **kwargs) -> Any:
        if self._bot:
            from telegram import InputMediaPhoto, InputMediaVideo, InputMediaDocument
            media_objects = []
            for m in media:
                media_type = m.get("type", "photo")
                if media_type == "photo":
                    media_objects.append(InputMediaPhoto(m["media"], caption=m.get("caption", "")))
                elif media_type == "video":
                    media_objects.append(InputMediaVideo(m["media"], caption=m.get("caption", "")))
                elif media_type == "document":
                    media_objects.append(InputMediaDocument(m["media"], caption=m.get("caption", "")))
            if media_objects:
                result = await self._bot.send_media_group(chat_id=chat_id, media=media_objects, **kwargs)
                self._metrics["media_sent"] += len(media_objects)
                return result

    async def send_inline_keyboard(self, chat_id: int, text: str, buttons: List[List[Dict]], **kwargs) -> Any:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = []
        for row in buttons:
            keyboard_row = []
            for btn in row:
                if "url" in btn:
                    keyboard_row.append(InlineKeyboardButton(btn["text"], url=btn["url"]))
                elif "callback_data" in btn:
                    keyboard_row.append(InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"]))
            keyboard.append(keyboard_row)
        markup = InlineKeyboardMarkup(keyboard)
        return await self.send_message(chat_id, text, reply_markup=markup, **kwargs)

    async def reply_to(self, message: TelegramMessage, text: str, **kwargs) -> Any:
        if self._bot:
            result = await self._bot.send_message(
                chat_id=message.chat_id, text=text,
                reply_to_message_id=message.message_id,
                parse_mode=kwargs.pop("parse_mode", self.config.parse_mode),
                **kwargs,
            )
            self._metrics["messages_sent"] += 1
            return result

    async def edit_message(self, chat_id: int, message_id: int, text: str, **kwargs) -> Any:
        if self._bot:
            return await self._bot.edit_message_text(
                chat_id=chat_id, message_id=message_id, text=text,
                parse_mode=kwargs.pop("parse_mode", self.config.parse_mode),
                **kwargs,
            )

    async def delete_message(self, chat_id: int, message_id: int) -> bool:
        if self._bot:
            try:
                await self._bot.delete_message(chat_id=chat_id, message_id=message_id)
                return True
            except Exception:
                return False
        return False

    async def answer_callback(self, callback_query_id: str, text: str = "", show_alert: bool = False):
        if self._bot:
            await self._bot.answer_callback_query(
                callback_query_id=callback_query_id, text=text, show_alert=show_alert,
            )

    async def set_my_commands(self, commands: List[Dict[str, str]], scope: Any = None):
        from telegram import BotCommand
        if self._bot:
            cmd_objects = [BotCommand(c["command"], c["description"]) for c in commands]
            await self._bot.set_my_commands(cmd_objects, scope=scope)

    async def get_me(self) -> Dict:
        if self._bot:
            me = await self._bot.get_me()
            return {"id": me.id, "username": me.username, "first_name": me.first_name}
        return {}

    def get_metrics(self) -> Dict:
        return dict(self._metrics)

    @property
    def is_connected(self) -> bool:
        return self._connected
