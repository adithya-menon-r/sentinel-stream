"""
app/core/config.py: Application settings.

Deployment-specific values (host, port, pool size) are loaded from environment
variables or a backend/.env file.  All other constants (thresholds, table names,
intervals) are fixed and live here alongside the settings object so every module
has a single import source for configuration.
"""
import sys
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Values that differ between environments (dev / staging / prod)."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    HBASE_HOST: str = "localhost"
    HBASE_PORT: int = 9090
    HBASE_POOL_SIZE: int = 10


# Module-level singleton — import with: from app.core.config import settings
settings = Settings()

# ── HBase table names ─────────────────────────────────────────────────────────
TABLE_EVENT_LEDGER = "user_event_ledger"
TABLE_VELOCITY     = "user_velocity_counters"
TABLE_RISK         = "entity_risk_counters"

# ── Fraud detection thresholds ────────────────────────────────────────────────
VELOCITY_SUM_CENTS = 500_000   # $5,000.00 — detector alert threshold
VELOCITY_TX_COUNT  = 4
TOXIC_INTERACTIONS = 3

# ── Background task poll intervals (seconds) ──────────────────────────────────
VELOCITY_INTERVAL_S = 10
TOXIC_INTERVAL_S    = 10
ATO_INTERVAL_S      = 15

# ── ATO detector ──────────────────────────────────────────────────────────────
ATO_SCAN_LIMIT     = 5000
ATO_TIME_WINDOW_MS = 300_000   # 5-minute sliding window

# ── Alert store deduplication ─────────────────────────────────────────────────
ALERT_TTL_S = 3600             # 1-hour TTL

# ── Row-key helpers ───────────────────────────────────────────────────────────
REVERSE_TS_BASE = sys.maxsize
HEX_SALTS       = [format(i, "x") for i in range(16)]  # '0' … 'f'

# ── WebSocket broadcast thresholds (scanner v2) ───────────────────────────────
VELOCITY_SUM_ALERT = 1_000_000  # cents → $10,000 total
TOXIC_HITS_ALERT   = 50         # distinct-account interactions per device
BRUTE_FORCE_THRESH = 50         # login_failed events per 1-second cycle
