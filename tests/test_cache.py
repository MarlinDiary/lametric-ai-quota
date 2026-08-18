from __future__ import annotations

import unittest
from datetime import datetime, timezone

from lametric_quota.cache import QuotaCache
from lametric_quota.codexbar import ProviderQuota


NOW = datetime(2026, 8, 18, 12, tzinfo=timezone.utc)


def quota(provider: str) -> ProviderQuota:
    return ProviderQuota(provider, 50, NOW, NOW)


class CacheTests(unittest.TestCase):
    def test_retains_last_good_provider_during_partial_failure(self) -> None:
        failing = set()

        def fetch(provider: str) -> ProviderQuota:
            if provider in failing:
                raise RuntimeError("sensitive provider diagnostic")
            return quota(provider)

        cache = QuotaCache(fetch)
        cache.refresh()
        failing.add("claude")
        cache.refresh()

        self.assertEqual(set(cache.quotas()), {"codex", "claude"})
        health = cache.health()
        self.assertEqual(health["status"], "degraded")
        self.assertEqual(health["providers"]["claude"]["error"], "fetch_failed")
        self.assertNotIn("sensitive", str(health))


if __name__ == "__main__":
    unittest.main()
