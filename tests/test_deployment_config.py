from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class DeploymentConfigTests(unittest.TestCase):
    def test_dockerfile_leaves_data_volume_to_railway(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text()
        instructions = [
            line.strip().split(maxsplit=1)[0].upper()
            for line in dockerfile.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertNotIn("VOLUME", instructions)


if __name__ == "__main__":
    unittest.main()
