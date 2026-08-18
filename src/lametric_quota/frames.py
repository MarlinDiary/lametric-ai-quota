from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Callable, Mapping

from .codexbar import ProviderQuota
from .icons import icon_data_uri


PROVIDER_ORDER = ("codex", "claude")


def format_countdown(reset_at: datetime, now: datetime | None = None) -> str:
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    if reset_at.tzinfo is None:
        reset_at = reset_at.replace(tzinfo=timezone.utc)
    seconds = max(0, math.ceil((reset_at - reference).total_seconds()))
    total_minutes = math.ceil(seconds / 60)
    days, remainder = divmod(total_minutes, 24 * 60)
    hours, minutes = divmod(remainder, 60)
    if days:
        return f"{days}d{hours:02d}h"
    if hours:
        return f"{hours}h{minutes:02d}m"
    return f"{minutes}m"


def _rounded_percent(value: float) -> int:
    return int(math.floor(max(0.0, min(100.0, value)) + 0.5))


def build_lametric_payload(
    quotas: Mapping[str, ProviderQuota],
    *,
    now: datetime | None = None,
    icon_loader: Callable[[str], str] = icon_data_uri,
) -> dict[str, list[dict[str, str]]]:
    reference = now or datetime.now(timezone.utc)
    frames: list[dict[str, str]] = []
    for provider in PROVIDER_ORDER:
        quota = quotas.get(provider)
        if quota is None:
            raise ValueError(f"missing quota for {provider}")
        frames.extend(
            [
                {
                    "icon": icon_loader(provider),
                    "text": f"{_rounded_percent(quota.remaining_percent)}%",
                },
                {
                    "icon": icon_loader(provider),
                    "text": format_countdown(quota.reset_at, reference),
                },
            ]
        )
    return {"frames": frames}
