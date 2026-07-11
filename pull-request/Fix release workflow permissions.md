# PR Draft: Fix release workflow permissions

## Summary

Fixes the GitHub Actions release job so tag builds can create a GitHub Release.

## Background

The `v2.0.0` release workflow failed at `ncipollo/release-action@v1` with:

```text
Error 403: Resource not accessible by integration
```

The release action uses `GITHUB_TOKEN` to create a GitHub Release, but the release job did not explicitly grant write access to repository contents.

## Changes

- Adds `contents: write` to the `release` job permissions.
- Keeps the permission scoped to the release job instead of broadening every job.

## Verification

- Confirmed the `v2.0.0` tag workflow completed successfully after the permission fix.
- Confirmed the GitHub Release was created:
  https://github.com/kishimin/glyph-forge/releases/tag/v2.0.0

## Notes

- The fix is limited to `.github/workflows/main.yaml`.
- `.gitignore` is intentionally not included.
