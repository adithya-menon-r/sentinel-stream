"""
app/db/hbase_pool.py — HBase connection pool and shared row-key helpers.

The pool is created lazily on first access so uvicorn can start even when
HBase is temporarily unavailable.
"""
import hashlib
import time
from typing import Optional

import happybase

from app.core.config import settings, REVERSE_TS_BASE

# Lazy singleton — populated on first call to get_pool()
_pool: Optional[happybase.ConnectionPool] = None


def get_pool() -> happybase.ConnectionPool:
    """Return the shared ConnectionPool, creating it on first call."""
    global _pool
    if _pool is None:
        _pool = happybase.ConnectionPool(
            size=settings.HBASE_POOL_SIZE,
            host=settings.HBASE_HOST,
            port=settings.HBASE_PORT,
        )
    return _pool


# Convenience proxy so call-sites can still write `pool.connection()`
class _PoolProxy:
    def connection(self, *args, **kwargs):
        return get_pool().connection(*args, **kwargs)


pool = _PoolProxy()


def get_salt(identifier: str) -> str:
    """Return the 1-char hex salt for a given identifier.

    Must match the ingestion script:
        hashlib.md5(identifier.encode('utf-8')).hexdigest()[0]
    """
    return hashlib.md5(identifier.encode("utf-8")).hexdigest()[0]


def decode_counter(value: bytes) -> int:
    """Decode an HBase atomic counter stored as an 8-byte big-endian long."""
    return int.from_bytes(value, byteorder="big")


def reverse_ts_to_human(reverse_ts_str: str) -> str:
    """Convert a reverse-timestamp string to 'HH:MM:SS AM/PM'."""
    real_ts_ms = REVERSE_TS_BASE - int(reverse_ts_str)
    return time.strftime("%I:%M:%S %p", time.localtime(real_ts_ms / 1000))


def reverse_ts_to_minute(reverse_ts_str: str) -> str:
    """Return the 'HH:MM AM/PM' minute bucket for grouping revenue."""
    real_ts_ms = REVERSE_TS_BASE - int(reverse_ts_str)
    return time.strftime("%I:%M %p", time.localtime(real_ts_ms / 1000))
