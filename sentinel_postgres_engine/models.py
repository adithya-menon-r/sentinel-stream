from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class RawEvent(Base):
    """Corresponds to HBase events"""
    __tablename__ = "raw_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String, nullable=False)
    amount = Column(Float, default=0.0)
    status = Column(String)
    ip_address = Column(String)
    device_id = Column(String, index=True)

    __table_args__ = (
        Index("ix_user_timestamp", "user_id", "timestamp"),
    )

class VelocityMetric(Base):
    """Corresponds to HBase user_activity"""
    __tablename__ = "velocity_metrics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    hour_bucket = Column(String, nullable=False) # YYYYMMDDHH
    tx_count = Column(Integer, default=0)
    tx_sum_cents = Column(BigInteger, default=0)

    __table_args__ = (
        Index("ix_user_hour", "user_id", "hour_bucket", unique=True),
    )

class RiskMetric(Base):
    """Corresponds to HBase risk_scores"""
    __tablename__ = "risk_metrics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    device_id = Column(String, nullable=False)
    day_bucket = Column(String, nullable=False) # YYYYMMDD
    interactions = Column(Integer, default=0)

    __table_args__ = (
        Index("ix_device_day", "device_id", "day_bucket", unique=True),
    )

class DeviceStats(Base):
    """For stress-testing row-level locking and MVCC"""
    __tablename__ = "device_stats"

    device_id = Column(String, primary_key=True)
    velocity_score = Column(Integer, default=0)
