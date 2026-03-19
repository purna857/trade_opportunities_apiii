from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock


class InMemoryStore:
    def __init__(self) -> None:
        self.lock = Lock()
        self.rate_buckets: dict[str, deque[float]] = defaultdict(deque)
        self.session_stats: dict[str, dict] = {}

    def record_session_hit(self, session_id: str, sector: str, user_type: str) -> dict:
        now = datetime.now(timezone.utc)
        with self.lock:
            current = self.session_stats.get(session_id, {
                "session_id": session_id,
                "user_type": user_type,
                "request_count": 0,
                "created_at": now.isoformat(),
                "last_sector": None,
                "last_seen_at": now.isoformat(),
            })
            current["request_count"] += 1
            current["last_sector"] = sector
            current["last_seen_at"] = now.isoformat()
            self.session_stats[session_id] = current
            return current.copy()


store = InMemoryStore()
