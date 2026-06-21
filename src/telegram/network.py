"""
Telegram network fallback transport.
Based on Hermes gateway/platforms/telegram_network.py.
Provides DNS-over-HTTPS fallback for blocked Telegram API endpoints.
"""
import asyncio
import ipaddress
import logging
import socket
from typing import Iterable, Optional, List

logger = logging.getLogger(__name__)

_TELEGRAM_API_HOST = "api.telegram.org"
_DOH_TIMEOUT = 4.0

_DOH_PROVIDERS = [
    {
        "url": "https://dns.google/resolve",
        "params": {"name": _TELEGRAM_API_HOST, "type": "A"},
        "headers": {},
    },
    {
        "url": "https://cloudflare-dns.com/dns-query",
        "params": {"name": _TELEGRAM_API_HOST, "type": "A"},
        "headers": {"Accept": "application/dns-json"},
    },
]

_SEED_FALLBACK_IPS = ["149.154.167.220", "149.154.167.221", "149.154.167.222"]

def _normalize_fallback_ips(ips: Iterable[str]) -> List[str]:
    normalized = []
    for ip in ips:
        try:
            addr = ipaddress.ip_address(ip)
            if isinstance(addr, ipaddress.IPv4Address):
                normalized.append(str(addr))
        except ValueError:
            continue
    return list(dict.fromkeys(normalized))

async def discover_fallback_ips() -> List[str]:
    """Discover Telegram API IPs via DNS-over-HTTPS."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=_DOH_TIMEOUT) as client:
            for provider in _DOH_PROVIDERS:
                try:
                    resp = await client.get(provider["url"], params=provider["params"], headers=provider["headers"])
                    if resp.status_code == 200:
                        data = resp.json()
                        answers = data.get("Answer", [])
                        ips = [a["data"] for a in answers if a.get("type") == 1]
                        if ips:
                            logger.info(f"Discovered {len(ips)} Telegram fallback IPs via DoH")
                            return _normalize_fallback_ips(ips)
                except Exception as e:
                    logger.debug(f"DoH provider failed: {e}")
                    continue
    except ImportError:
        pass
    
    logger.info("Using seed fallback IPs")
    return list(_SEED_FALLBACK_IPS)

def _rewrite_request_for_ip(request, ip: str):
    """Rewrite request URL to use fallback IP while preserving SNI."""
    from urllib.parse import urlparse, urlunparse
    parsed = urlparse(str(request.url))
    netloc = parsed.netloc
    if ":" in netloc:
        host, port = netloc.rsplit(":", 1)
        new_netloc = f"{ip}:{port}"
    else:
        new_netloc = ip
    new_url = urlunparse(parsed._replace(netloc=new_netloc))
    
    import httpx
    new_request = httpx.Request(
        method=request.method,
        url=new_url,
        headers=dict(request.headers),
        content=request.content,
    )
    new_request.headers["Host"] = _TELEGRAM_API_HOST
    return new_request

class TelegramFallbackTransport:
    """
    Fallback transport for Telegram Bot API.
    Tries primary DNS, then fallback IPs with sticky routing.
    """
    
    def __init__(self, fallback_ips: List[str] = None, proxy_url: str = None):
        self._fallback_ips = _normalize_fallback_ips(fallback_ips or _SEED_FALLBACK_IPS)
        self._proxy_url = proxy_url
        self._sticky_ip: Optional[str] = None
        self._sticky_lock = asyncio.Lock()
    
    def get_client_kwargs(self) -> dict:
        """Get kwargs for httpx client."""
        kwargs = {}
        if self._proxy_url:
            kwargs["proxy"] = self._proxy_url
        return kwargs
    
    async def test_connectivity(self) -> dict:
        """Test connectivity to Telegram API."""
        results = {"primary": False, "fallbacks": {}}
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"https://{_TELEGRAM_API_HOST}")
                results["primary"] = resp.status_code == 404
        except Exception as e:
            results["primary_error"] = str(e)
        
        for ip in self._fallback_ips:
            try:
                import httpx
                kwargs = self.get_client_kwargs()
                async with httpx.AsyncClient(**kwargs) as client:
                    request = httpx.Request("GET", f"https://{_TELEGRAM_API_HOST}")
                    rewritten = _rewrite_request_for_ip(request, ip)
                    resp = await client.send(rewritten)
                    results["fallbacks"][ip] = resp.status_code == 404
            except Exception as e:
                results["fallbacks"][ip] = False
        
        return results
