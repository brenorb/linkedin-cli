# Changelog

## 0.1.2 - 2026-07-01

- Added browser-cookie-backed LinkedIn Voyager session loading, including the `profile voyager-session` helper command.
- Added automatic `employment-history` fallback from the official API to Voyager and then to a live Chrome experience-page scrape on macOS.
- Added browser-scraped employment descriptions to the `employment-history` output.
- Added tests and documentation for the new employment-history fallback paths and browser session flow.
