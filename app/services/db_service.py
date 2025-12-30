from sqlalchemy.orm import Session
from app.models.db import Report, MarketSnapshot, SignalTrack
from datetime import datetime
from typing import Any, List, Optional

class DBService:
    """Service for database operations."""

    @staticmethod
    def save_report(
        db: Session, 
        date: str, 
        markdown: str, 
        regime_label: str
    ) -> Report:
        """Save a generated report."""
        db_report = Report(
            date=date,
            markdown=markdown,
            regime_label=regime_label,
            generated_at=datetime.utcnow()
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        return db_report

    @staticmethod
    def save_market_snapshots(
        db: Session, 
        spot_snapshot: dict, 
        derivatives_snapshot: dict
    ):
        """Save market snapshots for all symbols."""
        # Save spot
        for symbol, data in spot_snapshot.items():
            db_snap = MarketSnapshot(
                symbol=symbol,
                type="spot",
                data=data,
                timestamp=datetime.utcnow()
            )
            db.add(db_snap)
        
        # Save derivatives
        for symbol, data in derivatives_snapshot.items():
            db_snap = MarketSnapshot(
                symbol=symbol,
                type="derivatives",
                data=data,
                timestamp=datetime.utcnow()
            )
            db.add(db_snap)
        
        db.commit()

    @staticmethod
    def save_signals(db: Session, signals: List[dict]):
        """Save generated signals."""
        for signal in signals:
            # Extract symbol from signal ID if possible (usually SYMBOL_id)
            symbol = signal.get("id", "").split("_")[0]
            
            db_signal = SignalTrack(
                symbol=symbol,
                signal_id=signal.get("id"),
                level=signal.get("level"),
                title=signal.get("title"),
                reason=signal.get("reason"),
                value=str(signal.get("value")),
                timestamp=datetime.utcnow()
            )
            db.add(db_signal)
        db.commit()

    @staticmethod
    def get_latest_report(db: Session) -> Optional[Report]:
        """Get the most recently generated report."""
        return db.query(Report).order_by(Report.generated_at.desc()).first()

    @staticmethod
    def get_reports_by_date(db: Session, date: str) -> List[Report]:
        """Get reports for a specific date."""
        return db.query(Report).filter(Report.date == date).all()
