from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status


class RateLimiter:
    def __init__(
        self,
        *,
        max_requests: int = 60,
        window_seconds: int = 60,
    ):
        self._max_requests = max_requests
        self._window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, client_id: str) -> None:
        now = time.time()
        with self._lock:
            cutoff = now - self._window
            self._requests[client_id] = [
                t for t in self._requests[client_id] if t > cutoff
            ]

            if len(self._requests[client_id]) >= self._max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {self._max_requests} requests per {self._window}s",
                )

            self._requests[client_id].append(now)

    def get_remaining(self, client_id: str) -> int:
        now = time.time()
        with self._lock:
            cutoff = now - self._window
            active = [t for t in self._requests[client_id] if t > cutoff]
            return max(0, self._max_requests - len(active))