#!/usr/bin/env python3
"""Script to run daily report generation locally.

This script can be executed directly or via cron to generate daily reports.
"""

import asyncio
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.providers.factory import get_market_provider
from app.services.report_writer import ReportWriter
from app.services.signal_engine import SignalEngine
from app.services.notifier import telegram_notifier
from app.utils.logger import logger


async def generate_daily_report(
    symbols: list[str] | None = None,
    keywords: list[str] | None = None,
    tz: str = "Asia/Seoul",
) -> str:
    """
    Generate daily report.

    Args:
        symbols: List of cryptocurrency symbols (default: ["BTC", "ETH"]).
        keywords: List of keywords for news (default: ["bitcoin", "ethereum"]).
        tz: Timezone string (default: "Asia/Seoul").

    Returns:
        Generated markdown report.
    """
    from zoneinfo import ZoneInfo

    if symbols is None:
        symbols = ["BTC", "ETH"]
    if keywords is None:
        keywords = ["bitcoin", "ethereum"]

    # Get date in specified timezone
    try:
        tz_obj = ZoneInfo(tz)
    except Exception as e:
        logger.warning(f"Invalid timezone {tz}, using Asia/Seoul: {e}")
        tz_obj = ZoneInfo("Asia/Seoul")

    date_str = datetime.now(tz_obj).strftime("%Y-%m-%d")

    logger.info(f"Generating daily report for {date_str} (timezone: {tz})")
    logger.info(f"Symbols: {symbols}, Keywords: {keywords}")

    # Get provider
    provider = get_market_provider()
    if not provider.is_available():
        error_msg = "Data provider is not available"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Fetch market data
    logger.info("Fetching market data...")
    spot_snapshot = await provider.get_spot_snapshot(symbols)
    derivatives_snapshot = await provider.get_derivatives_snapshot(symbols)
    news_snapshot = await provider.get_news_snapshot(keywords)

    if not spot_snapshot or not derivatives_snapshot:
        error_msg = "No market data available from provider"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Analyze signals
    logger.info("Analyzing signals...")
    engine = SignalEngine()
    signal_result = engine.analyze(spot_snapshot, derivatives_snapshot)

    # Generate report
    logger.info("Generating markdown report...")
    writer = ReportWriter()
    markdown = writer.generate_report(
        date=date_str,
        spot_snapshot=spot_snapshot,
        derivatives_snapshot=derivatives_snapshot,
        signals=signal_result["signals"],
        regime=signal_result["regime"],
        news_snapshot=news_snapshot,
    )

    logger.info(f"Report generated successfully ({len(markdown)} characters)")

    # Send to Telegram if enabled
    from app.config import settings

    if settings.send_telegram:
        if telegram_notifier.is_configured():
            logger.info("Sending report to Telegram...")
            try:
                telegram_notifier.send(markdown)
                logger.info("Report sent to Telegram successfully")
            except Exception as e:
                logger.warning(f"Error sending Telegram notification: {str(e)}")
        else:
            logger.warning("Telegram notifier is not configured")
    else:
        logger.info("Telegram notifier is disabled (SEND_TELEGRAM=false)")

    return markdown


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate daily crypto morning brief report")
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["BTC", "ETH"],
        help="Cryptocurrency symbols (default: BTC ETH)",
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=["bitcoin", "ethereum"],
        help="News keywords (default: bitcoin ethereum)",
    )
    parser.add_argument(
        "--tz",
        default="Asia/Seoul",
        help="Timezone (default: Asia/Seoul)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (optional, prints to stdout if not specified)",
    )

    args = parser.parse_args()

    try:
        markdown = await generate_daily_report(
            symbols=args.symbols,
            keywords=args.keywords,
            tz=args.tz,
        )

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
            logger.info(f"Report saved to: {output_path}")
        else:
            print("\n" + "=" * 80)
            print("DAILY REPORT")
            print("=" * 80 + "\n")
            print(markdown)

        sys.exit(0)

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

