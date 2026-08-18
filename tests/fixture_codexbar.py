#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


provider = sys.argv[sys.argv.index("--provider") + 1]
payload = json.loads((Path(__file__).parents[1] / "fixtures" / "codexbar-usage.json").read_text())
offsets = {"codex": timedelta(days=2, hours=11), "claude": timedelta(days=4, hours=11)}
for item in payload:
    if item["provider"] == provider:
        item["usage"]["secondary"]["resetsAt"] = (
            datetime.now(timezone.utc) + offsets[provider]
        ).isoformat()
print(json.dumps([item for item in payload if item["provider"] == provider]))
