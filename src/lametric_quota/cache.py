from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Callable

from .codexbar import ProviderQuota, SUPPORTED_PROVIDERS


FetchQuota = Callable[[str], ProviderQuota]


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if value else None


class QuotaCache:
    def __init__(self, fetch: FetchQuota, refresh_seconds: int = 300) -> None:
        self._fetch = fetch
        self.refresh_seconds = refresh_seconds
        self._lock = threading.Lock()
        self._refresh_lock = threading.Lock()
        self._quotas: dict[str, ProviderQuota] = {}
        self._errors: dict[str, str] = {}
        self._last_attempt: datetime | None = None
        self._last_complete_success: datetime | None = None
        self._stop = threading.Event()

    def refresh(self) -> None:
        if not self._refresh_lock.acquire(blocking=False):
            return
        try:
            attempted_at = datetime.now(timezone.utc)
            results: dict[str, ProviderQuota] = {}
            errors: dict[str, str] = {}
            with ThreadPoolExecutor(max_workers=len(SUPPORTED_PROVIDERS)) as pool:
                futures = {pool.submit(self._fetch, provider): provider for provider in SUPPORTED_PROVIDERS}
                for future in as_completed(futures):
                    provider = futures[future]
                    try:
                        results[provider] = future.result()
                    except Exception as exc:  # surfaced through health without credentials
                        errors[provider] = str(exc)[:500]
            with self._lock:
                self._quotas.update(results)
                self._errors = errors
                self._last_attempt = attempted_at
                if all(provider in results for provider in SUPPORTED_PROVIDERS):
                    self._last_complete_success = attempted_at
        finally:
            self._refresh_lock.release()

    def quotas(self) -> dict[str, ProviderQuota]:
        with self._lock:
            ready = all(provider in self._quotas for provider in SUPPORTED_PROVIDERS)
        if not ready:
            self.refresh()
        with self._lock:
            return dict(self._quotas)

    def health(self) -> dict[str, object]:
        with self._lock:
            ready = all(provider in self._quotas for provider in SUPPORTED_PROVIDERS)
            if not ready:
                status = "starting"
            elif self._errors:
                status = "degraded"
            else:
                status = "ok"
            providers = {
                provider: {
                    "available": provider in self._quotas,
                    "error": "fetch_failed" if provider in self._errors else None,
                    "updatedAt": _iso(
                        self._quotas.get(provider).updated_at if provider in self._quotas else None
                    ),
                }
                for provider in SUPPORTED_PROVIDERS
            }
            return {
                "status": status,
                "ready": ready,
                "lastAttemptAt": _iso(self._last_attempt),
                "lastCompleteSuccessAt": _iso(self._last_complete_success),
                "refreshSeconds": self.refresh_seconds,
                "providers": providers,
            }

    def start(self) -> threading.Thread:
        def loop() -> None:
            self.refresh()
            while not self._stop.wait(self.refresh_seconds):
                self.refresh()

        thread = threading.Thread(target=loop, name="quota-refresh", daemon=True)
        thread.start()
        return thread

    def stop(self) -> None:
        self._stop.set()
