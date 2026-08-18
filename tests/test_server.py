from __future__ import annotations

import io
import json
import threading
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen

from lametric_quota.cache import QuotaCache
from lametric_quota.codexbar import ProviderQuota
from lametric_quota.server import make_handler


TOKEN = "test-token-with-at-least-24-characters"


def fetch(provider: str) -> ProviderQuota:
    now = datetime.now(timezone.utc)
    return ProviderQuota(provider, 50, now + timedelta(days=2), now)


class ServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cache = QuotaCache(fetch)
        self.cache.refresh()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.cache, TOKEN))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_health_is_public_and_redacted(self) -> None:
        with urlopen(f"{self.base}/health") as response:
            payload = json.load(response)
        self.assertTrue(payload["ready"])
        self.assertEqual(payload["status"], "ok")

    def test_secret_path_returns_four_frames_without_logging_token(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            with urlopen(f"{self.base}/v1/lametric/{TOKEN}") as response:
                payload = json.load(response)
        self.assertEqual(len(payload["frames"]), 4)
        self.assertNotIn(TOKEN, output.getvalue())

    def test_wrong_path_is_hidden_as_404(self) -> None:
        with self.assertRaises(HTTPError) as raised:
            urlopen(f"{self.base}/v1/lametric/wrong")
        self.assertEqual(raised.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
