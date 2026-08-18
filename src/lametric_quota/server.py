from __future__ import annotations

import hmac
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import unquote, urlsplit

from . import __version__
from .cache import QuotaCache
from .codexbar import CodexBarClient
from .frames import build_lametric_payload


PRIVACY_HTML = b"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Quota Privacy Policy</title>
<style>body{max-width:48rem;margin:3rem auto;padding:0 1rem;font:16px/1.6 system-ui;color:#18181b}h1,h2{line-height:1.2}</style>
</head><body><h1>AI Quota Privacy Policy</h1><p>Last updated: 18 August 2026.</p>
<p>AI Quota is a private, single-user LaMetric TIME integration. It displays weekly Codex and Claude Code quota remaining and reset countdowns.</p>
<h2>Data processed</h2><p>The service processes provider usage percentages, reset timestamps, and account authentication state. OAuth credentials are encrypted in transit and stored on a private persistent Railway volume so the provider command-line clients can refresh access.</p>
<h2>Data shared</h2><p>LaMetric receives only the four display frames: quota percentages, reset countdowns, and pixel icons. Railway hosts the service, while OpenAI and Anthropic supply the usage data. The app does not sell personal data and has no advertising or third-party analytics.</p>
<h2>Retention and control</h2><p>Usage values are cached in memory for up to five minutes. OAuth credentials remain until the app owner revokes access or deletes the service volume. Access can be revoked from the provider account settings at any time.</p>
<h2>Contact</h2><p>Contact the app owner through the LaMetric developer account that distributes this private app.</p>
</body></html>"""


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def make_handler(cache: QuotaCache, token: str) -> type[BaseHTTPRequestHandler]:
    expected_path = f"/v1/lametric/{token}"

    class Handler(BaseHTTPRequestHandler):
        server_version = "LaMetricAIQuota/" + __version__

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
            path = unquote(urlsplit(self.path).path)
            if path == "/health":
                self._send(HTTPStatus.OK, cache.health())
                return
            if path == "/privacy":
                self._send_bytes(HTTPStatus.OK, PRIVACY_HTML, "text/html; charset=utf-8")
                return
            if not hmac.compare_digest(path, expected_path):
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            quotas = cache.quotas()
            if len(quotas) != 2:
                self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "quota_not_ready"})
                return
            self._send(HTTPStatus.OK, build_lametric_payload(quotas))

        def _send(self, status: HTTPStatus, payload: Any) -> None:
            self._send_bytes(
                status,
                _json_bytes(payload),
                "application/json; charset=utf-8",
            )

        def _send_bytes(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
            self.send_response(status.value)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
            # Keep Railway logs useful without recording the secret URL path.
            print(
                json.dumps(
                    {
                        "event": "http",
                        "client": self.client_address[0],
                        "method": self.command,
                        "status": code,
                        "size": size,
                    }
                )
            )

        def log_message(self, fmt: str, *args: object) -> None:
            return

    return Handler


def main() -> None:
    token = os.environ.get("LAMETRIC_TOKEN", "")
    if len(token) < 24:
        raise SystemExit("LAMETRIC_TOKEN must contain at least 24 characters")
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    refresh_seconds = int(os.environ.get("REFRESH_INTERVAL", "300"))
    client = CodexBarClient()
    cache = QuotaCache(client.fetch, refresh_seconds=refresh_seconds)
    cache.start()
    server = ThreadingHTTPServer((host, port), make_handler(cache, token))
    print(json.dumps({"event": "started", "host": host, "port": port, "version": __version__}))
    try:
        server.serve_forever()
    finally:
        cache.stop()
        server.server_close()


if __name__ == "__main__":
    main()
