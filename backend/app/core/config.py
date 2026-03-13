import sys
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    HBASE_HOST: str = "localhost"
    HBASE_PORT: int = 9090
    HBASE_POOL_SIZE: int = 10

settings = Settings()

# HBase table names
TABLE_EVENT_LEDGER = "events"
TABLE_VELOCITY     = "user_activity"
TABLE_RISK         = "risk_scores"

VELOCITY_SUM_CENTS = 500_000
VELOCITY_TX_COUNT  = 4
TOXIC_INTERACTIONS = 3

VELOCITY_INTERVAL_S = 10
TOXIC_INTERVAL_S    = 10
ALERT_TTL_S = 3600

REVERSE_TS_BASE = sys.maxsize
HEX_SALTS       = [format(i, "x") for i in range(16)]

VELOCITY_SUM_ALERT = 2_000_000
TOXIC_HITS_ALERT   = 50
