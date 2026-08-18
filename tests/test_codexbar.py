from __future__ import annotations

import json
import unittest
from pathlib import Path

from lametric_quota.codexbar import parse_provider_quota


FIXTURE = Path(__file__).parents[1] / "fixtures" / "codexbar-usage.json"


class CodexBarParsingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads(FIXTURE.read_text())

    def test_extracts_weekly_remaining_and_reset_from_array(self) -> None:
        codex = parse_provider_quota(self.payload, "codex")
        claude = parse_provider_quota(self.payload, "claude")

        self.assertEqual(codex.remaining_percent, 63)
        self.assertEqual(codex.reset_at.isoformat(), "2026-08-20T23:00:00+00:00")
        self.assertEqual(claude.remaining_percent, 41)
        self.assertEqual(claude.reset_at.isoformat(), "2026-08-22T23:00:00+00:00")

    def test_accepts_single_provider_object(self) -> None:
        quota = parse_provider_quota(self.payload[0], "codex")
        self.assertEqual(quota.provider, "codex")

    def test_rejects_missing_weekly_window(self) -> None:
        payload = {"provider": "codex", "usage": {"primary": {"usedPercent": 2}}}
        with self.assertRaisesRegex(ValueError, "weekly"):
            parse_provider_quota(payload, "codex")


if __name__ == "__main__":
    unittest.main()
