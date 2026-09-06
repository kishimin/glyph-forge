import asyncio

import pytest

from app.request_limits import (
    ConcurrentRequestLimiter,
    RequestQueueFull,
    RequestQueueTimeout,
)


def test_concurrent_request_limiter_rejects_when_waiting_queue_is_full():
    async def exercise_limiter():
        limiter = ConcurrentRequestLimiter(
            max_concurrent=1,
            max_waiting=1,
            wait_timeout_seconds=1,
        )
        await limiter.acquire()
        waiting_request = asyncio.create_task(limiter.acquire())
        while limiter.waiting_count == 0:
            await asyncio.sleep(0)

        with pytest.raises(RequestQueueFull):
            await limiter.acquire()

        limiter.release()
        await waiting_request
        limiter.release()

    asyncio.run(exercise_limiter())


def test_concurrent_request_limiter_times_out_waiting_request():
    async def exercise_limiter():
        limiter = ConcurrentRequestLimiter(
            max_concurrent=1,
            max_waiting=1,
            wait_timeout_seconds=0.01,
        )
        await limiter.acquire()

        with pytest.raises(RequestQueueTimeout):
            await limiter.acquire()

        limiter.release()

    asyncio.run(exercise_limiter())
