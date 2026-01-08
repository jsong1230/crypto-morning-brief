"""Retry utilities with exponential backoff."""

import asyncio
from typing import Callable, TypeVar, Any
import httpx

from app.utils.logger import logger

T = TypeVar("T")


async def retry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = (httpx.RequestError, httpx.HTTPStatusError),
    retryable_status_codes: set[int] | None = None,
) -> T:
    """
    Retry a function with exponential backoff.

    Args:
        func: Async function to retry.
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay in seconds before first retry.
        max_delay: Maximum delay in seconds between retries.
        backoff_factor: Factor to multiply delay by after each retry.
        retryable_exceptions: Tuple of exceptions that should trigger retry.
        retryable_status_codes: Set of HTTP status codes that should trigger retry.
                               If None, only 429, 500, 502, 503, 504 are retried.

    Returns:
        Result of the function call.

    Raises:
        Last exception if all retries fail.
    """
    if retryable_status_codes is None:
        retryable_status_codes = {429, 500, 502, 503, 504}

    last_exception = None
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            result = await func()
            if attempt > 0:
                logger.info(f"Request succeeded after {attempt} retry(ies)")
            return result
        except retryable_exceptions as e:
            last_exception = e

            # Check if status code is retryable
            if isinstance(e, httpx.HTTPStatusError):
                status_code = e.response.status_code
                if status_code not in retryable_status_codes:
                    logger.warning(
                        f"Non-retryable status code {status_code}, not retrying"
                    )
                    raise

            # Don't retry on last attempt
            if attempt >= max_retries:
                logger.error(
                    f"Request failed after {max_retries} retries: {str(e)}"
                )
                raise

            # Log retry attempt
            if isinstance(e, httpx.HTTPStatusError):
                logger.warning(
                    f"Request failed with status {e.response.status_code}, "
                    f"retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})"
                )
            else:
                logger.warning(
                    f"Request failed: {str(e)}, "
                    f"retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})"
                )

            # Wait before retry
            await asyncio.sleep(delay)

            # Exponential backoff
            delay = min(delay * backoff_factor, max_delay)

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry logic failed unexpectedly")
