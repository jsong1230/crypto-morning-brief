"""Stock market data provider using Yahoo Finance."""

from datetime import datetime
from typing import Any

import yfinance as yf

from app.utils.logger import logger

# Stock symbol mappings
KOREA_STOCKS = {
    "KOSPI": "^KS11",  # KOSPI Index
    "KOSDAQ": "^KQ11",  # KOSDAQ Index
}

US_STOCKS = {
    "SPX": "^GSPC",  # S&P 500
    "DJI": "^DJI",  # Dow Jones Industrial Average
    "IXIC": "^IXIC",  # NASDAQ Composite
}


class StockMarketProvider:
    """Provider for stock market data using Yahoo Finance."""

    def __init__(self):
        """Initialize stock market provider."""
        self._http_timeout = 10.0

    async def get_korea_stocks(self) -> dict[str, Any]:
        """
        Get Korea stock market data (KOSPI, KOSDAQ).

        Returns:
            Dictionary with Korea stock market data.
        """
        result: dict[str, Any] = {}

        try:
            for symbol, yahoo_symbol in KOREA_STOCKS.items():
                try:
                    ticker = yf.Ticker(yahoo_symbol)
                    info = ticker.history(period="2d", interval="1d")

                    if info.empty:
                        logger.warning(f"No data available for {symbol}")
                        continue

                    # Get latest and previous day data
                    latest = info.iloc[-1]
                    prev = info.iloc[-2] if len(info) > 1 else latest

                    # Calculate change
                    current_price = float(latest["Close"])
                    prev_price = float(prev["Close"])
                    change_24h = ((current_price - prev_price) / prev_price) * 100

                    # Get volume
                    volume_24h = float(latest["Volume"]) if "Volume" in latest else 0.0

                    result[symbol] = {
                        "price": round(current_price, 2),
                        "change_24h": round(change_24h, 2),
                        "volume_24h": round(volume_24h, 0),
                        "high_24h": round(float(latest["High"]), 2),
                        "low_24h": round(float(latest["Low"]), 2),
                        "open": round(float(latest["Open"]), 2),
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    logger.debug(
                        f"Fetched {symbol}: {current_price:.2f} ({change_24h:+.2f}%)"
                    )

                except Exception as e:
                    logger.warning(f"Error fetching {symbol}: {str(e)}")
                    continue

            if result:
                logger.info(f"Successfully fetched {len(result)} Korea stock indices")
            else:
                logger.warning("No Korea stock data available")

        except Exception as e:
            logger.error(f"Error fetching Korea stock data: {str(e)}", exc_info=True)

        return result

    async def get_us_stocks(self) -> dict[str, Any]:
        """
        Get US stock market data (S&P 500, DOW, NASDAQ).

        Returns:
            Dictionary with US stock market data.
        """
        result: dict[str, Any] = {}

        try:
            for symbol, yahoo_symbol in US_STOCKS.items():
                try:
                    ticker = yf.Ticker(yahoo_symbol)
                    info = ticker.history(period="2d", interval="1d")

                    if info.empty:
                        logger.warning(f"No data available for {symbol}")
                        continue

                    # Get latest and previous day data
                    latest = info.iloc[-1]
                    prev = info.iloc[-2] if len(info) > 1 else latest

                    # Calculate change
                    current_price = float(latest["Close"])
                    prev_price = float(prev["Close"])
                    change_24h = ((current_price - prev_price) / prev_price) * 100

                    # Get volume
                    volume_24h = float(latest["Volume"]) if "Volume" in latest else 0.0

                    result[symbol] = {
                        "price": round(current_price, 2),
                        "change_24h": round(change_24h, 2),
                        "volume_24h": round(volume_24h, 0),
                        "high_24h": round(float(latest["High"]), 2),
                        "low_24h": round(float(latest["Low"]), 2),
                        "open": round(float(latest["Open"]), 2),
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                    logger.debug(
                        f"Fetched {symbol}: {current_price:.2f} ({change_24h:+.2f}%)"
                    )

                except Exception as e:
                    logger.warning(f"Error fetching {symbol}: {str(e)}")
                    continue

            if result:
                logger.info(f"Successfully fetched {len(result)} US stock indices")
            else:
                logger.warning("No US stock data available")

        except Exception as e:
            logger.error(f"Error fetching US stock data: {str(e)}", exc_info=True)

        return result

    def is_available(self) -> bool:
        """
        Check if provider is available.

        Returns:
            True (Yahoo Finance is always available).
        """
        return True


# Global instance
stock_provider = StockMarketProvider()

