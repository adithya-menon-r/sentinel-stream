import collections
from typing import Dict

minute_revenue: Dict[str, float] = collections.defaultdict(float)
user_totals: collections.Counter = collections.Counter()
device_counts: collections.Counter = collections.Counter()
auth_funnel: Dict[str, int] = {"success": 0, "failed": 0}
alerted_velocity: set = set()
alerted_toxic: set    = set()
