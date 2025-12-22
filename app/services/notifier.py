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

    def send(self, text: str) -> bool:
        """
        Send a message to Telegram.

        Args:
            text: Message text to send.

        Returns:
            True if message was sent successfully, False otherwise.

        Note:
            Errors are logged but do not raise exceptions.
        """
        if not self.is_configured():
            logger.error(
                f"❌ Telegram notifier is not configured or disabled. "
                f"bot_token={'set' if self.bot_token else 'missing'}, "
                f"chat_id={'set' if self.chat_id else 'missing'}, "
                f"enabled={self.enabled}"
            )
            return False

        # Convert markdown to HTML if needed
        formatted_text = self._format_text(text)
        logger.info(f"Formatted message length: {len(formatted_text)} characters")

        # Check length and split if needed
        if len(formatted_text) > MAX_MESSAGE_LENGTH:
            logger.info(f"Message exceeds {MAX_MESSAGE_LENGTH} chars, splitting...")
            return self.split_and_send(text)

        # Send message
        return self._send_message(formatted_text)

    def split_and_send(self, text: str) -> bool:
        """
        Split long message and send in multiple parts.

        Args:
            text: Long message text to split and send.

        Returns:
            True if at least one message was sent successfully, False otherwise.

        Note:
            Errors are logged but do not raise exceptions.
        """
        if not self.is_configured():
            logger.error("❌ Telegram notifier is not configured or disabled")
            return False

        # Split by paragraphs first (double newlines)
        paragraphs = text.split("\n\n")
        current_chunk = []
        success_count = 0

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
                    if self._send_message(chunk_text):
                        success_count += 1
                    current_chunk = []

                # If single paragraph is too long, force split
                if len(formatted_para) > MAX_MESSAGE_LENGTH:
                    chunks = self._force_split(formatted_para, MAX_MESSAGE_LENGTH)
                    for chunk in chunks:
                        if self._send_message(chunk):
                            success_count += 1
                else:
                    current_chunk.append(formatted_para)

        # Send remaining chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            if self._send_message(chunk_text):
                success_count += 1

        return success_count > 0

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
        # Process tables first (before HTML escaping)
        text = self._convert_tables_to_text(text)

        # Headers (before escaping)
        text = re.sub(r"^# (.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
        text = re.sub(r"^## (.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
        text = re.sub(r"^### (.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)

        # Bold (before escaping)
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

        # Italic (avoid matching bold markers)
        text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)

        # Code (before escaping)
        text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)

        # Links (before escaping)
        text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)

        # Now escape HTML for remaining text (but preserve our HTML tags)
        # Split by HTML tags to preserve them
        parts = re.split(r"(<[^>]+>)", text)
        escaped_parts = []
        for part in parts:
            if part.startswith("<") and part.endswith(">"):
                # This is an HTML tag, don't escape
                escaped_parts.append(part)
            else:
                # This is text, escape it
                escaped_parts.append(html.escape(part))
        text = "".join(escaped_parts)

        return text

    def _convert_tables_to_text(self, text: str) -> str:
        """
        Convert markdown tables to formatted text (Telegram HTML doesn't support <table> tags).

        Args:
            text: Markdown text with tables.

        Returns:
            Text with tables converted to formatted text.
        """
        # Telegram HTML parse mode only supports: <b>, <i>, <u>, <s>, <a>, <code>, <pre>
        lines = text.split("\n")
        result_lines = []
        in_table = False
        table_rows = []

        for line in lines:
            # Check if this is a separator line (contains only dashes, colons, spaces, and pipes)
            is_separator = bool(re.match(r"^\s*\|?[\s\-:]+\|", line))
            
            # Check if this is a table row (contains | and not a separator line)
            if "|" in line and not is_separator:
                # Table row
                if not in_table:
                    in_table = True
                
                # Extract cells (handle leading/trailing |)
                parts = line.split("|")
                # Remove empty strings from start/end (from leading/trailing |)
                cells = [part.strip() for part in parts if part.strip()]
                if cells:
                    table_rows.append(cells)
            else:
                # End of table (separator or non-table line)
                if in_table and table_rows:
                    # Format table as text with proper alignment
                    if table_rows:
                        # Calculate column widths
                        num_cols = max(len(row) for row in table_rows)
                        col_widths = [0] * num_cols
                        for row in table_rows:
                            for i, cell in enumerate(row):
                                if i < num_cols:
                                    col_widths[i] = max(col_widths[i], len(cell))
                        
                        # Format header (first row) with bold markers (will be converted to <b> later)
                        header = table_rows[0]
                        header_parts = []
                        for i, cell in enumerate(header):
                            width = col_widths[i] if i < len(col_widths) else len(cell)
                            header_parts.append(f"**{cell.ljust(width)}**")
                        result_lines.append(" | ".join(header_parts))
                        
                        # Add separator line
                        separator_parts = []
                        for i in range(num_cols):
                            width = col_widths[i] if i < len(col_widths) else 10
                            separator_parts.append("-" * width)
                        result_lines.append(" | ".join(separator_parts))
                        
                        # Format data rows
                        for row in table_rows[1:]:
                            row_parts = []
                            for i, cell in enumerate(row):
                                width = col_widths[i] if i < len(col_widths) else len(cell)
                                row_parts.append(cell.ljust(width))
                            result_lines.append(" | ".join(row_parts))
                    
                    table_rows = []
                    in_table = False
                
                # Skip separator lines, add other lines
                if not is_separator:
                    result_lines.append(line)

        # Close table if still open
        if in_table and table_rows:
            # Format remaining table
            num_cols = max(len(row) for row in table_rows)
            col_widths = [0] * num_cols
            for row in table_rows:
                for i, cell in enumerate(row):
                    if i < num_cols:
                        col_widths[i] = max(col_widths[i], len(cell))
            
            if table_rows:
                # Format header (first row) with bold
                header = table_rows[0]
                header_parts = []
                for i, cell in enumerate(header):
                    width = col_widths[i] if i < len(col_widths) else len(cell)
                    header_parts.append(f"<b>{cell.ljust(width)}</b>")
                result_lines.append(" | ".join(header_parts))
                
                # Add separator line
                separator_parts = []
                for i in range(num_cols):
                    width = col_widths[i] if i < len(col_widths) else 10
                    separator_parts.append("-" * width)
                result_lines.append(" | ".join(separator_parts))
                
                # Format data rows
                for row in table_rows[1:]:
                    row_parts = []
                    for i, cell in enumerate(row):
                        width = col_widths[i] if i < len(col_widths) else len(cell)
                        row_parts.append(cell.ljust(width))
                    result_lines.append(" | ".join(row_parts))

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

    def _send_message(self, text: str) -> bool:
        """
        Send a single message to Telegram API.

        Args:
            text: Message text to send.

        Returns:
            True if message was sent successfully, False otherwise.

        Note:
            Errors are logged but do not raise exceptions.
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
            
            # Get response body before raising error
            try:
                result = response.json()
            except Exception:
                result = {"error": "Failed to parse JSON response", "text": response.text[:500]}
            
            # Check status and log detailed error if failed
            if not response.ok:
                error_desc = result.get("description", result.get("error", "Unknown error"))
                error_code = result.get("error_code", response.status_code)
                logger.error(
                    f"❌ Telegram API error [{error_code}]: {error_desc}\n"
                    f"Response: {result}\n"
                    f"Request payload preview: text_length={len(text)}, parse_mode={self.parse_mode}"
                )
                # Log first 200 chars of text for debugging
                logger.debug(f"Message preview: {text[:200]}...")
                response.raise_for_status()
            
            if result.get("ok"):
                logger.info("✅ Telegram message sent successfully")
                return True
            else:
                error_desc = result.get("description", "Unknown error")
                error_code = result.get("error_code", "N/A")
                logger.error(
                    f"❌ Telegram API returned error: [{error_code}] {error_desc}. "
                    f"Response: {result}"
                )
                return False

        except requests.exceptions.HTTPError as e:
            # Try to get error details from response
            try:
                error_body = e.response.json() if e.response else {}
                error_desc = error_body.get("description", str(e))
                logger.error(
                    f"❌ HTTP error sending Telegram message: {error_desc}\n"
                    f"Status: {e.response.status_code if e.response else 'N/A'}\n"
                    f"Response: {error_body}"
                )
            except Exception:
                logger.error(f"❌ HTTP error sending Telegram message: {str(e)}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to send Telegram message: {str(e)}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error sending Telegram message: {str(e)}", exc_info=True)
            return False


# Global instance
telegram_notifier = TelegramNotifier()
