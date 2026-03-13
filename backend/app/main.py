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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
log = logging.getLogger("ids.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting background scanner tasks …")
    tasks = [
        asyncio.create_task(ledger_scanner_loop(),  name="ledger_scanner"),
        asyncio.create_task(counter_scanner_loop(), name="counter_scanner"),
    ]
    log.info("Background tasks launched.")
    yield
    log.info("Shutting down background tasks …")
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    log.info("Shutdown complete.")

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

app.include_router(api_router)

@app.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            msg = await ws.receive()
            if msg["type"] == "websocket.disconnect":
                break
    except Exception:
        pass
    finally:
        manager.disconnect(ws)

@app.get("/health")
def health():
    return {
        "status":          "ok",
        "ws_clients":      manager.client_count,
        "revenue_minutes": len(minute_revenue),
        "users_tracked":   len(user_totals),
        "devices_tracked": len(device_counts),
    }
