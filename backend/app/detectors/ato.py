"""
Pattern 3 — Account Takeover (ATO) Detection.

Scans ``user_event_ledger`` every ATO_INTERVAL_S seconds with a bounded
``limit`` per salt prefix.  Groups events by user_id and applies a
state-machine to detect the classic ATO sequence:

    login_failed → password_reset → login_success (new IP/device) → transfer_attempt

Uses REVERSE_TS_BASE to recover real timestamps from row keys and enforces
a configurable time-window for the entire sequence.
"""
import asyncio
import logging
import time
from collections import defaultdict

from app.core.config import (
    ATO_INTERVAL_S,
    ATO_SCAN_LIMIT,
    ATO_TIME_WINDOW_MS,
    HEX_SALTS,
    REVERSE_TS_BASE,
    TABLE_EVENT_LEDGER,
)
from app.db.hbase_pool      import pool
from app.services.alert_store import alert_store

log = logging.getLogger("ids.ato")


def _parse_row_key(row_key: bytes):
    """Return (user_id, real_ts_ms) from a user_event_ledger row key.

    Key format: ``<salt>-<user_id>-<reverse_timestamp_ms>``
    """
    decoded = row_key.decode("utf-8")
    parts = decoded.split("-")
    # salt = parts[0], reverse_ts = parts[-1], user_id = everything in between
    reverse_ts = int(parts[-1])
    user_id = "-".join(parts[1:-1])
    real_ts_ms = REVERSE_TS_BASE - reverse_ts
    return user_id, real_ts_ms


def _detect_ato_in_events(events: list[dict]) -> bool:
    """Run a state-machine over a chronologically-ordered event list.

    Returns True if the ATO sequence is found within ATO_TIME_WINDOW_MS.

    Sequence:
        1. login_failed
        2. password_reset
        3. login_success  (from a DIFFERENT ip or device than step 1)
        4. transfer_attempt

    We record the IP/device from step 1 and verify step 3 differs.
    """
    state = 0  # 0=waiting-for-fail, 1=got-fail, 2=got-reset, 3=got-new-login
    anchor_ts = 0
    fail_ip = None
    fail_dev = None

    for ev in events:
        ev_type = ev["type"]
        ts = ev["ts"]

        # Reset state machine if window exceeded
        if state > 0 and (ts - anchor_ts) > ATO_TIME_WINDOW_MS:
            state = 0

        if state == 0 and ev_type == "login_failed":
            state = 1
            anchor_ts = ts
            fail_ip = ev["ip"]
            fail_dev = ev["dev"]

        elif state == 1 and ev_type == "login_failed":
            # Additional failures just refresh anchor
            anchor_ts = ts
            fail_ip = ev["ip"]
            fail_dev = ev["dev"]

        elif state == 1 and ev_type == "password_reset":
            state = 2

        elif state == 2 and ev_type == "login_success":
            # Must be from a NEW ip or device
            if ev["ip"] != fail_ip or ev["dev"] != fail_dev:
                state = 3
            else:
                # Same device — reset
                state = 0

        elif state == 3 and ev_type == "transfer_attempt":
            return True

    return False


def _scan_ato() -> None:
    """Scan recent events per salt prefix, group by user, run state-machine."""
    hour_bucket = time.strftime("%Y%m%d%H", time.gmtime())

    with pool.connection() as conn:
        table = conn.table(TABLE_EVENT_LEDGER)

        for salt in HEX_SALTS:
            prefix = salt.encode("utf-8")

            # Collect events grouped by user for this salt region
            user_events: dict[str, list[dict]] = defaultdict(list)

            for row_key, data in table.scan(
                row_prefix=prefix, limit=ATO_SCAN_LIMIT
            ):
                try:
                    user_id, real_ts_ms = _parse_row_key(row_key)
                except (ValueError, IndexError):
                    continue

                ev = {
                    "ts": real_ts_ms,
                    "type": data.get(b"m:type", b"").decode("utf-8"),
                    "ip": data.get(b"m:ip", b"").decode("utf-8"),
                    "dev": data.get(b"m:dev", b"").decode("utf-8"),
                }
                user_events[user_id].append(ev)

            # Analyse each user's events in chronological order
            for user_id, events in user_events.items():
                # Rows come newest-first (reverse_ts). Sort chronologically.
                events.sort(key=lambda e: e["ts"])

                if _detect_ato_in_events(events):
                    detail = (
                        f"ATO sequence detected: login_failed → password_reset → "
                        f"login_success (new device/IP) → transfer_attempt"
                    )
                    added = alert_store.add_alert(
                        pattern="Account Takeover",
                        entity_type="user",
                        entity_id=user_id,
                        detail=detail,
                        time_bucket=hour_bucket,
                    )
                    if added:
                        log.warning("Account Takeover  ▸ user=%s", user_id)


async def ato_loop() -> None:
    """Long-running async task — polls event ledger every interval."""
    log.info("ATO detector started (interval=%ds)", ATO_INTERVAL_S)
    while True:
        try:
            await asyncio.to_thread(_scan_ato)
        except Exception:
            log.exception("ATO detector error — will retry next cycle")
        await asyncio.sleep(ATO_INTERVAL_S)
