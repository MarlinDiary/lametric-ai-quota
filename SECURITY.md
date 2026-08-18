# Security

This repository contains no provider credentials.

- Keep `LAMETRIC_TOKEN` in Railway Variables.
- Mount the Railway volume at `/data`; Codex and Claude credentials live below `/data/home`.
- Never commit `.env`, `.codex`, `.claude`, `.codexbar`, browser cookies, or command output containing tokens.
- The public LaMetric endpoint exposes only four display frames. `/health` redacts provider diagnostics.
- Rotate `LAMETRIC_TOKEN` after accidental disclosure and update the polling URL on the device.
