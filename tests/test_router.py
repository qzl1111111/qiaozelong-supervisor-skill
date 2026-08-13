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

REGISTRY_SCRIPT = Path(__file__).parents[1] / "skills" / "qiaozelong-supervisor" / "scripts" / "capability_registry.py"
REGISTRY_SPEC = importlib.util.spec_from_file_location("capability_registry", REGISTRY_SCRIPT)
REGISTRY_MODULE = importlib.util.module_from_spec(REGISTRY_SPEC)
assert REGISTRY_SPEC and REGISTRY_SPEC.loader
REGISTRY_SPEC.loader.exec_module(REGISTRY_MODULE)


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


def registry_fixture() -> dict:
    return {
        "schema_version": "1.0",
        "specialists": [
            {
                "name": "theory-agent",
                "capabilities": ["theory", "simulation"],
                "domains": ["materials"],
                "tools": ["python"],
                "limitations": ["no lab control"],
                "availability": 1.0,
                "cost": 0.2,
                "evidence_access": 0.8,
                "last_verified": "2026-08-13",
                "benchmarks": [
                    {"capability": "theory", "score": 0.9, "sample_size": 25, "source": "bench-25"}
                ],
                "history": {"completed": 8, "successful": 6},
            },
            {
                "name": "writer",
                "capabilities": ["reporting"],
                "domains": ["communications"],
                "tools": ["editor"],
                "limitations": [],
                "availability": 0.8,
                "cost": 0.15,
                "evidence_access": 0.6,
                "benchmarks": [],
                "history": {"completed": 0, "successful": 0},
            },
        ],
    }


class CapabilityRegistryTests(unittest.TestCase):
    def test_derives_scores_from_matching_evidence(self) -> None:
        candidates = REGISTRY_MODULE.derive_specialists(
            {
                "required_capabilities": ["theory"],
                "relevant_domains": ["materials"],
                "required_tools": ["python"],
            },
            registry_fixture(),
        )
        theory = next(item for item in candidates if item["name"] == "theory-agent")
        writer = next(item for item in candidates if item["name"] == "writer")
        self.assertEqual(theory["task_fit"], 1.0)
        self.assertEqual(theory["expertise"], 0.9)
        self.assertAlmostEqual(theory["reliability"], 8 / 12, places=6)
        self.assertEqual(writer["expertise"], 0.35)
        self.assertGreater(theory["task_fit"], writer["task_fit"])

    def test_registry_backed_route_is_auditable(self) -> None:
        request = REGISTRY_MODULE.enrich_request(
            {
                "task": "validate theory",
                "complexity": 0.8,
                "required_capabilities": ["theory"],
                "relevant_domains": ["materials"],
                "required_tools": ["python"],
            },
            registry_fixture(),
        )
        result = MODULE.route(request)
        self.assertEqual(result["scoring_source"], "capability_registry_v1")
        self.assertEqual(result["primary"], "theory-agent")
        self.assertIn("bench-25", " ".join(result["activated"][0]["score_basis"]))

    def test_invalid_benchmark_provenance_is_rejected(self) -> None:
        registry = registry_fixture()
        registry["specialists"][0]["benchmarks"][0]["source"] = ""
        with self.assertRaises(ValueError):
            REGISTRY_MODULE.validate_registry(registry)

    def test_registry_mode_rejects_manual_specialists(self) -> None:
        with self.assertRaises(ValueError):
            REGISTRY_MODULE.enrich_request({"specialists": [candidate("x", 0.5, 0.5, ["x"])]}, registry_fixture())


if __name__ == "__main__":
    unittest.main()
