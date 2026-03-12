"""
app/services/alert_store.py — TTL-aware in-memory alert store with deduplication.

Provides a module-level singleton ``alert_store`` used by all detector tasks.
"""
import threading
import time
import uuid
from typing import List, Optional

from app.core.config import ALERT_TTL_S


class AlertStore:
    """Append-only alert buffer with a dedup cache keyed on (pattern, entity, bucket)."""

    def __init__(self, ttl_s: int = ALERT_TTL_S) -> None:
        self._ttl_s = ttl_s
        self._lock = threading.Lock()
        self._alerts: List[dict] = []
        self._seen: dict[str, float] = {}  # dedup_key → expiry timestamp

    def add_alert(
        self,
        pattern: str,
        entity_type: str,
        entity_id: str,
        detail: str,
        time_bucket: str,
    ) -> bool:
        """Record a new alert.

        Returns False (and skips) if the same pattern+entity_id+time_bucket
        was already recorded within the TTL window.
        """
        dedup_key = f"{pattern}:{entity_id}:{time_bucket}"
        now = time.time()

        with self._lock:
            self._evict_stale(now)
            if dedup_key in self._seen:
                return False
            self._seen[dedup_key] = now + self._ttl_s
            self._alerts.append(
                {
                    "id":          uuid.uuid4().hex[:12],
                    "pattern":     pattern,
                    "entity_type": entity_type,
                    "entity_id":   entity_id,
                    "detail":      detail,
                    "time_bucket": time_bucket,
                    "timestamp":   now,
                }
            )
            return True

    def get_alerts(
        self, since_s: int = 3600, pattern: Optional[str] = None
    ) -> List[dict]:
        """Return alerts from the last *since_s* seconds, optionally filtered by pattern."""
        cutoff = time.time() - since_s
        with self._lock:
            out = [a for a in self._alerts if a["timestamp"] >= cutoff]
        if pattern:
            out = [a for a in out if a["pattern"] == pattern]
        return out

    def _evict_stale(self, now: float) -> None:
        expired = [k for k, exp in self._seen.items() if exp <= now]
        for k in expired:
            del self._seen[k]
        cutoff = now - self._ttl_s
        self._alerts = [a for a in self._alerts if a["timestamp"] >= cutoff]


# Module-level singleton
alert_store = AlertStore()
