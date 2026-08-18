#!/usr/bin/env python3
from __future__ import annotations

import binascii
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).parents[1]
ASSETS = ROOT / "assets"

PALETTE = {
    ".": (0, 0, 0, 0),
    "W": (255, 255, 255, 255),
    "O": (217, 119, 87, 255),
}

PATTERNS = {
    "codex": [
        "WWWWWWWW",
        "W......W",
        "W.W....W",
        "W..W...W",
        "W.W....W",
        "W...WW.W",
        "W......W",
        "WWWWWWWW",
    ],
    "claude": [
        "..OOOOO.",
        ".OO.....",
        ".O......",
        ".O......",
        ".O......",
        ".O......",
        ".OO.....",
        "..OOOOO.",
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
    for stale_name in ("codex-reset", "claude-reset"):
        (ASSETS / f"{stale_name}.png").unlink(missing_ok=True)
    for name, pattern in PATTERNS.items():
        (ASSETS / f"{name}.png").write_bytes(png(pattern))


if __name__ == "__main__":
    main()
