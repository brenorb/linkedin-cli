# Changelog

## 0.1.4 - 2026-07-02

- Reject orphaned `post create` flags that previously could fall through into a plain text post, including document titles without documents, article-only fields without `--article-url`, video-only metadata without a video source, upload-only video extras without a local upload, and poll duration without a poll question.
- Added regression coverage for those CLI validation cases plus the `profile voyager-session --format json` output path.

## 0.1.3 - 2026-07-01

- Refreshed `uv.lock` without local `exclude-newer` options so GitHub Actions can run `uv sync --locked --no-config` during release builds.
- Bumped the package metadata from `0.1.2` to `0.1.3` for the follow-up release tag after the failed `v0.1.2` build.

## 0.1.2 - 2026-07-01

- Added browser-cookie-backed LinkedIn Voyager session loading, including the `profile voyager-session` helper command.
- Added automatic `employment-history` fallback from the official API to Voyager and then to a live Chrome experience-page scrape on macOS.
- Added browser-scraped employment descriptions to the `employment-history` output.
- Added tests and documentation for the new employment-history fallback paths and browser session flow.
