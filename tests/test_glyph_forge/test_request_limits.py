import asyncio

import pytest

from app.request_limits import (
    ConcurrentRequestLimiter,
    RequestQueueFull,
    RequestQueueTimeout,
    TokenBucketRateLimiter,
)


def test_token_bucket_allows_burst_and_refills_at_configured_rate():
    current_time = [0.0]
    limiter = TokenBucketRateLimiter(
        requests_per_minute=10,
        burst_size=3,
        time_source=lambda: current_time[0],
    )

    assert [limiter.consume("client") for _ in range(3)] == [None, None, None]
    assert limiter.consume("client") == 6

    current_time[0] = 6.0

    assert limiter.consume("client") is None


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
