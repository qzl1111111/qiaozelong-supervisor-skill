from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "qiaozelong-supervisor" / "scripts" / "route_specialists.py"
SPEC = importlib.util.spec_from_file_location("route_specialists", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def candidate(name: str, fit: float, expertise: float, *, reviewer: bool = False) -> dict:
    return {
        "name": name,
        "task_fit": fit,
        "expertise": expertise,
        "reliability": 0.8,
        "evidence_access": 0.8,
        "availability": 1.0,
        "cost": 0.3,
        "overlap": 0.1,
        "reviewer": reviewer,
    }


class RouterTests(unittest.TestCase):
    def test_sparse_selection_does_not_activate_every_agent(self) -> None:
        result = MODULE.route(
            {
                "task": "theory validation",
                "stage": "theory",
                "risk": 0.2,
                "threshold": 0.55,
                "max_active": 2,
                "specialists": [
                    candidate("theory", 0.95, 0.95),
                    candidate("data", 0.70, 0.80),
                    candidate("experiment", 0.20, 0.70),
                    candidate("reporting", 0.10, 0.60),
                ],
            }
        )
        self.assertEqual(result["primary"], "theory")
        self.assertLessEqual(len(result["activated"]), 2)
        self.assertGreater(len(result["standby"]), 0)
        self.assertAlmostEqual(sum(item["weight"] for item in result["activated"]), 1.0, places=5)

    def test_high_risk_can_activate_reviewer(self) -> None:
        result = MODULE.route(
            {
                "task": "high-risk decision",
                "risk": 0.9,
                "threshold": 0.55,
                "max_active": 2,
                "specialists": [
                    candidate("primary", 0.95, 0.95),
                    candidate("critic", 0.75, 0.85, reviewer=True),
                    candidate("irrelevant", 0.10, 0.90),
                ],
            }
        )
        self.assertTrue(result["human_review_required"])
        self.assertIn("critic", {item["name"] for item in result["activated"]})


if __name__ == "__main__":
    unittest.main()
