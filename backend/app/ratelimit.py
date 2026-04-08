"""
Lightweight in-process rate limiter for public endpoints.

Uses a sliding-window counter per client IP. No external dependencies required.
For multi-instance deployments, consider replacing with Redis-backed slowapi.
"""

from __future__ import annotations

import time
from collections import defaultdict
from functools import wraps

from fastapi import HTTPException, Request, status


class RateLimiter:
    """Simple per-IP sliding-window rate limiter."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._check_count = 0

    def _cleanup(self, now: float) -> None:
        """Remove stale entries to prevent unbounded memory growth."""
        cutoff = now - self.window
        stale = [ip for ip, hits in self._hits.items() if not hits or hits[-1] < cutoff]
        for ip in stale:
            del self._hits[ip]

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def check(self, request: Request) -> None:
        """Raise 429 if the client has exceeded the rate limit."""
        ip = self._client_ip(request)
        now = time.monotonic()
        cutoff = now - self.window

        # Prune old hits for this IP
        hits = self._hits[ip] = [t for t in self._hits[ip] if t > cutoff]

        if len(hits) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window}s.",
            )

        hits.append(now)

        # Periodic cleanup: every 100 checks, purge stale IPs
        self._check_count += 1
        if self._check_count >= 100:
            self._check_count = 0
            self._cleanup(now)


# Shared instances for different endpoint groups
chat_limiter = RateLimiter(max_requests=30, window_seconds=60)   # 30 req/min
stats_limiter = RateLimiter(max_requests=60, window_seconds=60)  # 60 req/min
