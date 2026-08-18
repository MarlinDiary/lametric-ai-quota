from __future__ import annotations

import struct
import unittest
import zlib
from pathlib import Path

from lametric_quota.icons import icon_data_uri


ASSETS = Path(__file__).parents[1] / "assets"


class IconTests(unittest.TestCase):
    def test_exactly_two_icons_are_exact_8_by_8_pngs(self) -> None:
        self.assertEqual(
            {path.name for path in ASSETS.glob("*.png")},
            {"codex.png", "claude.png"},
        )
        for name in ("codex", "claude"):
            data = (ASSETS / f"{name}.png").read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            width, height = struct.unpack(">II", data[16:24])
            self.assertEqual((width, height), (8, 8))
            self.assertTrue(icon_data_uri(name).startswith("data:image/png;base64,"))

    def test_icons_use_only_the_requested_opaque_color(self) -> None:
        expected = {
            "codex": {(255, 255, 255, 255)},
            "claude": {(217, 119, 87, 255)},
        }
        for name, expected_colors in expected.items():
            data = (ASSETS / f"{name}.png").read_bytes()
            offset = 8
            idat = bytearray()
            while offset < len(data):
                length = struct.unpack(">I", data[offset : offset + 4])[0]
                kind = data[offset + 4 : offset + 8]
                payload = data[offset + 8 : offset + 8 + length]
                if kind == b"IDAT":
                    idat.extend(payload)
                offset += 12 + length
            raw = zlib.decompress(bytes(idat))
            pixels = []
            for row in range(8):
                scanline = raw[row * 33 : (row + 1) * 33]
                self.assertEqual(scanline[0], 0)
                pixels.extend(
                    tuple(scanline[index : index + 4])
                    for index in range(1, 33, 4)
                )
            self.assertEqual({pixel for pixel in pixels if pixel[3]}, expected_colors)


if __name__ == "__main__":
    unittest.main()
