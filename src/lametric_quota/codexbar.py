from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


SUPPORTED_PROVIDERS = ("codex", "claude")


@dataclass(frozen=True)
class ProviderQuota:
    provider: str
    remaining_percent: float
    reset_at: datetime
    updated_at: datetime | None


def parse_timestamp(value: Any) -> datetime:
    """Parse CodexBar's ISO-8601 or Foundation epoch timestamp."""
    if isinstance(value, bool):
        raise ValueError("timestamp must not be a boolean")
    if isinstance(value, (int, float)):
        seconds = float(value)
        if abs(seconds) >= 1_000_000_000_000:
            seconds /= 1000
        return datetime.fromtimestamp(seconds, tz=timezone.utc)
    if isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    raise ValueError(f"unsupported timestamp: {value!r}")


def _provider_payload(payload: Any, provider: str) -> Mapping[str, Any]:
    candidates: Sequence[Any]
    if isinstance(payload, list):
        candidates = payload
    else:
        candidates = [payload]
    for candidate in candidates:
        if isinstance(candidate, Mapping) and candidate.get("provider") == provider:
            return candidate
    raise ValueError(f"CodexBar payload has no {provider!r} provider")


def _weekly_window(usage: Mapping[str, Any]) -> Mapping[str, Any]:
    secondary = usage.get("secondary")
    if isinstance(secondary, Mapping):
        return secondary

    # Forward-compatible fallback if CodexBar moves to named windows.
    for named in usage.get("extraRateWindows") or []:
        if not isinstance(named, Mapping):
            continue
        window_id = str(named.get("id", "")).lower()
        title = str(named.get("title", "")).lower()
        window = named.get("window")
        if "week" in window_id or "week" in title:
            if isinstance(window, Mapping):
                return window
    raise ValueError("CodexBar payload has no weekly window")


def parse_provider_quota(payload: Any, provider: str) -> ProviderQuota:
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"unsupported provider: {provider}")
    item = _provider_payload(payload, provider)
    error = item.get("error")
    if error:
        raise ValueError(f"CodexBar {provider} error: {error}")
    usage = item.get("usage")
    if not isinstance(usage, Mapping):
        raise ValueError(f"CodexBar {provider} payload has no usage")
    weekly = _weekly_window(usage)
    used = weekly.get("usedPercent")
    if isinstance(used, bool) or not isinstance(used, (int, float)):
        raise ValueError(f"CodexBar {provider} weekly usedPercent is missing")
    reset_value = weekly.get("resetsAt")
    if reset_value is None:
        raise ValueError(f"CodexBar {provider} weekly reset is missing")
    updated_value = usage.get("updatedAt")
    return ProviderQuota(
        provider=provider,
        remaining_percent=max(0.0, min(100.0, 100.0 - float(used))),
        reset_at=parse_timestamp(reset_value),
        updated_at=parse_timestamp(updated_value) if updated_value is not None else None,
    )


class CodexBarClient:
    def __init__(
        self,
        binary: str | None = None,
        timeout_seconds: int | None = None,
        sources: Mapping[str, str] | None = None,
    ) -> None:
        self.binary = binary or os.environ.get("CODEXBAR_BINARY", "codexbar")
        self.timeout_seconds = timeout_seconds or int(
            os.environ.get("CODEXBAR_TIMEOUT_SECONDS", "60")
        )
        self.sources = dict(
            sources
            or {
                "codex": os.environ.get("CODEXBAR_CODEX_SOURCE", "oauth"),
                "claude": os.environ.get("CODEXBAR_CLAUDE_SOURCE", "oauth"),
            }
        )

    def fetch(self, provider: str) -> ProviderQuota:
        source = self.sources.get(provider, "oauth")
        command = [
            self.binary,
            "usage",
            "--provider",
            provider,
            "--source",
            source,
            "--format",
            "json",
            "--json-only",
        ]
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "no output"
            raise RuntimeError(
                f"CodexBar {provider} exited {completed.returncode}: {detail[:500]}"
            )
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"CodexBar {provider} returned invalid JSON") from exc
        return parse_provider_quota(payload, provider)
