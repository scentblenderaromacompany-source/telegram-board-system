"""
Comprehensive isolated tests for src/telegram/message_formatter.py.
"""
import pytest

from src.telegram.message_formatter import TelegramMessageFormatter


class TestFormatterInit:
    def test_max_length_constant(self):
        assert TelegramMessageFormatter.MAX_LENGTH == 4096

    def test_instance_creation(self):
        f = TelegramMessageFormatter()
        assert f is not None


class TestFormatHTML:
    def test_format_html_passthrough(self):
        f = TelegramMessageFormatter()
        assert f.format("<b>test</b>", "HTML") == "<b>test</b>"

    def test_format_plain_text(self):
        f = TelegramMessageFormatter()
        assert f.format("hello world", "HTML") == "hello world"


class TestFormatMarkdown:
    def test_format_markdown_v2_escapes(self):
        f = TelegramMessageFormatter()
        result = f.format("hello_world", "MarkdownV2")
        assert "\\_" in result
        assert "hello" in result

    def test_format_markdown_v2_special_chars(self):
        f = TelegramMessageFormatter()
        result = f.format("test(value)", "MarkdownV2")
        assert "\\(" in result
        assert "\\)" in result

    def test_format_unknown_mode_passthrough(self):
        f = TelegramMessageFormatter()
        text = "plain text"
        assert f.format(text, "UNKNOWN") == text


class TestTruncate:
    def test_short_text_not_truncated(self):
        f = TelegramMessageFormatter()
        assert f.truncate("hello", 100) == "hello"

    def test_exact_length_not_truncated(self):
        f = TelegramMessageFormatter()
        text = "x" * 100
        assert f.truncate(text, 100) == text

    def test_long_text_truncated(self):
        f = TelegramMessageFormatter()
        text = "x" * 5000
        result = f.truncate(text, 4096)
        assert len(result) == 4096
        assert result.endswith("...")

    def test_truncate_default_length(self):
        f = TelegramMessageFormatter()
        text = "y" * 5000
        result = f.truncate(text)
        assert len(result) == 4096

    def test_truncate_preserves_content(self):
        f = TelegramMessageFormatter()
        text = "hello world"
        assert f.truncate(text, 100) == "hello world"


class TestSplit:
    def test_short_text_single_chunk(self):
        f = TelegramMessageFormatter()
        chunks = f.split("hello", 100)
        assert chunks == ["hello"]

    def test_exact_length_single_chunk(self):
        f = TelegramMessageFormatter()
        text = "x" * 100
        chunks = f.split(text, 100)
        assert len(chunks) == 1

    def test_long_text_multiple_chunks(self):
        f = TelegramMessageFormatter()
        text = "\n".join([f"Line {i}" for i in range(100)])
        chunks = f.split(text, 500)
        assert len(chunks) > 1

    def test_split_prefers_newline(self):
        f = TelegramMessageFormatter()
        text = "aaaa\nbbbb\ncccc\ndddd\neeee\nffff"
        chunks = f.split(text, 20)
        assert len(chunks) > 1
        assert "\n" in chunks[0]

    def test_split_no_newline(self):
        f = TelegramMessageFormatter()
        text = "a" * 200
        chunks = f.split(text, 100)
        assert len(chunks) == 2
        assert chunks[0] == "a" * 100

    def test_split_default_length(self):
        f = TelegramMessageFormatter()
        text = "x" * 5000
        chunks = f.split(text)
        assert len(chunks) > 1

    def test_split_empty_text(self):
        f = TelegramMessageFormatter()
        chunks = f.split("", 100)
        assert chunks == [""]

    def test_split_reassembles(self):
        f = TelegramMessageFormatter()
        original = "\n".join([f"Line {i}" for i in range(200)])
        chunks = f.split(original, 1000)
        reassembled = "\n".join(chunks)
        assert reassembled == original


class TestEscapeHTML:
    def test_escape_quotes(self):
        f = TelegramMessageFormatter()
        assert f.escape_html('"hello"') == "&quot;hello&quot;"

    def test_escape_ampersand(self):
        f = TelegramMessageFormatter()
        assert f.escape_html("a&b") == "a&amp;b"

    def test_escape_tags(self):
        f = TelegramMessageFormatter()
        assert f.escape_html("<script>") == "&lt;script&gt;"

    def test_escape_no_special(self):
        f = TelegramMessageFormatter()
        assert f.escape_html("hello world") == "hello world"


class TestFormattingTags:
    def test_bold(self):
        f = TelegramMessageFormatter()
        assert f.bold("text") == "<b>text</b>"

    def test_italic(self):
        f = TelegramMessageFormatter()
        assert f.italic("text") == "<i>text</i>"

    def test_code(self):
        f = TelegramMessageFormatter()
        assert f.code("text") == "<code>text</code>"

    def test_pre_without_language(self):
        f = TelegramMessageFormatter()
        assert f.pre("code") == "<pre>code</pre>"

    def test_pre_with_language(self):
        f = TelegramMessageFormatter()
        assert f.pre("code", "python") == '<pre><code class="language-python">code</code></pre>'

    def test_link(self):
        f = TelegramMessageFormatter()
        result = f.link("click", "https://example.com")
        assert result == '<a href="https://example.com">click</a>'

    def test_mention(self):
        f = TelegramMessageFormatter()
        result = f.mention("user", 12345)
        assert result == '<a href="tg://user?id=12345">user</a>'


class TestProgressBar:
    def test_zero_progress(self):
        f = TelegramMessageFormatter()
        bar = f.progress_bar(0, 100)
        assert "0%" in bar
        assert "░" in bar

    def test_full_progress(self):
        f = TelegramMessageFormatter()
        bar = f.progress_bar(100, 100)
        assert "100%" in bar
        assert "█" in bar

    def test_half_progress(self):
        f = TelegramMessageFormatter()
        bar = f.progress_bar(50, 100)
        assert "50%" in bar

    def test_zero_total(self):
        f = TelegramMessageFormatter()
        bar = f.progress_bar(0, 0)
        assert "0%" in bar

    def test_custom_width(self):
        f = TelegramMessageFormatter()
        bar = f.progress_bar(50, 100, width=40)
        assert "█" in bar
        assert "░" in bar


class TestStatusMessage:
    def test_success(self):
        f = TelegramMessageFormatter()
        result = f.status_message("success", "Done")
        assert "✅" in result
        assert "Done" in result

    def test_error(self):
        f = TelegramMessageFormatter()
        result = f.status_message("error", "Failed")
        assert "❌" in result

    def test_warning(self):
        f = TelegramMessageFormatter()
        result = f.status_message("warning")
        assert "⚠️" in result

    def test_unknown_status(self):
        f = TelegramMessageFormatter()
        result = f.status_message("unknown")
        assert result == ""


class TestNotification:
    def test_notification_basic(self):
        f = TelegramMessageFormatter()
        result = f.notification("Title", "Body")
        assert "<b>Title</b>" in result
        assert "Body" in result

    def test_notification_with_url(self):
        f = TelegramMessageFormatter()
        result = f.notification("Title", "Body", "https://example.com")
        assert "View →" in result
        assert "https://example.com" in result


class TestTable:
    def test_table_basic(self):
        f = TelegramMessageFormatter()
        result = f.table(["Name", "Value"], [["a", "1"], ["b", "2"]])
        assert "Name" in result
        assert "Value" in result
        assert "a" in result
        assert "b" in result

    def test_table_empty_rows(self):
        f = TelegramMessageFormatter()
        result = f.table(["Col1", "Col2"], [])
        assert "Col1" in result

    def test_table_single_row(self):
        f = TelegramMessageFormatter()
        result = f.table(["H"], [["v"]])
        assert "H" in result
        assert "v" in result
