# Changelog

## 0.1.2

- On-demand, read-only `/diagnostics/privacy` report on a separate DVRIP session.
- Fixed allowlist of four candidate queries; no camera settings are changed.
- Cached background run, bounded RPC reads and sanitized report fields.
- Existing upstream HTTP PTZ and ONVIF routes retained.
- Simulated transport and HTTP tests; physical-camera diagnostic validation pending.

## 0.1.1

- Extract the pinned upstream package directly, avoiding its invalid pip build backend.
- Explicit Python base image and Home Assistant image labels.
- Direct Home Assistant repository link and installation limitations.

## 0.1.0

- Initial HAOS add-on for ARM64 and AMD64.
- Persistent DVRIP connection through `ptz-imou`.
- HTTP and ONVIF PTZ endpoints.
