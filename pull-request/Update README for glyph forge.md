# PR Draft: Update README for glyph-forge

## Summary

Updates `README.md` from a minimal two-line description into a project guide for glyph-forge.

## Changes

- Adds a project overview that explains `frame_text`, `inner_text`, and `outer_text`.
- Adds Python/FastAPI/Pillow/pytest tech stack badges.
- Documents the current directory structure.
- Adds setup steps for Python 3.12 and editable package installation without assuming the local checkout directory name.
- Adds Python and API usage examples.
- Uses a Python standard-library API request example instead of shell-specific curl quoting.
- Documents available API endpoints and request body fields.
- Adds command and troubleshooting sections.
- Allows the release workflow to update an existing GitHub Release when a tag is corrected.

## Verification

- Reviewed the README against the current repository files:
  - `app/main.py`
  - `app/schemas.py`
  - `src/glyph_forge/services/settings.py`
  - `requirements.txt`
  - `setup.py`
- Confirmed `v2.0.1` tag workflow completed successfully.

## Notes

- `v2.0.0` was restored to the previous release commit.
- `v2.0.1` points to the new README and release workflow updates.
- `.gitignore` is intentionally not included.
