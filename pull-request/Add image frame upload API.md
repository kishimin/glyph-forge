# PR Draft: Add image frame upload API

## Summary

Adds a multipart image upload API that renders uploaded image shapes as text art.

## Changes

- Adds `POST /images/frame-file`.
- Reads an uploaded image from multipart form data.
- Converts the uploaded image to a binary grid using the existing grayscale threshold service.
- Renders dark image regions with `inner_text`.
- Renders light image regions with `outer_text`.
- Adds request validation for missing text, invalid colors, invalid font size, and invalid image files.
- Adds `python-multipart` to support form parsing in FastAPI.
- Adds service and API regression tests.

## Verification

- `python -m pytest -q`
- `python -m black --check .`
- `python -m isort --check-only .`
- Japanese text scan outside `blog/` and `diary/`

## Notes

- Generated `output/` files and local `input/` images are intentionally not committed.
- No push was performed.
