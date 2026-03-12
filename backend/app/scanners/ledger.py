"""
Background Task 1 — Delta Ledger Scanner.

happybase 1.2.0 (Thrift-1) does NOT support the ``timerange`` keyword on
``Table.scan()`` — that lives in the newer Thrift-2 API.

Instead we maintain a per-salt rolling cursor:
  • The table is split into 16 salt prefixes ('0' … 'f').
  • Every cycle we advance ROWS_PER_SALT rows through each salt's key range.
  • A ``_seen_rows`` set deduplicates rows that appear in multiple cycles.
  • When a cursor reaches the end of its salt range it wraps back to the start,
    ensuring all users are eventually covered.

Coverage math (at 2000 rows/sec ingestion):
  16 salts × ROWS_PER_SALT(300) = 4 800 rows examined / cycle
  At 1 s interval → processes ≈ 2.4× current ingestion rate (enough to keep up)
"""
import asyncio
import logging
import time

import happybase

from app.core.config   import settings, BRUTE_FORCE_THRESH, HEX_SALTS, TABLE_EVENT_LEDGER
from app.db.hbase_pool import reverse_ts_to_minute
from app.state         import auth_funnel, device_counts, minute_revenue
from app.services.ws_manager import manager

log = logging.getLogger("ids.scanner.ledger")

# ── Cursor / dedup state (module-level so they persist across loop iterations) ─
ROWS_PER_SALT = 300          # rows fetched per salt per 1-second cycle
MEM_LIMIT_ROWS = 500_000     # ~40 MB ceiling on the seen-set; cleared when hit

_salt_cursors: dict[str, bytes] = {s: s.encode() for s in HEX_SALTS}
_seen_rows: set[bytes] = set()


def _salt_stop(salt: str) -> bytes:
    """Return the exclusive ``row_stop`` that is just past a salt's key range.

    e.g.  '0' → b'1',  'f' → b'g'
    All real row keys for salt ``s`` start with ``s + '-'`` so they all sort
    before ``chr(ord(s)+1)``.
    """
    return chr(ord(salt[0]) + 1).encode("utf-8")


async def ledger_scanner_loop() -> None:
    """Infinite loop — progressively scans user_event_ledger every second."""
    log.info("Ledger scanner started (cursor-based delta; happybase 1.2 compatible).")

    while True:
        try:
            batch_failed = 0   # new login_failed rows in this cycle only

            conn = happybase.Connection(settings.HBASE_HOST, port=settings.HBASE_PORT)
            try:
                table = conn.table(TABLE_EVENT_LEDGER)

                for salt in HEX_SALTS:
                    cursor         = _salt_cursors[salt]
                    stop           = _salt_stop(salt)
                    last_key: bytes | None = None
                    rows_this_salt = 0

                    for row_key_bytes, data in table.scan(
                        row_start=cursor,
                        row_stop=stop,
                        limit=ROWS_PER_SALT,
                        batch_size=ROWS_PER_SALT,
                    ):
                        rows_this_salt += 1
                        last_key = row_key_bytes

                        # ── Dedup: skip rows we already counted ─────────────
                        if row_key_bytes in _seen_rows:
                            continue
                        _seen_rows.add(row_key_bytes)

                        # ── Row key: <salt>-<user_id>-<reverse_ts_ms> ───────
                        row_key = row_key_bytes.decode("utf-8")
                        parts   = row_key.split("-")
                        if len(parts) < 3:
                            continue

                        reverse_ts_str = parts[-1]
                        user_id        = "-".join(parts[1:-1])

                        # ── Column decoding (bytes → str / float) ───────────
                        ev_type = data.get(b"m:type",   b"").decode("utf-8")
                        status  = data.get(b"m:status", b"").decode("utf-8")
                        amt_raw = data.get(b"m:amt",    b"0").decode("utf-8")
                        dev_id  = data.get(b"m:dev",    b"").decode("utf-8")

                        try:
                            amt = float(amt_raw)
                        except ValueError:
                            amt = 0.0

                        # ── Revenue per minute (successful transfers only) ───
                        if ev_type == "transfer_attempt" and status == "SUCCESS":
                            minute_revenue[reverse_ts_to_minute(reverse_ts_str)] += amt

                        # ── Device hit counter ───────────────────────────────
                        if dev_id:
                            device_counts[dev_id] += 1

                        # ── Auth funnel ──────────────────────────────────────
                        if ev_type == "login_success":
                            auth_funnel["success"] += 1
                        elif ev_type == "login_failed":
                            auth_funnel["failed"] += 1
                            batch_failed += 1

                    # ── Advance or wrap cursor ───────────────────────────────
                    if rows_this_salt < ROWS_PER_SALT or last_key is None:
                        # Reached the end of this salt's range → wrap around
                        _salt_cursors[salt] = salt.encode("utf-8")
                    else:
                        # More rows exist ahead — step past the last row seen
                        _salt_cursors[salt] = last_key + b"\x00"

                # ── Brute-force alert ────────────────────────────────────────
                if batch_failed > BRUTE_FORCE_THRESH:
                    log.warning("Mass Brute Force: %d new failures this cycle", batch_failed)
                    await manager.broadcast({
                        "type":    "ALERT",
                        "pattern": "Mass Brute Force",
                        "detail":  f"{batch_failed} new login_failed events detected in the last scan cycle.",
                        "ts":      time.strftime("%H:%M:%S"),
                    })

                # ── Evict seen-set when memory ceiling is hit ────────────────
                if len(_seen_rows) > MEM_LIMIT_ROWS:
                    log.info(
                        "Clearing seen-row cache (%d entries > limit %d) — resetting cursors",
                        len(_seen_rows), MEM_LIMIT_ROWS,
                    )
                    _seen_rows.clear()
                    for s in HEX_SALTS:
                        _salt_cursors[s] = s.encode("utf-8")

            finally:
                conn.close()

        except Exception:
            log.exception("Ledger scanner error — retrying next cycle")

        await asyncio.sleep(1)

