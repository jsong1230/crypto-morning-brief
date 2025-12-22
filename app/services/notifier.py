"""Notification service for sending reports via Telegram."""

import html
import re

import requests

from app.config import settings
from app.utils.logger import logger

# Telegram API constants
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MESSAGE_LENGTH = 4096  # Telegram message length limit


class TelegramNotifier:
    """Service for sending messages via Telegram."""

    def __init__(self):
        """Initialize Telegram notifier."""
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.enabled = settings.send_telegram
        self.parse_mode = settings.telegram_parse_mode.upper()
        self.wrap_pre = settings.telegram_wrap_pre

    def is_configured(self) -> bool:
        """
        Check if Telegram is properly configured.

        Returns:
            True if bot token and chat ID are set, False otherwise.
        """
        return bool(self.bot_token and self.chat_id and self.enabled)

    def send(self, text: str) -> None:
        """
        Send a message to Telegram.

        Args:
            text: Message text to send.

        Note:
            Errors are logged as warnings and do not raise exceptions.
        """
        if not self.is_configured():
            logger.error(
                f"Telegram notifier is not configured or disabled. "
                f"bot_token={'set' if self.bot_token else 'missing'}, "
                f"chat_id={'set' if self.chat_id else 'missing'}, "
                f"enabled={self.enabled}"
            )
            return

        # Convert markdown to HTML if needed
        formatted_text = self._format_text(text)
        logger.info(f"Formatted message length: {len(formatted_text)} characters")

        # Check length and split if needed
        if len(formatted_text) > MAX_MESSAGE_LENGTH:
            logger.info(f"Message exceeds {MAX_MESSAGE_LENGTH} chars, splitting...")
            self.split_and_send(text)
            return

        # Send message
        self._send_message(formatted_text)

    def split_and_send(self, text: str) -> None:
        """
        Split long message and send in multiple parts.

        Args:
            text: Long message text to split and send.

        Note:
            Errors are logged as warnings and do not raise exceptions.
        """
        if not self.is_configured():
            logger.warning("Telegram notifier is not configured or disabled")
            return

        # Split by paragraphs first (double newlines)
        paragraphs = text.split("\n\n")
        current_chunk = []

        for para in paragraphs:
            # Convert paragraph to HTML
            formatted_para = self._format_text(para)
            test_chunk = "\n\n".join(current_chunk + [formatted_para])

            if len(test_chunk) <= MAX_MESSAGE_LENGTH:
                current_chunk.append(formatted_para)
            else:
                # Send current chunk if exists
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    self._send_message(chunk_text)
                    current_chunk = []

                # If single paragraph is too long, force split
                if len(formatted_para) > MAX_MESSAGE_LENGTH:
                    chunks = self._force_split(formatted_para, MAX_MESSAGE_LENGTH)
                    for chunk in chunks:
                        self._send_message(chunk)
                else:
                    current_chunk.append(formatted_para)

        # Send remaining chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            self._send_message(chunk_text)

    def _format_text(self, text: str) -> str:
        """
        Format markdown text for Telegram.

        Args:
            text: Markdown text.

        Returns:
            Formatted text (HTML or wrapped in <pre>).
        """
        if self.parse_mode == "HTML":
            if self.wrap_pre:
                # Wrap entire text in <pre> tags
                escaped_text = html.escape(text)
                return f"<pre>{escaped_text}</pre>"
            else:
                # Convert markdown to HTML
                return self._markdown_to_html(text)
        else:
            # For MarkdownV2, return as-is (caller should handle escaping)
            return text

    def _markdown_to_html(self, text: str) -> str:
        """
        Convert basic markdown to HTML for Telegram.

        Args:
            text: Markdown text.

        Returns:
            HTML formatted text.
        """
        # Escape HTML first
        text = html.escape(text)

        # Headers
        text = re.sub(r"^# (.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
        text = re.sub(r"^## (.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
        text = re.sub(r"^### (.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)

        # Bold
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

        # Italic
        text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)

        # Code
        text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)

        # Links (basic)
        text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)

        # Tables (convert to simple format)
        lines = text.split("\n")
        result_lines = []
        in_table = False

        for line in lines:
            if "|" in line and not line.strip().startswith("|"):
                # Table row
                if not in_table:
                    in_table = True
                cells = [cell.strip() for cell in line.split("|") if cell.strip()]
                if cells:
                    result_lines.append(" | ".join(cells))
            else:
                if in_table:
                    in_table = False
                result_lines.append(line)

        return "\n".join(result_lines)

    def _force_split(self, text: str, max_length: int) -> list[str]:
        """
        Force split text into chunks of maximum length.

        Args:
            text: Text to split.
            max_length: Maximum length per chunk.

        Returns:
            List of text chunks.
        """
        chunks = []
        current_chunk = ""

        # Split by lines first
        lines = text.split("\n")
        for line in lines:
            # Check if adding this line would exceed max_length
            test_chunk = current_chunk + ("\n" if current_chunk else "") + line
            if len(test_chunk) <= max_length:
                current_chunk = test_chunk
            else:
                # Save current chunk if it exists
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""

                # If single line is too long, split by words or characters
                if len(line) > max_length:
                    # Try splitting by words first
                    words = line.split()
                    current_line = ""
                    for word in words:
                        test_line = current_line + (" " if current_line else "") + word
                        if len(test_line) <= max_length:
                            current_line = test_line
                        else:
                            # Save current line if exists
                            if current_line:
                                chunks.append(current_line)
                            # If single word is too long, split by characters
                            if len(word) > max_length:
                                # Split word character by character
                                for i in range(0, len(word), max_length):
                                    chunks.append(word[i : i + max_length])
                                current_line = ""
                            else:
                                current_line = word
                    if current_line:
                        current_chunk = current_line
                else:
                    current_chunk = line

        # Save remaining chunk
        if current_chunk:
            chunks.append(current_chunk)

        # If no chunks were created (empty text), return empty list
        # If text is too long and couldn't be split, return at least one chunk
        if not chunks and text:
            # Fallback: split character by character
            for i in range(0, len(text), max_length):
                chunks.append(text[i : i + max_length])

        return chunks

    def _send_message(self, text: str) -> None:
        """
        Send a single message to Telegram API.

        Args:
            text: Message text to send.

        Note:
            Errors are logged as warnings and do not raise exceptions.
        """
        url = TELEGRAM_API_URL.format(token=self.bot_token)

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": self.parse_mode,
            "disable_web_page_preview": True,
        }

        try:
            logger.info(f"Sending Telegram message to chat_id={self.chat_id}, length={len(text)}")
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get("ok"):
                logger.info("Telegram message sent successfully")
            else:
                error_desc = result.get("description", "Unknown error")
                error_code = result.get("error_code", "N/A")
                logger.error(
                    f"Telegram API returned error: [{error_code}] {error_desc}. "
                    f"Response: {result}"
                )

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {str(e)}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {str(e)}", exc_info=True)


# Global instance
telegram_notifier = TelegramNotifier()
