# Sentinel Stream — Financial Intrusion Detection System

Real-time fraud detection over Apache HBase. Processes 2,000+ transactions/second, broadcasts live alerts via WebSocket, and exposes REST metrics for a React dashboard.

## Repository Layout

```
sentinel-stream/
├── backend/    FastAPI + HBase fraud-detection engine
└── frontend/   React 18 + Vite real-time dashboard
```

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env       # edit HBASE_HOST etc.
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check + live counters |
| GET | `/api/metrics/revenue` | Per-minute transfer totals |
| GET | `/api/metrics/whales` | Top-10 users by volume |
| GET | `/api/metrics/auth` | Auth funnel stats |
| GET | `/api/user/{id}/profile` | User velocity profile from HBase |
| GET | `/api/user/{id}/history` | Last 10 user events from HBase |
| WS  | `/ws/alerts` | Live fraud alert stream |

## Fraud Detection Patterns

| Pattern | Trigger |
|---------|---------|
| Rapid Transfers | User transfers > $10,000 total in session |
| Suspicious Node | Device touches > 50 distinct accounts in a day |
