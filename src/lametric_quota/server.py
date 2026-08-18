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
            if not hmac.compare_digest(path, expected_path):
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            quotas = cache.quotas()
            if len(quotas) != 2:
                self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "quota_not_ready"})
                return
            self._send(HTTPStatus.OK, build_lametric_payload(quotas))

        def _send(self, status: HTTPStatus, payload: Any) -> None:
            body = _json_bytes(payload)
            self.send_response(status.value)
            self.send_header("Content-Type", "application/json; charset=utf-8")
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
