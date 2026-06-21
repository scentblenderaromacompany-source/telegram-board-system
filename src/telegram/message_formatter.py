"""
Telegram message formatter with HTML/Markdown support and rich messages.
"""
import re
import html
from typing import List, Optional


class TelegramMessageFormatter:
    """
    Formats messages for Telegram with:
    - HTML/Markdown escaping
    - Message splitting for length limits
    - Rich message templates
    - Progress indicators
    """

    MAX_LENGTH = 4096

    def format(self, text: str, parse_mode: str = "HTML") -> str:
        if parse_mode == "HTML":
            return self._format_html(text)
        elif parse_mode == "MarkdownV2":
            return self._format_markdown_v2(text)
        return text

    def _format_html(self, text: str) -> str:
        return text

    def _format_markdown_v2(self, text: str) -> str:
        special_chars = r"_*[]()~`>#+-=|{}.!"
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
        return text

    def truncate(self, text: str, max_length: int = None) -> str:
        max_len = max_length or self.MAX_LENGTH
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."

    def split(self, text: str, max_length: int = None) -> List[str]:
        max_len = max_length or self.MAX_LENGTH
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

    def escape_html(self, text: str) -> str:
        return html.escape(text)

    def bold(self, text: str) -> str:
        return f"<b>{text}</b>"

    def italic(self, text: str) -> str:
        return f"<i>{text}</i>"

    def code(self, text: str) -> str:
        return f"<code>{text}</code>"

    def pre(self, text: str, language: str = "") -> str:
        if language:
            return f'<pre><code class="language-{language}">{text}</code></pre>'
        return f"<pre>{text}</pre>"

    def link(self, text: str, url: str) -> str:
        return f'<a href="{url}">{text}</a>'

    def mention(self, text: str, user_id: int) -> str:
        return f'<a href="tg://user?id={user_id}">{text}</a>'

    def progress_bar(self, current: int, total: int, width: int = 20) -> str:
        filled = int(width * current / total) if total > 0 else 0
        bar = "█" * filled + "░" * (width - filled)
        pct = int(100 * current / total) if total > 0 else 0
        return f"[{bar}] {pct}%"

    def status_message(self, status: str, details: str = "") -> str:
        icons = {
            "success": "✅", "error": "❌", "warning": "⚠️",
            "info": "ℹ️", "loading": "⏳", "processing": "⚙️",
        }
        icon = icons.get(status, "")
        return f"{icon} {details}" if details else icon

    def notification(self, title: str, body: str, url: str = None) -> str:
        parts = [self.bold(title), "", body]
        if url:
            parts.extend(["", self.link("View →", url)])
        return "\n".join(parts)

    def table(self, headers: List[str], rows: List[List[str]]) -> str:
        lines = [self.bold(" | ".join(headers)), "─" * 40]
        for row in rows:
            lines.append(" | ".join(str(c) for c in row))
        return "\n".join(lines)
