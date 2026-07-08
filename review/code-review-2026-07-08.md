# Code Review: glyph-forge latest commits

Target commits:
- 53b9f67 test: characterize glyph image services
- a593f8d test: specify layout and color options
- fedc5bc feat: add configurable glyph rendering
- ab9c5cc test: specify compact image request
- ab78892 feat: accept compact image API requests
- b9178f0 refactor: optimize image thresholding
- 85e1296 refactor: format touched Python files
- 78def3d refactor: align lint formatting rules

## Findings

### Medium: Invalid numeric request options escape FastAPI validation and return 500

- `app/schemas.py:17`
- `app/schemas.py:18`
- `app/schemas.py:19`
- `app/main.py:30`
- `src/glyph_forge/services/settings.py:25`

`max_chars_per_line`, `frame_font_size`, and `output_font_size` are plain `int` fields in the request model, and the positivity checks live in `GlyphForgeConfig.__post_init__()`. Because `generate_image()` calls `generateImageRequest.to_config()` directly, invalid client JSON such as `{"max_chars_per_line": 0}` or `{"frame_font_size": 0}` raises `ValueError` inside the endpoint and becomes a 500 Internal Server Error instead of a request validation error.

Confirmed with `TestClient(app, raise_server_exceptions=False)`:
- `max_chars_per_line: 0` -> 500
- `frame_font_size: 0` -> 500

This is a FastAPI request boundary regression: client-controlled validation should be represented in the schema, for example with positive integer constraints, or converted to `HTTPException(422)` before reaching rendering.

### Medium: Previous `frame_columns` / `frame_rows` API shape is silently ignored

- `app/schemas.py:17`
- `app/main.py:26`
- `src/glyph_forge/services/convert_to_image.py:72`

The old `/images` request accepted explicit `frame_columns` and `frame_rows`; the new model replaces this with `max_chars_per_line` and computed row count. Pydantic's default extra-field behavior means old clients can still receive 200 responses, but their `frame_columns` and `frame_rows` values are ignored. For example, posting `frame_columns: 2` and `frame_rows: 3` with `frame_text: "ABCDEF"` now renders as the default compact layout `(100, 40)` instead of the old explicit grid shape `(40, 60)`.

Silent compatibility changes are harder for callers to detect than a clear 422. If this is an intentional API break, reject extra fields or document/version the request shape. If backward compatibility is required, keep accepting and honoring the legacy fields.

### Low: Empty `frame_text` still reaches rendering and crashes

- `app/main.py:18`
- `src/glyph_forge/services/convert_to_image.py:74`
- `src/glyph_forge/services/convert_text_to_image.py:91`

`inner_text` and `outer_text` are checked for emptiness, but `frame_text` is not. With an empty `frame_text`, `split_text_lines()` returns `[""]`, `horizontal_len` becomes `0`, and `text_2_img()` calls `range(0, 0, 0)`, raising `ValueError: range() arg 3 must not be zero`. Through the API this returns 500.

If empty frame text is invalid, validate it at the request boundary. If it should be valid, `text_2_img()` needs a non-zero grid width policy for the empty frame case.

## Verification

- Ran `pytest -q`: 13 passed, 1 Starlette/httpx deprecation warning.
- Reproduced the invalid-option and empty-frame API failures with FastAPI `TestClient`.
- Confirmed legacy request fields are currently accepted but ignored.

## Residual Risk

The new color fields validate tuple length, but not RGB channel range. Pillow accepted out-of-range values in a smoke test, so callers may get implementation-dependent color behavior unless channel values are constrained to 0-255.
