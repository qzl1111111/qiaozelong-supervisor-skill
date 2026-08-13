from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "qiaozelong-supervisor" / "scripts" / "route_specialists.py"
SPEC = importlib.util.spec_from_file_location("route_specialists", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def candidate(
    name: str,
    fit: float,
    expertise: float,
    capabilities: list[str],
    *,
    reviewer: bool = False,
    cost: float = 0.2,
    overlap: float = 0.1,
) -> dict:
    return {
        "name": name,
        "capabilities": capabilities,
        "task_fit": fit,
        "expertise": expertise,
        "reliability": 0.8,
        "evidence_access": 0.8,
        "availability": 1.0,
        "cost": cost,
        "overlap": overlap,
        "reviewer": reviewer,
        "score_basis": ["test fixture"],
    }


class RouterTests(unittest.TestCase):
    def test_simple_task_stays_with_supervisor(self) -> None:
        result = MODULE.route(
            {
                "task": "rename a heading",
                "complexity": 0.1,
                "risk": 0.1,
                "specialists": [candidate("writer", 0.9, 0.9, ["writing"])],
            }
        )
        self.assertEqual(result["mode"], "supervisor_only")
        self.assertEqual(result["activated"], [])

    def test_selects_smallest_team_that_covers_requirements(self) -> None:
        result = MODULE.route(
            {
                "task": "theory validation and report",
                "complexity": 0.8,
                "required_capabilities": ["theory", "reporting"],
                "max_active": 3,
                "budget": 0.8,
                "specialists": [
                    candidate("theory", 0.95, 0.95, ["theory"]),
                    candidate("reporter", 0.80, 0.85, ["reporting"]),
                    candidate("duplicate", 0.75, 0.80, ["theory"], overlap=0.9),
                    candidate("experiment", 0.20, 0.70, ["experiment"]),
                ],
            }
        )
        self.assertEqual(result["mode"], "delegated")
        self.assertEqual(result["covered_capabilities"], ["reporting", "theory"])
        self.assertEqual(result["uncovered_capabilities"], [])
        self.assertEqual({item["name"] for item in result["activated"]}, {"theory", "reporter"})
        self.assertAlmostEqual(sum(item["weight"] for item in result["activated"]), 1.0, places=5)

    def test_budget_blocks_unaffordable_agent(self) -> None:
        result = MODULE.route(
            {
                "task": "data and theory",
                "complexity": 0.9,
                "required_capabilities": ["data", "theory"],
                "budget": 0.4,
                "specialists": [
                    candidate("data", 0.95, 0.90, ["data"], cost=0.2),
                    candidate("theory", 0.90, 0.90, ["theory"], cost=0.5),
                ],
            }
        )
        self.assertIn("theory", result["uncovered_capabilities"])
        self.assertTrue(result["human_review_required"])
        reasons = {item["name"]: item["reason"] for item in result["standby"]}
        self.assertEqual(reasons["theory"], "budget_exceeded")

    def test_route_blocks_when_no_agent_is_affordable(self) -> None:
        result = MODULE.route(
            {
                "task": "expensive specialist task",
                "complexity": 0.9,
                "required_capabilities": ["theory"],
                "budget": 0.1,
                "specialists": [candidate("theory", 0.95, 0.95, ["theory"], cost=0.5)],
            }
        )
        self.assertEqual(result["mode"], "blocked")
        self.assertEqual(result["activated"], [])
        self.assertTrue(result["human_review_required"])

    def test_high_risk_adds_reviewer_when_budget_allows(self) -> None:
        result = MODULE.route(
            {
                "task": "high-risk decision",
                "complexity": 0.8,
                "risk": 0.9,
                "required_capabilities": ["analysis"],
                "budget": 0.6,
                "max_active": 2,
                "specialists": [
                    candidate("primary", 0.95, 0.95, ["analysis"], cost=0.2),
                    candidate("critic", 0.75, 0.85, ["review"], reviewer=True, cost=0.2),
                    candidate("irrelevant", 0.10, 0.90, ["other"], cost=0.2),
                ],
            }
        )
        self.assertTrue(result["human_review_required"])
        self.assertIn("critic", {item["name"] for item in result["activated"]})
        primary = next(item for item in result["activated"] if item["name"] == "primary")
        self.assertEqual(primary["score_basis"], ["test fixture"])

    def test_invalid_score_is_rejected(self) -> None:
        bad = candidate("bad", 1.2, 0.5, ["analysis"])
        with self.assertRaises(ValueError):
            MODULE.route({"task": "x", "complexity": 0.8, "specialists": [bad]})


if __name__ == "__main__":
    unittest.main()
