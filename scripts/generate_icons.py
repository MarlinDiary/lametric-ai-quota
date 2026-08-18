#!/usr/bin/env python3
from __future__ import annotations

import binascii
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).parents[1]
ASSETS = ROOT / "assets"

PALETTE = {
    "B": (10, 15, 20, 255),
    "T": (63, 224, 181, 255),
    "W": (244, 248, 250, 255),
    "D": (42, 20, 12, 255),
    "O": (217, 119, 87, 255),
    "C": (126, 211, 255, 255),
}

PATTERNS = {
    "codex": [
        "BBTTTBBB",
        "BTTBTTBB",
        "TTBBBTTB",
        "TBTWTBTB",
        "TBTWTBTB",
        "BTTBBBTT",
        "BBTTBTTB",
        "BBBTTTBB",
    ],
    "codex-reset": [
        "BBTTTBBB",
        "BTTBTTBB",
        "TTBBBTTB",
        "TBTWTBTB",
        "TBTWCCCC",
        "BTTBCBBC",
        "BBTTCWBC",
        "BBBCCCCC",
    ],
    "claude": [
        "DDDOODDD",
        "DODOODOD",
        "DDOOOODD",
        "OOOOOOOO",
        "OOOOOOOO",
        "DDOOOODD",
        "DODOODOD",
        "DDDOODDD",
    ],
    "claude-reset": [
        "DDDOODDD",
        "DODOODOD",
        "DDOOOODD",
        "OOOOOOOO",
        "OOOOWWWW",
        "DDOOWDDW",
        "DODOOWDW",
        "DDDWWWWW",
    ],
}


def chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", binascii.crc32(kind + data))


def png(pattern: list[str]) -> bytes:
    assert len(pattern) == 8 and all(len(row) == 8 for row in pattern)
    raw = b"".join(
        b"\x00" + b"".join(bytes(PALETTE[pixel]) for pixel in row)
        for row in pattern
    )
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, level=9))
        + chunk(b"IEND", b"")
    )


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for name, pattern in PATTERNS.items():
        (ASSETS / f"{name}.png").write_bytes(png(pattern))


if __name__ == "__main__":
    main()
