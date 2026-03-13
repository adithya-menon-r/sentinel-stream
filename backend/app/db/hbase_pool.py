import hashlib
import time
import happybase

from typing import Optional
from app.core.config import settings, REVERSE_TS_BASE

_pool: Optional[happybase.ConnectionPool] = None

def get_pool() -> happybase.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = happybase.ConnectionPool(
            size=settings.HBASE_POOL_SIZE,
            host=settings.HBASE_HOST,
            port=settings.HBASE_PORT,
        )
    return _pool

class _PoolProxy:
    def connection(self, *args, **kwargs):
        return get_pool().connection(*args, **kwargs)

pool = _PoolProxy()

def get_salt(identifier: str) -> str:
    return hashlib.md5(identifier.encode("utf-8")).hexdigest()[0]

def decode_counter(value: bytes) -> int:
    """Decode an HBase counter stored as an 8-byte big-endian long."""
    return int.from_bytes(value, byteorder="big")

def reverse_ts_to_human(reverse_ts_str: str) -> str:
    real_ts_ms = REVERSE_TS_BASE - int(reverse_ts_str)
    return time.strftime("%I:%M:%S %p", time.localtime(real_ts_ms / 1000))

def reverse_ts_to_minute(reverse_ts_str: str) -> str:
    real_ts_ms = REVERSE_TS_BASE - int(reverse_ts_str)
    return time.strftime("%I:%M %p", time.localtime(real_ts_ms / 1000))
