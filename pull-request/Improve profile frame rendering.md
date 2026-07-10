# PR Draft: Improve profile frame rendering

## Summary

Improves X profile image rendering so `frame_text` stays readable while preserving the intended glyph rule: `inner_text` draws the frame shape, and `outer_text` fills only the area outside that frame.

## Changes

- Renders profile images from separate inner and outer text layers.
- Clips `outer_text` to the outside of the frame mask and `inner_text` to the inside.
- Keeps `inner_text` and `outer_text` at the same profile font size.
- Uses a larger profile frame region so `frame_text` is less likely to collapse.
- Wraps X icon frame shapes more tightly for readability while keeping the background frame line wider.
- Adds regression tests for color isolation, frame shape readability, wrapping behavior, and text-size consistency.

## Verification

- `autoflake --check --recursive .`
- `isort --check-only .`
- `black --check .`
- `pytest -q`

## Notes

- Target PR branch: `feature/expansion`
- `blog/` and `diary/` files are intentionally left out of commit history.
