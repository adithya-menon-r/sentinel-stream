"""
Background Task 2 — Counter Table Scanner.

Runs every 2 seconds, scanning user_velocity_counters and entity_risk_counters
for threshold breaches.  Broadcasts WebSocket alerts with session-scoped
deduplication so the same entity is never re-alerted.
"""
import asyncio
import logging
import time

import happybase

from app.core.config import (
    settings,
    TABLE_RISK,
    TABLE_VELOCITY,
    TOXIC_HITS_ALERT,
    VELOCITY_SUM_ALERT,
)
from app.db.hbase_pool       import decode_counter
from app.state               import alerted_toxic, alerted_velocity, user_totals
from app.services.ws_manager import manager

log = logging.getLogger("ids.scanner.counters")


async def counter_scanner_loop() -> None:
    """Infinite loop — scans velocity and risk counter tables every 2 seconds."""
    log.info("Counter scanner started.")

    while True:
        try:
            conn = happybase.Connection(settings.HBASE_HOST, port=settings.HBASE_PORT)
            try:
                # ── Velocity Fraud ─────────────────────────────────────────────
                vel_table = conn.table(TABLE_VELOCITY)
                # Snapshot user totals from velocity counters so Whale leaderboard
                # stays aligned with Investigate profile totals.
                user_totals_cents: dict[str, int] = {}
                for row_key_bytes, data in vel_table.scan(batch_size=500):
                    parts = row_key_bytes.decode("utf-8").split("-")
                    if len(parts) < 3:
                        continue
                    user_id = "-".join(parts[1:-1])
                    tx_sum  = decode_counter(data[b"v:tx_sum_cents"]) if b"v:tx_sum_cents" in data else 0

                    user_totals_cents[user_id] = user_totals_cents.get(user_id, 0) + tx_sum

                    if tx_sum > VELOCITY_SUM_ALERT and user_id not in alerted_velocity:
                        alerted_velocity.add(user_id)
                        log.warning("Velocity Fraud: user=%s  sum=$%.2f", user_id, tx_sum / 100)
                        await manager.broadcast({
                            "type":    "ALERT",
                            "pattern": "Velocity Fraud",
                            "entity":  user_id,
                            "detail":  f"Total transfer sum ${tx_sum / 100:,.2f} exceeds threshold.",
                            "ts":      time.strftime("%H:%M:%S"),
                        })

                # Bootstrap + continuous sync: refresh in-memory whale totals
                # from authoritative counter-table aggregates each scan cycle.
                user_totals.clear()
                user_totals.update({uid: cents / 100 for uid, cents in user_totals_cents.items()})

                # ── Toxic Node ─────────────────────────────────────────────────
                risk_table = conn.table(TABLE_RISK)
                for row_key_bytes, data in risk_table.scan(batch_size=500):
                    parts = row_key_bytes.decode("utf-8").split("-")
                    if len(parts) < 3:
                        continue
                    dev_id       = "-".join(parts[1:-1])
                    interactions = decode_counter(data[b"c:interactions"]) if b"c:interactions" in data else 0

                    if interactions > TOXIC_HITS_ALERT and dev_id not in alerted_toxic:
                        alerted_toxic.add(dev_id)
                        log.warning("Toxic Node: dev=%s  interactions=%d", dev_id, interactions)
                        await manager.broadcast({
                            "type":    "ALERT",
                            "pattern": "Toxic Node",
                            "entity":  dev_id,
                            "detail":  f"Device interacted with {interactions} distinct accounts.",
                            "ts":      time.strftime("%H:%M:%S"),
                        })

            finally:
                conn.close()

        except Exception:
            log.exception("Counter scanner error — retrying next cycle")

        await asyncio.sleep(2)
