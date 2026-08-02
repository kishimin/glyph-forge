## Review Target

- Branch: `feature/expansion`
- Comparison: `1e518414e2ed5be18f85af556c84f56ef6f48303..2bc7b5d93972f3bf0061564ce58c214b7f70a6ce`
- Focus: output image limits, uploaded image validation, per-IP rate limiting, concurrent execution, and the waiting queue
- Files reviewed: all 14 files changed in the comparison, with detailed inspection of `app/main.py`, `app/request_limits.py`, `app/uploaded_image.py`, renderer services, and related tests

## Summary

The configured output dimensions and decoded-image metadata are bounded, and all 98 tests pass. However, an anonymous multipart request can consume unbounded temporary storage before the 2 MiB check, and the upload rendering path blocks the event loop. The agreed 30-second generation timeout is also not enforced.

---

**P1: Multipart parsing bypasses the effective upload-size boundary**

- ID: `CR-001`
- Path: `app/main.py:166`
- Evidence: `request.form()` parses the complete multipart body before `_uploaded_image()` calls `load_uploaded_image()`. The installed Starlette parser applies `max_part_size` only to non-file fields and writes file parts to `SpooledTemporaryFile` without a per-file byte limit. The endpoint then reads at most 2 MiB only from the selected `frame_image`; additional file parts and bytes beyond that point have already been received and stored.
- Impact: A public anonymous request can send one very large file or many ignored file parts and exhaust instance disk, file descriptors, or request-processing capacity despite the documented 2 MiB upload limit. The per-IP token bucket reduces frequency but does not bound damage per request or distributed traffic.
- Expected correction: Enforce a cumulative request-body limit while consuming ASGI `receive` messages, before multipart parsing, with enough allowance for the accepted file and multipart overhead. Also parse with `max_files=1` and reject unexpected file parts. Keep the decoded-image checks as defense in depth.
- Status: `open`

---

**P1: Uploaded-image rendering blocks the application event loop**

- ID: `CR-002`
- Path: `app/main.py:164`
- Evidence: `generate_image_from_frame_file()` is asynchronous, but after the upload read it performs Pillow decoding, grid conversion, glyph rendering, PNG encoding, and response construction synchronously on the event-loop thread at lines 167-187. A local ASGI probe replacing rendering with a 400 ms blocking operation delayed a callback scheduled for 50 ms until 406 ms, demonstrating that unrelated async work cannot run during this path.
- Impact: One accepted maximum-cost upload can delay `/health`, queue admission, timeout handling, and every other async request handled by that worker. On a single-process deployment this creates a straightforward availability failure even though the concurrency semaphore is set to one.
- Expected correction: Keep multipart I/O asynchronous, then move decode, render, and PNG encoding together into a bounded worker thread or dedicated rendering worker. Preserve the existing concurrency permit around that offloaded work and add a regression test proving `/health` remains responsive during upload rendering.
- Status: `open`

---

**P2: The generation execution timeout is not implemented**

- ID: `CR-003`
- Path: `app/request_limits.py:170`
- Evidence: `IMAGE_REQUEST_QUEUE_TIMEOUT_SECONDS` limits only semaphore acquisition. After a permit is obtained, `call_next(request)` has no 30-second execution deadline, and the permit is released only when that call returns. No server-level or worker-level generation timeout is present in the reviewed repository.
- Impact: A renderer hang or unexpectedly expensive valid input can retain the sole execution permit indefinitely; four requests then wait and all later generation requests receive `503` until the process is restarted.
- Expected correction: Execute rendering in an isolation boundary that can be terminated after 30 seconds, return a defined timeout response, and always reclaim the concurrency permit. A process worker or managed task worker is preferable because cancelling an awaited thread does not stop CPU work already running in that thread.
- Status: `open`

## Verification

- `python -m pytest -q`: passed, 98 tests
- `autoflake --check --recursive .`: passed
- `isort --check-only .`: passed
- `black --check .`: passed
- `flake8 .`: passed
- `mypy src`: passed
- `mypy app`: failed with four errors, including missing typed-package metadata and one `ValidationInfo.field_name` argument mismatch; this command is not part of the documented validation command and was not treated as a new priority finding
- Local ASGI event-loop responsiveness probe: reproduced the blocking behavior described in `CR-002`

## Residual Risk

- The limits are process-local. Multiple application processes or instances do not share rate-limit or concurrency state.
- Correct per-client behavior still depends on the deployment proxy supplying a trusted, rewritten `request.client`; that deployment configuration was not available in the repository and was not asserted as a code defect here.
- No external load test or production proxy integration test was run.
