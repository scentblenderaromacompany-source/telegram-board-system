"""
Telegram Managed Bot onboarding.
Based on Hermes hermes_cli/telegram_managed_bot.py.
Creates user-owned child bots without manual BotFather token copy-paste.
"""
import asyncio
import logging
import re
import secrets
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_API_URL = "https://setup.hermes-agent.nousresearch.com"
DEFAULT_MANAGER_BOT = "HermesSetupBot"
DEFAULT_BOT_NAME = "Hermes Agent"
DEFAULT_POLL_TIMEOUT = 180
POLL_INTERVAL = 2

_TELEGRAM_BOT_TOKEN_RE = re.compile(r"^\d+:[A-Za-z0-9_-]{30,}$")

@dataclass(frozen=True)
class TelegramPairing:
    pairing_id: str
    poll_token: str
    suggested_username: str
    deep_link: str
    qr_payload: str
    expires_at: Optional[str] = None

@dataclass(frozen=True)
class TelegramBotSetupResult:
    token: str
    bot_username: Optional[str] = None
    owner_user_id: Optional[int] = None

def is_valid_telegram_bot_token(token: object) -> bool:
    return isinstance(token, str) and bool(_TELEGRAM_BOT_TOKEN_RE.match(token))

class TelegramManagedBot:
    """
    Manages Telegram bot onboarding via managed bot pairing.
    """
    
    def __init__(self, api_url: str = None):
        self._api_url = (api_url or DEFAULT_API_URL).rstrip("/")
    
    async def create_pairing(self, manager_bot: str = None) -> TelegramPairing:
        """Create a new pairing request."""
        manager = manager_bot or DEFAULT_MANAGER_BOT
        pairing_id = secrets.token_urlsafe(16)
        poll_token = secrets.token_urlsafe(32)
        username_slug = f"hermes_{pairing_id[:8]}"
        
        deep_link = f"https://t.me/{manager}?start={pairing_id}"
        qr_payload = deep_link
        
        return TelegramPairing(
            pairing_id=pairing_id,
            poll_token=poll_token,
            suggested_username=username_slug,
            deep_link=deep_link,
            qr_payload=qr_payload,
        )
    
    async def poll_for_completion(self, pairing: TelegramPairing, timeout: int = None) -> Optional[TelegramBotSetupResult]:
        """Poll for bot creation completion."""
        timeout = timeout or DEFAULT_POLL_TIMEOUT
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(
                        f"{self._api_url}/pair/{pairing.pairing_id}/status",
                        headers={"Authorization": f"Bearer {pairing.poll_token}"},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get("status") == "completed":
                            return TelegramBotSetupResult(
                                token=data["token"],
                                bot_username=data.get("bot_username"),
                                owner_user_id=data.get("owner_user_id"),
                            )
            except Exception as e:
                logger.debug(f"Poll error: {e}")
            
            await asyncio.sleep(POLL_INTERVAL)
        
        logger.warning(f"Pairing {pairing.pairing_id} timed out after {timeout}s")
        return None
    
    def render_qr_terminal(self, url: str) -> str:
        """Render URL as QR code for terminal."""
        try:
            import io
            import qrcode
            qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=1, border=1)
            qr.add_data(url)
            qr.make(fit=True)
            buf = io.StringIO()
            qr.print_ascii(out=buf, invert=True)
            return buf.getvalue()
        except ImportError:
            return f"[QR: {url}]"
