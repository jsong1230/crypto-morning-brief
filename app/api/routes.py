"""API route handlers."""

from fastapi import APIRouter, Depends, HTTPException

from app.config import settings
from app.models.report import (
    DailyReportRequestV2,
    DailyReportResponseV2,
)
from app.providers.base import MarketProvider
from app.providers.factory import get_market_provider
from app.services.report_service import ReportService
from app.database import get_db
from sqlalchemy.orm import Session
from app.services.db_service import DBService
from app.utils.logger import logger

router = APIRouter()


def get_report_service(
    provider: MarketProvider = Depends(get_market_provider),
) -> ReportService:
    """
    Dependency injection for ReportService.

    Args:
        provider: MarketProvider instance injected by FastAPI.

    Returns:
        ReportService instance.
    """
    # For now, ReportService uses CryptoDataProvider, so we'll keep the old service
    # This can be refactored later to use MarketProvider directly
    return ReportService()


# Keep the old service for backward compatibility
report_service = ReportService()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Health status response.
    """
    return {"status": "healthy", "service": "crypto-morning-brief"}


@router.post("/report/daily", response_model=DailyReportResponseV2)
async def generate_daily_report(
    request: DailyReportRequestV2,
    provider: MarketProvider = Depends(get_market_provider),
    db: Session = Depends(get_db),
) -> DailyReportResponseV2:
    """
    Generate a daily cryptocurrency report with signals and regime analysis.

    Args:
        request: DailyReportRequestV2 with symbols, keywords, and timezone.
        provider: MarketProvider instance injected by FastAPI.

    Returns:
        DailyReportResponseV2 with markdown, signals, and regime.

    Raises:
        HTTPException: If report generation fails.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from app.services.report_writer import ReportWriter
    from app.services.signal_engine import SignalEngine

    try:
        logger.info(
            f"Received daily report request: symbols={request.symbols}, "
            f"keywords={request.keywords}, tz={request.tz}"
        )

        # Validate provider availability
        if not provider.is_available():
            logger.error("Provider is not available")
            raise HTTPException(
                status_code=502,
                detail="Data provider is not available. Please try again later.",
            )

        # Get date in specified timezone
        try:
            tz = ZoneInfo(request.tz)
        except Exception as e:
            logger.warning(f"Invalid timezone {request.tz}, using Asia/Seoul: {e}")
            tz = ZoneInfo("Asia/Seoul")

        date_str = datetime.now(tz).strftime("%Y-%m-%d")

        # Fetch market data from provider
        try:
            spot_snapshot = await provider.get_spot_snapshot(request.symbols)
            derivatives_snapshot = await provider.get_derivatives_snapshot(request.symbols)
            news_snapshot = await provider.get_news_snapshot(request.keywords)
        except Exception as e:
            logger.error(f"Error fetching data from provider: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch market data from provider: {str(e)}",
            ) from e

        # Validate data availability
        if not spot_snapshot or not derivatives_snapshot:
            logger.error("Empty data received from provider")
            raise HTTPException(
                status_code=502,
                detail="No market data available from provider",
            )

        # Analyze signals
        try:
            from app.services.signal_engine import signal_engine
            signal_result = signal_engine.analyze(spot_snapshot, derivatives_snapshot)
        except Exception as e:
            logger.error(f"Error analyzing signals: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze market signals: {str(e)}",
            ) from e

        # Fetch stock market data (optional, non-blocking)
        korea_stocks = None
        us_stocks = None
        try:
            from app.providers.stock_provider import stock_provider

            # Fetch stock data asynchronously
            korea_stocks = await stock_provider.get_korea_stocks()
            us_stocks = await stock_provider.get_us_stocks()
        except Exception as e:
            logger.warning(f"Error fetching stock market data: {str(e)}, continuing without it")

        # Generate report
        try:
            writer = ReportWriter()
            markdown = writer.generate_report(
                date=date_str,
                spot_snapshot=spot_snapshot,
                derivatives_snapshot=derivatives_snapshot,
                signals=signal_result["signals"],
                regime=signal_result["regime"],
                news_snapshot=news_snapshot,
                korea_stocks=korea_stocks,
                us_stocks=us_stocks,
            )
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate report: {str(e)}",
            ) from e

        # Save to database (non-blocking for the report response)
        try:
            DBService.save_report(db, date_str, markdown, signal_result["regime"]["label"])
            DBService.save_market_snapshots(db, spot_snapshot, derivatives_snapshot)
            DBService.save_signals(db, signal_result["signals"])
            logger.info("Market data and report saved to database")
        except Exception as e:
            logger.warning(f"Failed to save to database: {str(e)}")
            # Don't fail the request if DB save fails

        logger.info("Daily report generated successfully")

        # Send to Telegram if enabled (non-blocking, failures are logged as warnings)
        telegram_sent = False
        if settings.send_telegram:
            try:
                from app.services.notifier import telegram_notifier

                if telegram_notifier.is_configured():
                    logger.info("Sending report to Telegram...")
                    telegram_notifier.send(markdown)
                    telegram_sent = True
                    logger.info("Report sent to Telegram successfully")
                else:
                    logger.warning("Telegram notifier is not configured")
            except Exception as e:
                logger.warning(f"Error sending Telegram notification: {str(e)}", exc_info=True)
                # Don't fail the request if Telegram fails

        return DailyReportResponseV2(
            date=date_str,
            markdown=markdown,
            signals=signal_result["signals"],
            regime=signal_result["regime"],
            telegram_sent=telegram_sent,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating daily report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}") from e


@router.get("/market/spot")
async def get_spot_snapshot(
    symbols: str = "BTC,ETH,SOL",
    provider: MarketProvider = Depends(get_market_provider),
) -> dict:
    """
    Get spot market snapshot.

    Args:
        symbols: Comma-separated list of symbols (e.g., "BTC,ETH,SOL").
        provider: MarketProvider instance injected by FastAPI.

    Returns:
        Dictionary with spot market data.
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        result = await provider.get_spot_snapshot(symbol_list)
        return {"data": result, "symbols": symbol_list}
    except Exception as e:
        logger.error(f"Error fetching spot snapshot: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch spot data: {str(e)}") from e


@router.get("/market/derivatives")
async def get_derivatives_snapshot(
    symbols: str = "BTC,ETH,SOL",
    provider: MarketProvider = Depends(get_market_provider),
) -> dict:
    """
    Get derivatives market snapshot.

    Args:
        symbols: Comma-separated list of symbols (e.g., "BTC,ETH,SOL").
        provider: MarketProvider instance injected by FastAPI.

    Returns:
        Dictionary with derivatives market data.
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        result = await provider.get_derivatives_snapshot(symbol_list)
        return {"data": result, "symbols": symbol_list}
    except Exception as e:
        logger.error(f"Error fetching derivatives snapshot: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch derivatives data: {str(e)}"
        ) from e


@router.get("/market/news")
async def get_news_snapshot(
    keywords: str = "Bitcoin,Ethereum,Solana",
    provider: MarketProvider = Depends(get_market_provider),
) -> dict:
    """
    Get news snapshot.

    Args:
        keywords: Comma-separated list of keywords (e.g., "Bitcoin,Ethereum,Solana").
        provider: MarketProvider instance injected by FastAPI.

    Returns:
        Dictionary with news data.
    """
    try:
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        result = await provider.get_news_snapshot(keyword_list)
        return {"data": result, "keywords": keyword_list, "count": len(result)}
    except Exception as e:
        logger.error(f"Error fetching news snapshot: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch news data: {str(e)}") from e


@router.get("/signals/analyze")
async def analyze_signals(
    symbols: str = "BTC,ETH,SOL",
    provider: MarketProvider = Depends(get_market_provider),
) -> dict:
    """
    Analyze market signals using rule-based engine.

    Args:
        symbols: Comma-separated list of symbols (e.g., "BTC,ETH,SOL").
        provider: MarketProvider instance injected by FastAPI.

    Returns:
        Dictionary with signals and regime analysis.
    """
    try:
        from app.services.signal_engine import SignalEngine

        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]

        # Fetch market data
        spot_snapshot = await provider.get_spot_snapshot(symbol_list)
        derivatives_snapshot = await provider.get_derivatives_snapshot(symbol_list)

        # Analyze with signal engine
        from app.services.signal_engine import signal_engine
        result = signal_engine.analyze(spot_snapshot, derivatives_snapshot)

        return {
            "symbols": symbol_list,
            "signals": result["signals"],
            "regime": result["regime"],
            "timestamp": result["timestamp"],
            "signals_count": len(result["signals"]),
        }
    except Exception as e:
        logger.error(f"Error analyzing signals: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze signals: {str(e)}") from e


@router.get("/report/morning-brief")
async def generate_morning_brief(
    date: str | None = None,
    symbols: str = "BTC,ETH,SOL",
    keywords: str = "Bitcoin,Ethereum,Solana",
    provider: MarketProvider = Depends(get_market_provider),
    db: Session = Depends(get_db),
) -> dict:
    """
    Generate morning brief report in Markdown format.

    Args:
        date: Date string in KST format (YYYY-MM-DD). If None, uses today.
        symbols: Comma-separated list of symbols (e.g., "BTC,ETH,SOL").
        keywords: Comma-separated list of keywords for news (e.g., "Bitcoin,Ethereum").
        provider: MarketProvider instance injected by FastAPI.

    Returns:
        Dictionary with markdown report.
    """
    try:
        from datetime import datetime, timedelta, timezone

        from app.services.report_writer import ReportWriter
        from app.services.signal_engine import SignalEngine

        # Get date (KST)
        if date is None:
            kst = timezone(timedelta(hours=9))
            date = datetime.now(kst).strftime("%Y-%m-%d")
        else:
            # Validate date format
            try:
                # Just validate format, timezone not needed for date string
                datetime.strptime(date, "%Y-%m-%d").date()  # noqa: DTZ007
            except ValueError as ve:
                raise HTTPException(
                    status_code=400, detail="Date must be in YYYY-MM-DD format"
                ) from ve

        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]

        # Fetch market data
        spot_snapshot = await provider.get_spot_snapshot(symbol_list)
        derivatives_snapshot = await provider.get_derivatives_snapshot(symbol_list)
        news_snapshot = await provider.get_news_snapshot(keyword_list)

        # Analyze signals
        from app.services.signal_engine import signal_engine
        signal_result = signal_engine.analyze(spot_snapshot, derivatives_snapshot)

        # Generate report
        from app.services.report_writer import ReportWriter
        writer = ReportWriter()
        markdown = writer.generate_report(
            date=date,
            spot_snapshot=spot_snapshot,
            derivatives_snapshot=derivatives_snapshot,
            signals=signal_result["signals"],
            regime=signal_result["regime"],
            news_snapshot=news_snapshot,
        )

        # Save to database
        try:
            DBService.save_report(db, date, markdown, signal_result["regime"]["label"])
            DBService.save_market_snapshots(db, spot_snapshot, derivatives_snapshot)
            DBService.save_signals(db, signal_result["signals"])
            logger.info("Morning brief data and report saved to database")
        except Exception as e:
            logger.warning(f"Failed to save morning brief to database: {str(e)}")

        return {
            "date": date,
            "markdown": markdown,
            "metadata": {
                "symbols": symbol_list,
                "keywords": keyword_list,
                "signals_count": len(signal_result["signals"]),
                "regime": signal_result["regime"]["label"],
                "generated_at": datetime.utcnow().isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating morning brief: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate morning brief: {str(e)}"
        ) from e
