"""
Financial IDS Backend — FastAPI entry point.

This file is intentionally thin.  All business logic lives in dedicated modules:
  app/state.py                    — global in-memory counters / dedup sets
  app/services/ws_manager.py      — WebSocket ConnectionManager singleton
  app/scanners/ledger.py          — delta ledger scanner (every 1 s)
  app/scanners/counters.py        — velocity + risk counter scanner (every 2 s)
  app/api/v1/endpoints/metrics.py — GET /api/metrics/* (in-memory reads)
  app/api/v1/endpoints/users.py   — GET /api/user/* (HBase direct lookups)

Run with:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.scanners.ledger   import ledger_scanner_loop
from app.scanners.counters import counter_scanner_loop
from app.api.v1.router     import api_router
from app.services.ws_manager import manager
from app.state             import minute_revenue, user_totals, device_counts

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
log = logging.getLogger("ids.main")


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting background scanner tasks …")
    tasks = [
        asyncio.create_task(ledger_scanner_loop(),  name="ledger_scanner"),
        asyncio.create_task(counter_scanner_loop(), name="counter_scanner"),
    ]
    log.info("Both background tasks launched.")
    yield
    log.info("Shutting down background tasks …")
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    log.info("Shutdown complete.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Financial IDS Backend",
    version="2.0.0",
    description="Live fraud detection over HBase — in-memory analytics + WebSocket alerts.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_router)


# ── WebSocket ─────────────────────────────────────────────────────────────────
@app.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket):
    """Live alert stream — push-only; client never needs to send messages."""
    await manager.connect(ws)
    try:
        while True:
            # receive() handles text, binary, ping/pong and disconnect frames —
            # unlike receive_text() it won't crash when the client stays silent.
            msg = await ws.receive()
            if msg["type"] == "websocket.disconnect":
                break
    except Exception:
        pass
    finally:
        manager.disconnect(ws)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status":          "ok",
        "ws_clients":      manager.client_count,
        "revenue_minutes": len(minute_revenue),
        "users_tracked":   len(user_totals),
        "devices_tracked": len(device_counts),
    }
