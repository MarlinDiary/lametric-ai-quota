from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path


ASSET_DIR = Path(__file__).resolve().parents[2] / "assets"
ICON_NAMES = frozenset({"codex", "claude"})


@lru_cache(maxsize=len(ICON_NAMES))
def icon_data_uri(name: str) -> str:
    if name not in ICON_NAMES:
        raise ValueError(f"unknown icon: {name}")
    encoded = base64.b64encode((ASSET_DIR / f"{name}.png").read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
