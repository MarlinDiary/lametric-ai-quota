# LaMetric AI Quota

An intentionally small Railway adapter that reuses
[CodexBar](https://github.com/steipete/CodexBar) to show Codex and Claude Code
weekly quota on LaMetric TIME.

The device rotates exactly four frames:

```text
[Codex]  63%
[Codex]  2d11h
[Claude] 41%
[Claude] 4d07h
```

The percentage is weekly quota **remaining**. The second frame is time until
the weekly reset. There are no `W` or `R` prefixes.

## Pixel icons

<p>
  <img src="assets/codex.png" width="64" height="64" alt="Codex 8x8 pixel icon">
  <img src="assets/claude.png" width="64" height="64" alt="Claude 8x8 pixel icon">
</p>

There are exactly two source icons, both exact 8×8 PNGs. The white terminal
icon is reused for both Codex frames. The `C` uses Claude's `#D97757` accent
and is reused for both Claude Code frames. `scripts/generate_icons.py`
recreates them deterministically.

## Data flow

```text
Codex + Claude OAuth
        |
        v
CodexBar 0.52.0
        |
        v
This adapter (5 minute cache)
        |
        v
Railway HTTPS -> LaMetric TIME
```

The repository does not reimplement provider APIs. It invokes the pinned
CodexBar CLI, extracts `usage.secondary`, and maps `usedPercent` plus
`resetsAt` to the four LaMetric frames.

## Local verification

```bash
./scripts/verify.sh
```

This regenerates the icons, compiles the Python package, runs the test suite,
starts the real HTTP server against a CodexBar fixture, and checks the literal
frame sequence.

## Railway deployment

1. Create a Railway service from this repository.
2. Attach a persistent volume at `/data`.
3. Generate a secret with `python3 scripts/generate_token.py` and save it as
   `LAMETRIC_TOKEN` in Railway Variables.
4. Generate a Railway domain for the service.
5. Open a Railway SSH session and establish the two subscription sessions:

```bash
codex login --device-auth
claude auth login --claudeai
codexbar usage --provider codex --source oauth --format json --json-only
codexbar usage --provider claude --source oauth --format json --json-only
```

The container includes pinned Codex and Claude Code CLIs so they own their
credential refresh lifecycle. Their files persist under `/data/home`.

Configure the LaMetric Poll Indicator or My Data DIY app with:

```text
https://YOUR_RAILWAY_DOMAIN/v1/lametric/YOUR_LAMETRIC_TOKEN
```

The recommended polling interval is five minutes.

## Endpoints

- `GET /health` — public, credential-free readiness with redacted errors.
- `GET /v1/lametric/<token>` — the four LaMetric frames.

Unknown paths return `404`. The secret path is omitted from service logs.

## Pinned upstream components

| Component | Version |
|---|---:|
| CodexBar CLI | 0.52.0 |
| OpenAI Codex CLI | 0.147.0 |
| Anthropic Claude Code | 2.1.234 |
| Node.js | 22 |

CodexBar release archives are verified with their published SHA-256 values in
the Docker build.

## Rollback

To create a local rollback commit for a deployed change:

```bash
./scripts/rollback.sh COMMIT_TO_REVERT
./scripts/verify.sh
git push
```

Railway will deploy the verified rollback commit through the same GitHub
integration.

## License

MIT. CodexBar remains a separate MIT-licensed upstream dependency.
