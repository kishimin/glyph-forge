import math
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass

import anyio
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

IMAGE_GENERATION_PATHS = frozenset(
    {
        "/images",
        "/images/x-icon",
        "/images/background",
        "/images/frame-file",
    }
)
RATE_LIMIT_REQUESTS_PER_MINUTE = 10
RATE_LIMIT_BURST_SIZE = 3
RATE_LIMIT_MAX_CLIENTS = 10_000
MAX_CONCURRENT_IMAGE_REQUESTS = 1
MAX_WAITING_IMAGE_REQUESTS = 4
IMAGE_REQUEST_QUEUE_TIMEOUT_SECONDS = 10.0


@dataclass
class _TokenBucket:
    tokens: float
    updated_at: float


class TokenBucketRateLimiter:
    def __init__(
        self,
        *,
        requests_per_minute: int,
        burst_size: int,
        max_clients: int = RATE_LIMIT_MAX_CLIENTS,
        time_source: Callable[[], float] = time.monotonic,
    ) -> None:
        self._tokens_per_second = requests_per_minute / 60
        self._burst_size = burst_size
        self._max_clients = max_clients
        self._time_source = time_source
        self._buckets: OrderedDict[str, _TokenBucket] = OrderedDict()
        self._lock = threading.Lock()

    def consume(self, client_key: str) -> int | None:
        now = self._time_source()
        with self._lock:
            bucket = self._buckets.get(client_key)
            if bucket is None:
                if len(self._buckets) >= self._max_clients:
                    self._buckets.popitem(last=False)
                bucket = _TokenBucket(float(self._burst_size), now)
                self._buckets[client_key] = bucket
            else:
                elapsed = max(0.0, now - bucket.updated_at)
                bucket.tokens = min(
                    float(self._burst_size),
                    bucket.tokens + elapsed * self._tokens_per_second,
                )
                bucket.updated_at = now
                self._buckets.move_to_end(client_key)

            if bucket.tokens < 1:
                seconds_until_token = (1 - bucket.tokens) / self._tokens_per_second
                return max(1, math.ceil(seconds_until_token))

            bucket.tokens -= 1
            return None

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


class RequestQueueFull(Exception):
    pass


class RequestQueueTimeout(Exception):
    pass


class ConcurrentRequestLimiter:
    def __init__(
        self,
        *,
        max_concurrent: int,
        max_waiting: int,
        wait_timeout_seconds: float,
    ) -> None:
        self._semaphore = threading.BoundedSemaphore(max_concurrent)
        self._max_waiting = max_waiting
        self._wait_timeout_seconds = wait_timeout_seconds
        self._waiting_count = 0
        self._lock = threading.Lock()

    @property
    def waiting_count(self) -> int:
        with self._lock:
            return self._waiting_count

    async def acquire(self) -> None:
        if self._semaphore.acquire(blocking=False):
            return

        with self._lock:
            if self._semaphore.acquire(blocking=False):
                return
            if self._waiting_count >= self._max_waiting:
                raise RequestQueueFull
            self._waiting_count += 1

        try:
            acquired = await anyio.to_thread.run_sync(
                lambda: self._semaphore.acquire(timeout=self._wait_timeout_seconds)
            )
        finally:
            with self._lock:
                self._waiting_count -= 1

        if not acquired:
            raise RequestQueueTimeout

    def release(self) -> None:
        self._semaphore.release()


class ImageRequestLimitsMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        *,
        rate_limiter: TokenBucketRateLimiter,
        concurrent_limiter: ConcurrentRequestLimiter,
    ) -> None:
        super().__init__(app)
        self._rate_limiter = rate_limiter
        self._concurrent_limiter = concurrent_limiter

    async def dispatch(self, request: Request, call_next):
        if request.method != "POST" or request.url.path not in IMAGE_GENERATION_PATHS:
            return await call_next(request)

        retry_after = self._rate_limiter.consume(_client_key(request))
        if retry_after is not None:
            return JSONResponse(
                status_code=429,
                content={"detail": "image generation rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )

        try:
            await self._concurrent_limiter.acquire()
        except (RequestQueueFull, RequestQueueTimeout):
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "image generation capacity is temporarily unavailable"
                },
                headers={"Retry-After": "1"},
            )

        try:
            return await call_next(request)
        finally:
            self._concurrent_limiter.release()


def _client_key(request: Request) -> str:
    # Forwarded headers are only safe when a trusted proxy rewrites request.client.
    return request.client.host if request.client is not None else "unknown"
