from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.database import Base
from datetime import datetime

class Report(Base):
    """Model for stored reports."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)  # YYYY-MM-DD
    markdown = Column(Text)
    regime_label = Column(String)
    generated_at = Column(DateTime, default=datetime.utcnow)

class MarketSnapshot(Base):
    """Model for market data snapshots."""
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    type = Column(String)  # 'spot' or 'derivatives'
    data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

class SignalTrack(Base):
    """Model for tracking individual signals."""
    __tablename__ = "signal_tracks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    signal_id = Column(String)
    level = Column(String)
    title = Column(String)
    reason = Column(Text)
    value = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
