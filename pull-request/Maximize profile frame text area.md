# PR Draft: Maximize profile frame text area

## Summary

Updates profile image rendering so `frame_text` can use the full available canvas for both X profile banners and profile icons.

## Changes

- Sets X profile banner output to `1500x500`.
- Sets X profile icon output to `400x400`.
- Chooses the frame text line width dynamically from the text length and canvas shape.
- Allows profile frame masks to use the full canvas area.
- Adds regression tests for banner and icon frame coverage.
- Regenerates local `output/` samples for manual inspection.

## Verification

- `python -m pytest -q`
- `python -m black --check .`
- `python -m isort --check-only .`
- Japanese text scan outside `blog/` and `diary/`

## Notes

- `output/` images are generated artifacts and are not part of the committed source changes.
- No push was performed.
