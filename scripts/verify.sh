#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT"

python3 scripts/generate_icons.py
PYTHONPATH=src python3 -m compileall -q src
PYTHONPATH=src python3 -m unittest discover -s tests -v

port=$(python3 - <<'PY'
import socket
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
)
token=verification-token-with-32-characters
LAMETRIC_TOKEN="$token" \
CODEXBAR_BINARY="$ROOT/tests/fixture_codexbar.py" \
REFRESH_INTERVAL=3600 \
HOST=127.0.0.1 \
PORT="$port" \
PYTHONPATH=src \
python3 -m lametric_quota > /tmp/lametric-ai-quota-verify.log 2>&1 &
pid=$!
trap 'kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true' EXIT INT TERM

python3 - "$port" "$token" <<'PY'
import json
import sys
import time
from urllib.request import urlopen

port, token = sys.argv[1:]
base = f"http://127.0.0.1:{port}"
for _ in range(50):
    try:
        with urlopen(f"{base}/health", timeout=1) as response:
            health = json.load(response)
        if health.get("ready"):
            break
    except Exception:
        pass
    time.sleep(0.1)
else:
    raise SystemExit("service did not become ready")

with urlopen(f"{base}/v1/lametric/{token}", timeout=2) as response:
    payload = json.load(response)
texts = [frame["text"] for frame in payload["frames"]]
expected = ["63%", "2d11h", "41%", "4d11h"]
if texts != expected:
    raise SystemExit(f"unexpected frames: {texts!r}")
print(json.dumps({"health": health["status"], "texts": texts, "frames": len(texts)}))
PY
