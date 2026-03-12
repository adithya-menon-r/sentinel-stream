"""
Endpoint — Per-User HBase Fast Lookups.

These endpoints open a direct HBase connection and perform targeted prefix scans
to showcase O(1)-style low-latency reads.  They are intentionally kept separate
from the in-memory metrics so the difference in access patterns is obvious.

Endpoints
---------
GET /api/user/{user_id}/profile  — velocity counters (all hour buckets)
GET /api/user/{user_id}/history  — 10 most recent events from the event ledger
"""
import logging

import happybase
from fastapi import APIRouter, HTTPException

from app.core.config   import settings, TABLE_EVENT_LEDGER, TABLE_VELOCITY
from app.db.hbase_pool import decode_counter, get_salt, reverse_ts_to_human

log    = logging.getLogger("ids.router.users")
router = APIRouter(prefix="/api/user", tags=["users"])


@router.get("/{user_id}/profile")
def get_user_profile(user_id: str):
    """Fetch velocity counters for a user directly from HBase.

    Performs a row-prefix scan on user_velocity_counters and aggregates all
    hourly buckets for the given user.
    """
    salt   = get_salt(user_id)
    prefix = f"{salt}-{user_id}-".encode("utf-8")

    try:
        conn = happybase.Connection(settings.HBASE_HOST, port=settings.HBASE_PORT)
        try:
            table              = conn.table(TABLE_VELOCITY)
            total_tx_count     = 0
            total_tx_sum_cents = 0
            buckets            = []

            for row_key_bytes, data in table.scan(row_prefix=prefix):
                bucket   = row_key_bytes.decode("utf-8").split("-")[-1]
                tx_count = decode_counter(data[b"v:tx_count"])    if b"v:tx_count"    in data else 0
                tx_sum   = decode_counter(data[b"v:tx_sum_cents"]) if b"v:tx_sum_cents" in data else 0
                total_tx_count     += tx_count
                total_tx_sum_cents += tx_sum
                buckets.append({
                    "bucket":     bucket,
                    "tx_count":   tx_count,
                    "tx_sum_usd": round(tx_sum / 100, 2),
                })

            # Some datasets populate tx_sum_cents but not tx_count in velocity
            # counters. Fallback to ledger-derived successful transfer count so
            # Investigate does not show zero for active users.
            if total_tx_count == 0 and total_tx_sum_cents > 0:
                ledger_table = conn.table(TABLE_EVENT_LEDGER)
                for _, ev in ledger_table.scan(row_prefix=prefix):
                    ev_type = ev.get(b"m:type", b"").decode("utf-8")
                    status = ev.get(b"m:status", b"").decode("utf-8")
                    amt_raw = ev.get(b"m:amt", b"0").decode("utf-8")
                    try:
                        amt = float(amt_raw)
                    except ValueError:
                        amt = 0.0

                    if ev_type == "transfer_attempt" and status.upper() == "SUCCESS" and amt > 0:
                        total_tx_count += 1

            if not buckets:
                raise HTTPException(
                    status_code=404,
                    detail=f"No velocity data found for user '{user_id}'",
                )

            return {
                "user_id":          user_id,
                "salt":             salt,
                "total_tx_count":   total_tx_count,
                "total_tx_sum_usd": round(total_tx_sum_cents / 100, 2),
                "hourly_buckets":   buckets,
            }
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("Profile lookup failed for user=%s", user_id)
        raise HTTPException(status_code=503, detail=str(exc))


@router.get("/{user_id}/history")
def get_user_history(user_id: str):
    """Return the 10 most recent events for a user from user_event_ledger.

    Because row keys embed a reverse timestamp, the first rows HBase returns
    are the *newest* — no client-side sorting needed.
    """
    salt   = get_salt(user_id)
    prefix = f"{salt}-{user_id}-".encode("utf-8")

    try:
        conn = happybase.Connection(settings.HBASE_HOST, port=settings.HBASE_PORT)
        try:
            table  = conn.table(TABLE_EVENT_LEDGER)
            events = []

            for row_key_bytes, data in table.scan(row_prefix=prefix, limit=10):
                reverse_ts_str = row_key_bytes.decode("utf-8").split("-")[-1]
                events.append({
                    "timestamp": reverse_ts_to_human(reverse_ts_str),
                    "type":      data.get(b"m:type",   b"").decode("utf-8"),
                    "amount":    data.get(b"m:amt",    b"0").decode("utf-8"),
                    "ip":        data.get(b"m:ip",     b"").decode("utf-8"),
                    "device":    data.get(b"m:dev",    b"").decode("utf-8"),
                    "status":    data.get(b"m:status", b"").decode("utf-8"),
                })

            if not events:
                raise HTTPException(
                    status_code=404,
                    detail=f"No events found for user '{user_id}'",
                )

            return {"user_id": user_id, "salt": salt, "events": events}
        finally:
            conn.close()
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("History lookup failed for user=%s", user_id)
        raise HTTPException(status_code=503, detail=str(exc))
