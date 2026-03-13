import asyncio
import logging
import time

from app.core.config import (
    HEX_SALTS,
    TABLE_VELOCITY,
    VELOCITY_INTERVAL_S,
    VELOCITY_SUM_CENTS,
    VELOCITY_TX_COUNT,
)
from app.db.hbase_pool        import decode_counter, pool
from app.services.alert_store import alert_store

log = logging.getLogger("ids.rapid_transfers")

def _scan_velocity_for_hour(hour_bucket: str) -> None:
    hour_bucket_bytes = hour_bucket.encode("utf-8")

    with pool.connection() as conn:
        table = conn.table(TABLE_VELOCITY)

        for salt in HEX_SALTS:
            prefix = salt.encode("utf-8")
            for row_key, data in table.scan(row_prefix=prefix):
                if not row_key.endswith(b"-" + hour_bucket_bytes):
                    continue

                parts = row_key.decode("utf-8").split("-")
                user_id = "-".join(parts[1:-1])

                tx_count = decode_counter(data[b"v:tx_count"])    if b"v:tx_count"    in data else 0
                tx_sum   = decode_counter(data[b"v:tx_sum_cents"]) if b"v:tx_sum_cents" in data else 0

                if tx_sum > VELOCITY_SUM_CENTS or tx_count > VELOCITY_TX_COUNT:
                    detail = (
                        f"tx_count={tx_count}, "
                        f"tx_sum=₹{tx_sum / 100:.2f} "
                        f"in hour {hour_bucket}"
                    )
                    added = alert_store.add_alert(
                        pattern="Rapid Transfers",
                        entity_type="user",
                        entity_id=user_id,
                        detail=detail,
                        time_bucket=hour_bucket,
                    )
                    if added:
                        log.warning("Rapid Transfers  ▸ user=%s  %s", user_id, detail)


async def rapid_transfers_loop() -> None:
    log.info("Rapid-transfers detector started (interval=%ds)", VELOCITY_INTERVAL_S)
    while True:
        try:
            hour_bucket = time.strftime("%Y%m%d%H", time.gmtime())
            await asyncio.to_thread(_scan_velocity_for_hour, hour_bucket)
        except Exception:
            log.exception("Rapid-transfers detector error — will retry next cycle")
        await asyncio.sleep(VELOCITY_INTERVAL_S)

velocity_loop = rapid_transfers_loop
