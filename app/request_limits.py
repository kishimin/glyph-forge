import threading

import anyio
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message

IMAGE_GENERATION_PATHS = frozenset(
    {
        "/images",
        "/images/x-icon",
        "/images/background",
        "/images/frame-file",
    }
)
MAX_CONCURRENT_IMAGE_REQUESTS = 1
MAX_WAITING_IMAGE_REQUESTS = 4
IMAGE_REQUEST_QUEUE_TIMEOUT_SECONDS = 10.0
IMAGE_GENERATION_TIMEOUT_SECONDS = 30.0


class RequestQueueFull(Exception):
    pass


class RequestQueueTimeout(Exception):
    pass


class RequestBodyTooLarge(Exception):
    pass


def image_generation_capacity_response() -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "image generation capacity is temporarily unavailable"},
        headers={"Retry-After": "1"},
    )


def request_with_body_limit(request: Request, max_bytes: int) -> Request:
    received_bytes = 0

    async def receive() -> Message:
        nonlocal received_bytes
        message = await request.receive()
        if message["type"] == "http.request":
            received_bytes += len(message.get("body", b""))
            # Content-Length can be absent or dishonest, so enforce the limit on
            # actual ASGI bytes before the multipart parser receives each chunk.
            if received_bytes > max_bytes:
                raise RequestBodyTooLarge
        return message

    return Request(request.scope, receive=receive)


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
        concurrent_limiter: ConcurrentRequestLimiter,
    ) -> None:
        super().__init__(app)
        self._concurrent_limiter = concurrent_limiter

    async def dispatch(self, request: Request, call_next):
        if request.method != "POST" or request.url.path not in IMAGE_GENERATION_PATHS:
            return await call_next(request)

        try:
            await self._concurrent_limiter.acquire()
        except (RequestQueueFull, RequestQueueTimeout):
            return image_generation_capacity_response()

        try:
            return await call_next(request)
        finally:
            self._concurrent_limiter.release()
