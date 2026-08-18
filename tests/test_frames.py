from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from lametric_quota.codexbar import parse_provider_quota
from lametric_quota.frames import build_lametric_payload, format_countdown


FIXTURE = Path(__file__).parents[1] / "fixtures" / "codexbar-usage.json"


class FrameTests(unittest.TestCase):
    def test_exact_four_frame_two_icon_contract(self) -> None:
        raw = json.loads(FIXTURE.read_text())
        quotas = {
            provider: parse_provider_quota(raw, provider)
            for provider in ("codex", "claude")
        }
        payload = build_lametric_payload(
            quotas,
            now=datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc),
            icon_loader=lambda name: f"data:image/png;base64,{name}",
        )

        self.assertEqual(
            payload,
            {
                "frames": [
                    {
                        "icon": "data:image/png;base64,codex",
                        "text": "63%",
                        "duration": 5000,
                    },
                    {
                        "icon": "data:image/png;base64,codex",
                        "text": "2d11h",
                        "duration": 5000,
                    },
                    {
                        "icon": "data:image/png;base64,claude",
                        "text": "41%",
                        "duration": 5000,
                    },
                    {
                        "icon": "data:image/png;base64,claude",
                        "text": "4d11h",
                        "duration": 5000,
                    },
                ]
            },
        )

    def test_countdown_switches_to_hours_and_minutes(self) -> None:
        now = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(
            format_countdown(datetime(2026, 8, 18, 23, 42, tzinfo=timezone.utc), now),
            "11h42m",
        )
        self.assertEqual(
            format_countdown(datetime(2026, 8, 18, 12, 42, tzinfo=timezone.utc), now),
            "42m",
        )


if __name__ == "__main__":
    unittest.main()
