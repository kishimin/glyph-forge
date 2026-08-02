# Review Responses public-image-safety-limits-20260802.md

## Finding 1: Multipart parsing bypasses the effective upload-size boundary

**Disposition:** fix-delegated

> **Original comment:**
> **P1: Multipart parsing bypasses the effective upload-size boundary**
>
> - ID: `CR-001`
> - Path: `app/main.py:166`
> - Evidence: `request.form()` parses the complete multipart body before `_uploaded_image()` calls `load_uploaded_image()`. The installed Starlette parser applies `max_part_size` only to non-file fields and writes file parts to `SpooledTemporaryFile` without a per-file byte limit. The endpoint then reads at most 2 MiB only from the selected `frame_image`; additional file parts and bytes beyond that point have already been received and stored.
> - Impact: A public anonymous request can send one very large file or many ignored file parts and exhaust instance disk, file descriptors, or request-processing capacity despite the documented 2 MiB upload limit. The per-IP token bucket reduces frequency but does not bound damage per request or distributed traffic.
> - Expected correction: Enforce a cumulative request-body limit while consuming ASGI `receive` messages, before multipart parsing, with enough allowance for the accepted file and multipart overhead. Also parse with `max_files=1` and reject unexpected file parts. Keep the decoded-image checks as defense in depth.
> - Status: `open`

**Reply:**
The frame-file endpoint now enforces a cumulative 2 MiB plus 64 KiB request-body limit on actual ASGI chunks before multipart parsing. Multipart parsing accepts at most one file and five expected text fields, while the existing file-byte and decoded-image validation remains in place. Oversized request bodies return `413`, and an additional file part is rejected with `400`.

> Fixed by FixAgent: Updated `app/request_limits.py`, `app/main.py`, and `tests/test_glyph_forge/test_app.py`; the RED request-boundary test now passes, and the integrated suite passes all 103 tests plus static checks.

---

## Finding 2: Uploaded-image rendering blocks the application event loop

**Disposition:** fix-delegated

> **Original comment:**
> **P1: Uploaded-image rendering blocks the application event loop**
>
> - ID: `CR-002`
> - Path: `app/main.py:164`
> - Evidence: `generate_image_from_frame_file()` is asynchronous, but after the upload read it performs Pillow decoding, grid conversion, glyph rendering, PNG encoding, and response construction synchronously on the event-loop thread at lines 167-187. A local ASGI probe replacing rendering with a 400 ms blocking operation delayed a callback scheduled for 50 ms until 406 ms, demonstrating that unrelated async work cannot run during this path.
> - Impact: One accepted maximum-cost upload can delay `/health`, queue admission, timeout handling, and every other async request handled by that worker. On a single-process deployment this creates a straightforward availability failure even though the concurrency semaphore is set to one.
> - Expected correction: Keep multipart I/O asynchronous, then move decode, render, and PNG encoding together into a bounded worker thread or dedicated rendering worker. Preserve the existing concurrency permit around that offloaded work and add a regression test proving `/health` remains responsive during upload rendering.
> - Status: `open`

**Reply:**
Multipart parsing and upload reads remain asynchronous. Image decoding, glyph rendering, and PNG encoding now run outside the event-loop thread while the existing middleware continues to hold the image-generation permit around the endpoint. A regression test confirms that `/health` responds before a deliberately blocked uploaded-image render completes.

> Fixed by FixAgent: Updated `app/main.py`, `app/uploaded_image.py`, and `tests/test_glyph_forge/test_app.py`; the event-loop responsiveness test passed repeatedly, and the integrated suite passes all 103 tests plus static checks.

---

## Finding 3: The generation execution timeout is not implemented

**Disposition:** fix-delegated

> **Original comment:**
> **P2: The generation execution timeout is not implemented**
>
> - ID: `CR-003`
> - Path: `app/request_limits.py:170`
> - Evidence: `IMAGE_REQUEST_QUEUE_TIMEOUT_SECONDS` limits only semaphore acquisition. After a permit is obtained, `call_next(request)` has no 30-second execution deadline, and the permit is released only when that call returns. No server-level or worker-level generation timeout is present in the reviewed repository.
> - Impact: A renderer hang or unexpectedly expensive valid input can retain the sole execution permit indefinitely; four requests then wait and all later generation requests receive `503` until the process is restarted.
> - Expected correction: Execute rendering in an isolation boundary that can be terminated after 30 seconds, return a defined timeout response, and always reclaim the concurrency permit. A process worker or managed task worker is preferable because cancelling an awaited thread does not stop CPU work already running in that thread.
> - Status: `open`

**Reply:**
All image rendering now runs in a Windows `spawn`-compatible child process with a 30-second execution deadline. On timeout, the worker is terminated and joined, with a kill fallback; the endpoint returns the existing `503` capacity response, and middleware releases the concurrency permit in its `finally` block. Tests verify both worker termination and successful permit reuse by the next request.

> Fixed by FixAgent: Added `app/image_worker.py` and `tests/test_glyph_forge/test_image_worker.py`, and updated `app/main.py`, `app/request_limits.py`, and `tests/test_glyph_forge/test_app.py`; timeout termination and permit-reuse tests pass with the integrated 103-test suite and static checks.

---
