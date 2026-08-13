from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "qiaozelong-supervisor" / "scripts" / "route_specialists.py"
SPEC = importlib.util.spec_from_file_location("route_specialists", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

INSTALL_SCRIPT = Path(__file__).parents[1] / "skills" / "qiaozelong-supervisor" / "scripts" / "install_skill.py"
INSTALL_SPEC = importlib.util.spec_from_file_location("install_skill", INSTALL_SCRIPT)
INSTALL_MODULE = importlib.util.module_from_spec(INSTALL_SPEC)
assert INSTALL_SPEC and INSTALL_SPEC.loader
INSTALL_SPEC.loader.exec_module(INSTALL_MODULE)


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

    def test_primary_weight_remains_strictly_highest(self) -> None:
        result = MODULE.route(
            {
                "task": "analysis with a stronger critic",
                "complexity": 0.8,
                "risk": 0.9,
                "required_capabilities": ["analysis"],
                "budget": 0.6,
                "max_active": 2,
                "specialists": [
                    candidate("primary", 0.70, 0.70, ["analysis"], cost=0.2),
                    candidate("critic", 1.0, 1.0, ["review"], reviewer=True, cost=0.2, overlap=0.0),
                ],
            }
        )
        primary_weight = result["activated"][0]["weight"]
        self.assertTrue(all(primary_weight > item["weight"] for item in result["activated"][1:]))

    def test_invalid_score_is_rejected(self) -> None:
        bad = candidate("bad", 1.2, 0.5, ["analysis"])
        with self.assertRaises(ValueError):
            MODULE.route({"task": "x", "complexity": 0.8, "specialists": [bad]})


class InstallerTests(unittest.TestCase):
    def test_auto_detects_cli_and_configuration_roots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            (home / ".hermes").mkdir()

            def fake_which(command: str) -> str | None:
                return "C:/tools/claude.exe" if command == "claude" else None

            self.assertEqual(INSTALL_MODULE.detect_targets(home, fake_which), ["claude", "hermes"])

    def test_install_all_and_protect_existing_copies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir) / "home"
            source = Path(temp_dir) / "source"
            source.mkdir()
            (source / "SKILL.md").write_text("---\nname: test\n---\n", encoding="utf-8")

            results = INSTALL_MODULE.install(["all"], home, source)
            self.assertTrue(all(item["status"] == "installed" for item in results.values()))
            for relative_path in INSTALL_MODULE.TARGETS.values():
                self.assertTrue((home / relative_path / "SKILL.md").is_file())

            second_results = INSTALL_MODULE.install(["all"], home, source)
            self.assertTrue(all(item["status"] == "exists" for item in second_results.values()))

    def test_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir) / "home"
            source = Path(temp_dir) / "source"
            source.mkdir()
            results = INSTALL_MODULE.install(["all"], home, source, dry_run=True)
            self.assertTrue(all(item["status"] == "would_install" for item in results.values()))
            self.assertFalse(home.exists())


if __name__ == "__main__":
    unittest.main()
