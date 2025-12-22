"""Tests for Telegram notifier."""

from unittest.mock import patch

import pytest

from app.services.notifier import TelegramNotifier


@pytest.fixture
def mock_notifier():
    """Create a mock notifier with test configuration."""
    notifier = TelegramNotifier()
    notifier.bot_token = "test_token"
    notifier.chat_id = "test_chat_id"
    notifier.enabled = True
    notifier.parse_mode = "HTML"
    notifier.wrap_pre = False
    return notifier


def test_notifier_is_configured(mock_notifier):
    """Test notifier configuration check."""
    assert mock_notifier.is_configured() is True

    mock_notifier.bot_token = None
    assert mock_notifier.is_configured() is False

    mock_notifier.bot_token = "test_token"
    mock_notifier.chat_id = None
    assert mock_notifier.is_configured() is False

    mock_notifier.chat_id = "test_chat_id"
    mock_notifier.enabled = False
    assert mock_notifier.is_configured() is False


def test_send_not_configured():
    """Test sending when not configured."""
    notifier = TelegramNotifier()
    notifier.bot_token = None
    # Should not raise, just log warning
    notifier.send("Test message")


@patch("app.services.notifier.requests.post")
def test_send_success(mock_post, mock_notifier):
    """Test successful Telegram message send."""
    mock_response = mock_post.return_value
    mock_response.json.return_value = {"ok": True}
    mock_response.raise_for_status = lambda: None

    # Should not raise
    mock_notifier.send("Test message")

    assert mock_post.called
    call_args = mock_post.call_args
    assert call_args[0][0] == "https://api.telegram.org/bottest_token/sendMessage"
    assert call_args[1]["json"]["chat_id"] == "test_chat_id"
    assert call_args[1]["json"]["parse_mode"] == "HTML"


@patch("app.services.notifier.requests.post")
def test_send_failure(mock_post, mock_notifier):
    """Test failed Telegram message send."""
    import requests

    mock_post.side_effect = requests.exceptions.RequestException("Connection error")

    # Should not raise, just log warning
    mock_notifier.send("Test message")


@patch("app.services.notifier.requests.post")
def test_split_and_send(mock_post, mock_notifier):
    """Test splitting and sending long message."""
    mock_response = mock_post.return_value
    mock_response.json.return_value = {"ok": True}
    mock_response.raise_for_status = lambda: None

    # Create a message longer than 4096 characters
    long_message = "A" * 5000

    mock_notifier.split_and_send(long_message)

    # Should have called post multiple times
    assert mock_post.call_count > 1


def test_markdown_to_html(mock_notifier):
    """Test markdown to HTML conversion."""
    markdown = "**bold** *italic* `code`"
    html = mock_notifier._markdown_to_html(markdown)
    assert "<b>bold</b>" in html
    assert "<i>italic</i>" in html
    assert "<code>code</code>" in html


def test_wrap_pre(mock_notifier):
    """Test wrapping in <pre> tags."""
    mock_notifier.wrap_pre = True
    text = "Test message"
    formatted = mock_notifier._format_text(text)
    assert formatted.startswith("<pre>")
    assert formatted.endswith("</pre>")


def test_force_split(mock_notifier):
    """Test force splitting text."""
    long_text = "A" * 5000
    chunks = mock_notifier._force_split(long_text, 1000)
    assert len(chunks) > 1
    assert all(len(chunk) <= 1000 for chunk in chunks)
    
    # Test with newlines
    long_text_with_newlines = "\n".join(["Line " + "A" * 200] * 30)
    chunks = mock_notifier._force_split(long_text_with_newlines, 500)
    assert len(chunks) >= 1
    assert all(len(chunk) <= 500 for chunk in chunks)
