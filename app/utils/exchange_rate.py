"""Exchange rate utility for currency conversion."""

import logging
from typing import Any

import requests

from app.utils.logger import logger

# Exchange rate API endpoints (free/public)
EXCHANGE_RATE_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"
BACKUP_API_URL = "https://open.er-api.com/v6/latest/USD"


def get_usd_to_krw() -> float:
    """
    Get current USD to KRW exchange rate.

    Returns:
        USD to KRW exchange rate (default: 1300.0 if API fails).
    """
    try:
        # Try primary API
        response = requests.get(EXCHANGE_RATE_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()

        if "rates" in data and "KRW" in data["rates"]:
            rate = float(data["rates"]["KRW"])
            logger.info(f"USD to KRW exchange rate fetched: {rate:.2f}")
            return rate

    except Exception as e:
        logger.warning(f"Failed to fetch exchange rate from primary API: {str(e)}")

    try:
        # Try backup API
        response = requests.get(BACKUP_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()

        if "rates" in data and "KRW" in data["rates"]:
            rate = float(data["rates"]["KRW"])
            logger.info(f"USD to KRW exchange rate fetched from backup API: {rate:.2f}")
            return rate

    except Exception as e:
        logger.warning(f"Failed to fetch exchange rate from backup API: {str(e)}")

    # Fallback to default
    logger.warning("Using default USD to KRW rate: 1300.0")
    return 1300.0


