"""
Core Telegram bot framework with mask support, middleware, and advanced features.
"""
import asyncio
import logging
import time
import traceback
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Awaitable
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)

class BotState(Enum):
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    PROCESSING = "processing"
    WAITING = "waiting"
    STOPPING = "stopping"
    ERROR = "error"

class MessageType(Enum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    VOICE = "voice"
    STICKER = "sticker"
    CALLBACK = "callback"
    INLINE = "inline"
    UNKNOWN = "unknown"

@dataclass
class MessageContext:
    """Parsed message context for handlers."""
    update: Any
    chat_id: str
    user_id: int
    username: Optional[str]
    text: Optional[str]
    message_type: MessageType
    is_group: bool
    is_bot_mentioned: bool
    reply_to_message: Optional[Any] = None
    media: Optional[Dict] = None
    callback_data: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BotConfig:
    token: str
    bot_id: str
    name: str
    business_id: str
    mask_id: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    allowed_chat_ids: List[str] = field(default_factory=list)
    allowed_user_ids: List[int] = field(default_factory=list)
    rate_limit: int = 30
    max_message_length: int = 4096
    parse_mode: Optional[str] = "HTML"
    disable_web_page_preview: bool = False
    disable_notification: bool = False
    settings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BotMetrics:
    """Bot performance metrics."""
    messages_received: int = 0
    messages_sent: int = 0
    errors: int = 0
    uptime_start: float = field(default_factory=time.time)
    last_activity: float = 0
    avg_response_time: float = 0
    _response_times: List[float] = field(default_factory=list)

    def record_response(self, duration: float):
        self._response_times.append(duration)
        if len(self._response_times) > 1000:
            self._response_times = self._response_times[-500:]
        self.avg_response_time = sum(self._response_times) / len(self._response_times)

    @property
    def uptime(self) -> float:
        return time.time() - self.uptime_start

    def to_dict(self) -> Dict:
        return {
            "messages_received": self.messages_received,
            "messages_sent": self.messages_sent,
            "errors": self.errors,
            "uptime_seconds": self.uptime,
            "avg_response_time_ms": round(self.avg_response_time * 1000, 2),
            "last_activity": self.last_activity,
        }

MiddlewareFunc = Callable[[MessageContext, Callable], Awaitable[Any]]
HandlerFunc = Callable[[MessageContext], Awaitable[Any]]

class TelegramBot:
    """Production-grade Telegram bot with middleware, webhooks, and mask support."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.state = BotState.IDLE
        self.metrics = BotMetrics()
        self._app = None
        self._handlers: Dict[str, HandlerFunc] = {}
        self._middleware: List[MiddlewareFunc] = []
        self._error_handlers: List[Callable] = []
        self._before_send_hooks: List[Callable] = []
        self._after_send_hooks: List[Callable] = []
        self._custom_commands: Dict[str, str] = {}

    def use(self, middleware: MiddlewareFunc):
        """Add middleware to the bot pipeline."""
        self._middleware.append(middleware)
        return self

    def on_error(self, handler: Callable):
        """Register error handler."""
        self._error_handlers.append(handler)
        return self

    def before_send(self, hook: Callable):
        """Register before-send hook."""
        self._before_send_hooks.append(hook)
        return self

    def after_send(self, hook: Callable):
        """Register after-send hook."""
        self._after_send_hooks.append(hook)
        return self

    def command(self, name: str, description: str = ""):
        """Decorator to register command handler."""
        def decorator(func: HandlerFunc):
            self._handlers[name] = func
            if description:
                self._custom_commands[name] = description
            return func
        return decorator

    def on_message(self, func: HandlerFunc):
        """Decorator to register message handler."""
        self._handlers["__message__"] = func
        return func

    def on_callback(self, func: HandlerFunc):
        """Decorator to register callback query handler."""
        self._handlers["__callback__"] = func
        return func

    async def start(self):
        """Initialize and start the bot."""
        self.state = BotState.STARTING
        try:
            from telegram.ext import Application
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

            self.state = BotState.RUNNING
            self.metrics.uptime_start = time.time()
            logger.info(f"Bot {self.config.bot_id} started successfully")
        except Exception as e:
            self.state = BotState.ERROR
            self.metrics.errors += 1
            logger.error(f"Failed to start bot {self.config.bot_id}: {e}")
            raise

    async def stop(self):
        """Gracefully stop the bot."""
        self.state = BotState.STOPPING
        try:
            if self._app:
                if not self.config.webhook_url:
                    await self._app.updater.stop()
                await self._app.stop()
                await self._app.shutdown()
            self.state = BotState.IDLE
            logger.info(f"Bot {self.config.bot_id} stopped")
        except Exception as e:
            logger.error(f"Error stopping bot {self.config.bot_id}: {e}")

    def _register_handlers(self):
        """Register all handlers with the application."""
        from telegram.ext import (
            CommandHandler, MessageHandler, CallbackQueryHandler,
            InlineQueryHandler, ChosenResultHandler,
            filters,
        )

        for cmd_name, handler in self._handlers.items():
            if cmd_name.startswith("__"):
                continue
            self._app.add_handler(CommandHandler(cmd_name, self._wrap_handler(handler)))

        if "__message__" in self._handlers:
            self._app.add_handler(
                MessageHandler(
                    filters.ALL & ~filters.COMMAND,
                    self._wrap_handler(self._handlers["__message__"]),
                )
            )

        if "__callback__" in self._handlers:
            self._app.add_handler(
                CallbackQueryHandler(self._wrap_handler(self._handlers["__callback__"]))
            )

        default_message = MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self._handle_default_message,
        )
        self._app.add_handler(default_message)

        self._app.add_error_handler(self._handle_error)

    def _wrap_handler(self, handler: HandlerFunc):
        """Wrap handler with middleware pipeline."""
        async def wrapped(update, context):
            msg_ctx = self._parse_update(update)
            self.metrics.messages_received += 1
            self.metrics.last_activity = time.time()

            pipeline = handler
            for mw in reversed(self._middleware):
                next_handler = pipeline
                async def mw_chain(ctx, next_h=next_handler, m=mw):
                    return await m(ctx, next_h)
                pipeline = mw_chain

            start = time.time()
            try:
                result = await pipeline(msg_ctx)
                duration = time.time() - start
                self.metrics.record_response(duration)
                return result
            except Exception as e:
                self.metrics.errors += 1
                raise
        return wrapped

    def _parse_update(self, update) -> MessageContext:
        """Parse a Telegram update into MessageContext."""
        msg = update.message or update.callback_query and update.callback_query.message
        user = update.effective_user
        chat = update.effective_chat

        msg_type = MessageType.TEXT
        media = None
        text = None
        callback_data = None

        if update.callback_query:
            msg_type = MessageType.CALLBACK
            callback_data = update.callback_query.data
            text = update.callback_query.message.text if update.callback_query.message else None
        elif msg:
            if msg.photo:
                msg_type = MessageType.PHOTO
                media = {"photo": msg.photo[-1].file_id}
            elif msg.video:
                msg_type = MessageType.VIDEO
                media = {"video": msg.video.file_id}
            elif msg.document:
                msg_type = MessageType.DOCUMENT
                media = {"document": msg.document.file_id}
            elif msg.audio:
                msg_type = MessageType.AUDIO
                media = {"audio": msg.audio.file_id}
            elif msg.voice:
                msg_type = MessageType.VOICE
                media = {"voice": msg.voice.file_id}
            elif msg.sticker:
                msg_type = MessageType.STICKER
                media = {"sticker": msg.sticker.file_id}
            elif msg.text:
                msg_type = MessageType.TEXT
                text = msg.text

        bot_username = context.bot.username if hasattr(context, "bot") else ""
        is_mentioned = False
        if text and bot_username:
            is_mentioned = f"@{bot_username}" in text

        return MessageContext(
            update=update,
            chat_id=str(chat.id) if chat else "",
            user_id=user.id if user else 0,
            username=user.username if user else None,
            text=text,
            message_type=msg_type,
            is_group=chat.type in ("group", "supergroup") if chat else False,
            is_bot_mentioned=is_mentioned,
            reply_to_message=msg.reply_to_message if msg else None,
            media=media,
            callback_data=callback_data,
            metadata={
                "bot_id": self.config.bot_id,
                "business_id": self.config.business_id,
            },
        )

    async def _handle_default_message(self, update, context):
        """Default message handler with auto-response."""
        msg_ctx = self._parse_update(update)
        self.metrics.messages_received += 1

        if msg_ctx.is_group and not msg_ctx.is_bot_mentioned:
            return

        text = msg_ctx.text or ""
        responses = {
            "hello": f"Hello {msg_ctx.username or 'there'}! I'm {self.config.name}.",
            "hi": f"Hey {msg_ctx.username or 'there'}! How can I help?",
            "help": self._get_help_text(),
            "status": self._get_status_text(),
            "ping": "pong",
        }

        for keyword, response in responses.items():
            if keyword in text.lower():
                await self.send_message(msg_ctx.chat_id, response)
                return

    async def _handle_error(self, update, context):
        """Handle errors from handlers."""
        logger.error(f"Handler error: {context.error}")
        self.metrics.errors += 1
        for handler in self._error_handlers:
            try:
                await handler(update, context)
            except Exception as e:
                logger.error(f"Error handler failed: {e}")

    def _get_help_text(self) -> str:
        """Generate help text from registered commands."""
        lines = [f"<b>{self.config.name} Commands:</b>", ""]
        for cmd, desc in self._custom_commands.items():
            lines.append(f"/{cmd} - {desc}")
        if not self._custom_commands:
            lines.extend([
                "/start - Start the bot",
                "/help - Show this help",
                "/status - Show bot status",
                "/ping - Check connectivity",
            ])
        return "\n".join(lines)

    def _get_status_text(self) -> str:
        """Get bot status text."""
        m = self.metrics
        return (
            f"<b>Status:</b> {self.state.value}\n"
            f"<b>Uptime:</b> {m.uptime:.0f}s\n"
            f"<b>Messages:</b> {m.messages_received} recv / {m.messages_sent} sent\n"
            f"<b>Avg Response:</b> {m.avg_response_time*1000:.1f}ms\n"
            f"<b>Errors:</b> {m.errors}"
        )

    async def send_message(self, chat_id: str, text: str, **kwargs) -> Any:
        """Send a message with hooks and rate limiting."""
        for hook in self._before_send_hooks:
            try:
                kwargs = await hook(chat_id, text, kwargs) or kwargs
            except Exception as e:
                logger.error(f"Before-send hook error: {e}")

        if len(text) > self.config.max_message_length:
            chunks = self._split_message(text)
            results = []
            for chunk in chunks:
                result = await self._do_send(chat_id, chunk, **kwargs)
                results.append(result)
            return results

        result = await self._do_send(chat_id, text, **kwargs)

        for hook in self._after_send_hooks:
            try:
                await hook(chat_id, text, result)
            except Exception as e:
                logger.error(f"After-send hook error: {e}")

        return result

    async def _do_send(self, chat_id: str, text: str, **kwargs) -> Any:
        """Actually send a message."""
        if self._app:
            kwargs.setdefault("parse_mode", self.config.parse_mode)
            kwargs.setdefault("disable_web_page_preview", self.config.disable_web_page_preview)
            result = await self._app.bot.send_message(chat_id=chat_id, text=text, **kwargs)
            self.metrics.messages_sent += 1
            return result

    async def send_photo(self, chat_id: str, photo: str, caption: str = "", **kwargs) -> Any:
        """Send a photo with optional caption."""
        if self._app:
            result = await self._app.bot.send_photo(
                chat_id=chat_id, photo=photo, caption=caption,
                parse_mode=self.config.parse_mode, **kwargs
            )
            self.metrics.messages_sent += 1
            return result

    async def send_document(self, chat_id: str, document: str, caption: str = "", **kwargs) -> Any:
        """Send a document."""
        if self._app:
            result = await self._app.bot.send_document(
                chat_id=chat_id, document=document, caption=caption,
                parse_mode=self.config.parse_mode, **kwargs
            )
            self.metrics.messages_sent += 1
            return result

    async def send_inline_keyboard(self, chat_id: str, text: str, buttons: List[List[Dict]], **kwargs) -> Any:
        """Send message with inline keyboard."""
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

    async def reply_to(self, message, text: str, **kwargs) -> Any:
        """Reply to a specific message."""
        if self._app:
            result = await message.reply_text(text, parse_mode=self.config.parse_mode, **kwargs)
            self.metrics.messages_sent += 1
            return result

    async def edit_message(self, chat_id: str, message_id: int, text: str, **kwargs) -> Any:
        """Edit an existing message."""
        if self._app:
            return await self._app.bot.edit_message_text(
                chat_id=chat_id, message_id=message_id, text=text,
                parse_mode=self.config.parse_mode, **kwargs
            )

    async def delete_message(self, chat_id: str, message_id: int) -> bool:
        """Delete a message."""
        if self._app:
            try:
                await self._app.bot.delete_message(chat_id=chat_id, message_id=message_id)
                return True
            except Exception:
                return False
        return False

    def _split_message(self, text: str) -> List[str]:
        """Split long message into chunks."""
        max_len = self.config.max_message_length
        if len(text) <= max_len:
            return [text]
        chunks = []
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break
            split_at = text.rfind("\n", 0, max_len)
            if split_at == -1:
                split_at = max_len
            chunks.append(text[:split_at])
            text = text[split_at:].lstrip("\n")
        return chunks

    def get_metrics(self) -> Dict:
        """Get bot metrics."""
        return self.metrics.to_dict()
