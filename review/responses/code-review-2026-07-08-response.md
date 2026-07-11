# Review Response: code-review-2026-07-08

## Medium: Invalid numeric request options escape FastAPI validation

Fixed in `fa8fd3e`.

The request schema now validates positive integer options at the FastAPI
boundary, so invalid values return 422 instead of reaching
`GlyphForgeConfig.__post_init__()`.

## Medium: Previous `frame_columns` / `frame_rows` API shape is silently ignored

Fixed in `fa8fd3e`.

The request schema now forbids extra fields, so legacy fields are rejected with
422 instead of being silently ignored.

## Low: Empty `frame_text` still reaches rendering and crashes

Fixed in `fa8fd3e`.

The request schema now requires non-empty `frame_text`, `inner_text`, and
`outer_text`, preventing empty input from reaching the renderer.

## Residual Risk: RGB channel range

Fixed in `fa8fd3e`.

RGB channel values are constrained to the 0-255 range in the API request schema.

## Verification

- `autoflake --check --recursive .`
- `isort --check-only .`
- `black --check .`
- `pytest -q`
