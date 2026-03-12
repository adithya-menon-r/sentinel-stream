"""
Pattern 2 — Toxic Node (Botnet / Credential-Stuffing) Detection.

Scans ``entity_risk_counters`` every TOXIC_INTERVAL_S seconds for the *current*
day bucket.  Flags any device whose distinct-account interaction count exceeds
the configured threshold.
"""
import asyncio
import logging
import time

from app.core.config import (
    HEX_SALTS,
    TABLE_RISK,
    TOXIC_INTERACTIONS,
    TOXIC_INTERVAL_S,
)
from app.db.hbase_pool        import decode_counter, pool
from app.services.alert_store import alert_store

log = logging.getLogger("ids.toxic_node")


def _scan_toxic_for_day(day_bucket: str) -> None:
    """Iterate every salt prefix and check interaction counters for today."""
    day_bucket_bytes = day_bucket.encode("utf-8")

    with pool.connection() as conn:
        table = conn.table(TABLE_RISK)

        for salt in HEX_SALTS:
            prefix = salt.encode("utf-8")
            for row_key, data in table.scan(row_prefix=prefix):
                # Row key: <dev_salt>-<dev_id>-<YYYYMMDD>
                if not row_key.endswith(b"-" + day_bucket_bytes):
                    continue

                parts = row_key.decode("utf-8").split("-")
                # parts: [salt, *dev_id_parts, YYYYMMDD]
                dev_id = "-".join(parts[1:-1])

                interactions = (
                    decode_counter(data[b"c:interactions"])
                    if b"c:interactions" in data
                    else 0
                )

                if interactions > TOXIC_INTERACTIONS:
                    detail = (
                        f"interactions={interactions} distinct accounts on {day_bucket}"
                    )
                    added = alert_store.add_alert(
                        pattern="Toxic Node",
                        entity_type="device",
                        entity_id=dev_id,
                        detail=detail,
                        time_bucket=day_bucket,
                    )
                    if added:
                        log.warning("Toxic Node  ▸ dev=%s  %s", dev_id, detail)


async def toxic_node_loop() -> None:
    """Long-running async task — polls risk counters every interval."""
    log.info("Toxic-node detector started (interval=%ds)", TOXIC_INTERVAL_S)
    while True:
        try:
            day_bucket = time.strftime("%Y%m%d", time.gmtime())
            await asyncio.to_thread(_scan_toxic_for_day, day_bucket)
        except Exception:
            log.exception("Toxic-node detector error — will retry next cycle")
        await asyncio.sleep(TOXIC_INTERVAL_S)
