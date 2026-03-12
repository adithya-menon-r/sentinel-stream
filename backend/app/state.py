import collections
from typing import Dict

# Per-minute transfer totals: "HH:MM AM/PM" → cumulative USD
minute_revenue: Dict[str, float] = collections.defaultdict(float)

# Total money per user_id
user_totals: collections.Counter = collections.Counter()

# Raw event hits per device ID
device_counts: collections.Counter = collections.Counter()

# Authentication funnel counters
auth_funnel: Dict[str, int] = {"success": 0, "failed": 0}

# Session-scoped alert deduplication sets.
# Entities added here will not trigger a repeat WebSocket broadcast until restart.
alerted_velocity: set = set()   # user_ids flagged for Velocity Fraud
alerted_toxic: set    = set()   # dev_ids  flagged as Toxic Node
