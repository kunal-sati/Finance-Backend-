import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    def __init__(self):
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def hit(
        self,
        *,
        bucket: str,
        identifier: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        now = time.monotonic()
        key = f"{bucket}:{identifier}"
        with self._lock:
            events = self._buckets[key]
            threshold = now - window_seconds
            while events and events[0] <= threshold:
                events.popleft()

            if len(events) >= limit:
                retry_after = max(1, int(window_seconds - (now - events[0])))
                return False, retry_after

            events.append(now)
            return True, 0

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


rate_limiter = InMemoryRateLimiter()


def limit_requests(*, bucket: str, limit: int, window_seconds: int):
    def dependency(request: Request):
        identifier = request.client.host if request.client else "unknown"
        allowed, retry_after = rate_limiter.hit(
            bucket=bucket,
            identifier=identifier,
            limit=limit,
            window_seconds=window_seconds,
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please retry later.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency
