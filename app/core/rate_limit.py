from __future__ import annotations

import time
from collections import deque

from fastapi import HTTPException, status

from app.config import get_settings
from app.core.auth import AuthContext
from app.core.store import store


async def enforce_rate_limit(auth: AuthContext) -> None:
    settings = get_settings()
    key = f"{auth.user_type}:{auth.session_id}"
    now = time.time()
    window_start = now - settings.rate_limit_window_seconds

    with store.lock:
        bucket: deque[float] = store.rate_buckets[key]
        while bucket and bucket[0] < window_start:
            bucket.popleft()

        if len(bucket) >= settings.rate_limit_requests:
            retry_after = max(1, int(bucket[0] + settings.rate_limit_window_seconds - now))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Rate limit exceeded. Allowed {settings.rate_limit_requests} requests "
                    f"per {settings.rate_limit_window_seconds} seconds. Retry in {retry_after}s."
                ),
                headers={"Retry-After": str(retry_after)},
            )

        bucket.append(now)
