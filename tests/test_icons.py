from __future__ import annotations

import struct
import unittest
from pathlib import Path

from lametric_quota.icons import icon_data_uri


ASSETS = Path(__file__).parents[1] / "assets"


class IconTests(unittest.TestCase):
    def test_every_icon_is_an_exact_8_by_8_png(self) -> None:
        for name in ("codex", "codex-reset", "claude", "claude-reset"):
            data = (ASSETS / f"{name}.png").read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            width, height = struct.unpack(">II", data[16:24])
            self.assertEqual((width, height), (8, 8))
            self.assertTrue(icon_data_uri(name).startswith("data:image/png;base64,"))


if __name__ == "__main__":
    unittest.main()
