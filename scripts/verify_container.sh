#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
name="lametric-ai-quota-verify-$$"
token=container-verification-token-1234567890

docker run --rm -d --name "$name" \
  -p 127.0.0.1::8080 \
  -e LAMETRIC_TOKEN="$token" \
  -e CODEXBAR_BINARY=/app/tests/fixture_codexbar.py \
  -e REFRESH_INTERVAL=3600 \
  -v "$ROOT/tests:/app/tests:ro" \
  -v "$ROOT/fixtures:/app/fixtures:ro" \
  lametric-ai-quota:local >/dev/null

cleanup() {
  docker stop "$name" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

mapping=$(docker port "$name" 8080/tcp)
port=${mapping##*:}
for _ in $(seq 1 50); do
  if curl -fsS "http://127.0.0.1:$port/health" > /tmp/lametric-health.json 2>/dev/null; then
    ready=$(python3 -c 'import json; print(str(json.load(open("/tmp/lametric-health.json"))["ready"]).lower())')
    [ "$ready" = true ] && break
  fi
  sleep 0.2
done

echo '-- versions --'
docker exec "$name" sh -lc 'codexbar --version; codex --version; claude --version'
echo '-- health --'
python3 - <<'PY'
import json
payload = json.load(open("/tmp/lametric-health.json"))
print(json.dumps({"status": payload["status"], "ready": payload["ready"]}, separators=(",", ":")))
PY
echo '-- frames --'
curl -fsS "http://127.0.0.1:$port/v1/lametric/$token" | python3 -c '
import json, sys
p = json.load(sys.stdin)
print(json.dumps({
    "texts": [f["text"] for f in p["frames"]],
    "icons_are_png": [f["icon"].startswith("data:image/png;base64,") for f in p["frames"]],
}, separators=(",", ":")))
'
echo '-- token absent from logs --'
if docker logs "$name" 2>&1 | grep -F "$token" >/dev/null; then
  echo TOKEN_LEAKED
  exit 1
fi
echo TOKEN_NOT_LOGGED
