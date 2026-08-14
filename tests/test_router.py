from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "skills" / "sparse-supervisor" / "scripts" / "route_specialists.py"
SPEC = importlib.util.spec_from_file_location("route_specialists", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

INSTALL_SCRIPT = Path(__file__).parents[1] / "skills" / "sparse-supervisor" / "scripts" / "install_skill.py"
INSTALL_SPEC = importlib.util.spec_from_file_location("install_skill", INSTALL_SCRIPT)
INSTALL_MODULE = importlib.util.module_from_spec(INSTALL_SPEC)
assert INSTALL_SPEC and INSTALL_SPEC.loader
INSTALL_SPEC.loader.exec_module(INSTALL_MODULE)

REGISTRY_SCRIPT = Path(__file__).parents[1] / "skills" / "sparse-supervisor" / "scripts" / "capability_registry.py"
REGISTRY_SPEC = importlib.util.spec_from_file_location("capability_registry", REGISTRY_SCRIPT)
REGISTRY_MODULE = importlib.util.module_from_spec(REGISTRY_SPEC)
assert REGISTRY_SPEC and REGISTRY_SPEC.loader
REGISTRY_SPEC.loader.exec_module(REGISTRY_MODULE)

KNOWLEDGE_SCRIPT = Path(__file__).parents[1] / "skills" / "sparse-supervisor" / "scripts" / "validate_knowledge_base.py"
KNOWLEDGE_SPEC = importlib.util.spec_from_file_location("validate_knowledge_base", KNOWLEDGE_SCRIPT)
KNOWLEDGE_MODULE = importlib.util.module_from_spec(KNOWLEDGE_SPEC)
assert KNOWLEDGE_SPEC and KNOWLEDGE_SPEC.loader
KNOWLEDGE_SPEC.loader.exec_module(KNOWLEDGE_MODULE)

TUTORIAL_SCRIPT = Path(__file__).parents[1] / "skills" / "sparse-supervisor" / "scripts" / "validate_tutorial_package.py"
TUTORIAL_SPEC = importlib.util.spec_from_file_location("validate_tutorial_package", TUTORIAL_SCRIPT)
TUTORIAL_MODULE = importlib.util.module_from_spec(TUTORIAL_SPEC)
assert TUTORIAL_SPEC and TUTORIAL_SPEC.loader
TUTORIAL_SPEC.loader.exec_module(TUTORIAL_MODULE)

INIT_TUTORIAL_SCRIPT = Path(__file__).parents[1] / "skills" / "sparse-supervisor" / "scripts" / "init_tutorial_package.py"
INIT_TUTORIAL_SPEC = importlib.util.spec_from_file_location("init_tutorial_package", INIT_TUTORIAL_SCRIPT)
INIT_TUTORIAL_MODULE = importlib.util.module_from_spec(INIT_TUTORIAL_SPEC)
assert INIT_TUTORIAL_SPEC and INIT_TUTORIAL_SPEC.loader
INIT_TUTORIAL_SPEC.loader.exec_module(INIT_TUTORIAL_MODULE)

PUBLICATION_SCRIPT = Path(__file__).parents[1] / "skills" / "sparse-supervisor" / "scripts" / "check_publication_safety.py"
PUBLICATION_SPEC = importlib.util.spec_from_file_location("check_publication_safety", PUBLICATION_SCRIPT)
PUBLICATION_MODULE = importlib.util.module_from_spec(PUBLICATION_SPEC)
assert PUBLICATION_SPEC and PUBLICATION_SPEC.loader
PUBLICATION_SPEC.loader.exec_module(PUBLICATION_MODULE)


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


KNOWLEDGE_TEXT = """# Expert knowledge

## Scope
Theory review only.
## Core knowledge
- Testable statement. [S1]
## Decision rules
1. Check evidence. [S1]
## Workflow
1. Inspect inputs.
## Evidence standards
Prefer primary evidence.
## Known limitations
No laboratory control.
## Escalation triggers
Conflicting safety evidence.
## Terminology
- Theory: explanatory model.
"""


def write_knowledge_expert(root: Path, *, source_id: str = "S1") -> Path:
    directory = root / "theory-expert"
    directory.mkdir(parents=True)
    manifest = {
        "schema_version": "1.0",
        "expert_id": "theory-expert",
        "display_name": "Theory Expert",
        "summary": "Reviews theoretical evidence.",
        "domains": ["materials"],
        "capabilities": ["theory"],
        "knowledge_files": ["knowledge.md"],
        "languages": ["en"],
        "updated_at": "2026-08-14",
        "review_after": "2027-02-14",
        "limitations": ["No lab control"],
        "escalation_triggers": ["Safety conflict"],
        "sources": [
            {
                "id": source_id,
                "title": "Primary report",
                "type": "paper",
                "locator": "https://doi.org/example",
                "published_at": "2025-01-01",
                "accessed_at": "2026-08-14",
                "authority": "primary",
            }
        ],
    }
    (directory / "expert.json").write_text(json.dumps(manifest), encoding="utf-8")
    (directory / "knowledge.md").write_text(KNOWLEDGE_TEXT, encoding="utf-8")
    return directory


class KnowledgeBaseTests(unittest.TestCase):
    def test_valid_expert_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_knowledge_expert(root)
            result = KNOWLEDGE_MODULE.validate_knowledge_base(root)
            self.assertEqual(result[0]["expert_id"], "theory-expert")

    def test_directory_must_match_expert_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            directory = write_knowledge_expert(root)
            manifest_path = directory / "expert.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["expert_id"] = "different-id"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(ValueError):
                KNOWLEDGE_MODULE.validate_knowledge_base(root)

    def test_unknown_source_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_knowledge_expert(root, source_id="S2")
            with self.assertRaises(ValueError):
                KNOWLEDGE_MODULE.validate_knowledge_base(root)


OVERVIEW_TEXT = """# Course overview

## Scope and audience
Scientists.
## Source coverage
One source.
## Topic hierarchy
Crystallography.
## Prerequisites
Geometry.
## Key knowledge units
- Definition (`ku_crystal-course_000001`).
## Formulas, units, and conventions
State conventions.
## Limitations and unresolved questions
None.
## Candidate expert mappings
Materials theory.
"""


def write_tutorial_package(root: Path, *, evidence_source: str | None = None) -> Path:
    package_id = "crystal-course"
    package = root / package_id
    for relative in ("units", "summaries", "mappings", "merge", "qa"):
        (package / relative).mkdir(parents=True, exist_ok=True)
    sha = "a" * 64
    source_id = f"src_{sha[:16]}"
    manifest = {
        "schema_version": "1.1", "package_id": package_id, "title": "Crystal course",
        "version": "1.0.0", "status": "review", "languages": ["zh-CN"],
        "created_at": "2026-08-14", "updated_at": "2026-08-14",
        "description": "Course package", "scope": ["crystallography"],
        "unit_shard_max_bytes": 5_242_880, "unit_shard_max_records": 500,
        "publication": {
            "distribution": "local-only", "source_metadata_visibility": "private",
            "contains_original_files": False, "upload_requires_explicit_user_approval": True,
        },
    }
    inventory = {
        "source_id": source_id, "relative_path": "course.pdf", "sha256": sha,
        "size_bytes": 100, "media_type": "application/pdf", "source_role": "primary-tutorial",
        "extraction_status": "complete", "extracted_artifacts": [], "warnings": [],
    }
    unit_id = "ku_crystal-course_000001"
    unit = {
        "schema_version": "1.0", "unit_id": unit_id, "package_id": package_id,
        "title": "Unit cell", "domain_path": ["crystallography"], "knowledge_type": "concept",
        "summary": "A reusable definition.",
        "claims": [{"claim_id": "C1", "text": "Definition.", "evidence": [{
            "source_id": evidence_source or source_id, "locator": "page=1", "evidence_excerpt": "Short excerpt."
        }]}],
        "prerequisites": [], "keywords": ["unit cell"], "applicability": ["crystals"],
        "limitations": ["Convention dependent"], "relations": [],
        "merge_key": "crystallography/unit-cell/definition", "status": "active", "supersedes": [],
        "review": {"status": "model-reviewed", "confidence": 0.8, "reviewer": "model", "notes": ""},
    }
    mapping = {"unit_id": unit_id, "expert_id": "materials-theory", "role": "core", "relevance": 0.9, "reason": "Core concept", "status": "candidate"}
    decision = {"cluster_id": "cluster_000001", "action": "keep-separate", "canonical_unit_id": unit_id, "member_unit_ids": [unit_id], "rationale": "Unique", "conflicts": [], "status": "needs-review"}
    report = {
        "schema_version": "1.0", "package_id": package_id, "inventory_records": 1,
        "knowledge_units": 1, "units_without_evidence": 0,
        "unknown_source_references": 0 if evidence_source is None else 1,
        "extraction_failures": 0, "duplicate_candidates": 0, "conflict_clusters": 0,
        "unresolved_items": [], "validation_status": "pass",
    }
    (package / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
    (package / "inventory.jsonl").write_text(json.dumps(inventory) + "\n", encoding="utf-8")
    (package / "units" / "part-0001.jsonl").write_text(json.dumps(unit) + "\n", encoding="utf-8")
    (package / "summaries" / "course-overview.md").write_text(OVERVIEW_TEXT, encoding="utf-8")
    (package / "mappings" / "expert-units.jsonl").write_text(json.dumps(mapping) + "\n", encoding="utf-8")
    (package / "merge" / "decisions.jsonl").write_text(json.dumps(decision) + "\n", encoding="utf-8")
    (package / "qa" / "report.json").write_text(json.dumps(report), encoding="utf-8")
    return package


class TutorialPackageTests(unittest.TestCase):
    def test_valid_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = write_tutorial_package(Path(temp_dir))
            result = TUTORIAL_MODULE.validate_package(package)
            self.assertEqual(result["sources"], 1)
            self.assertEqual(result["units"], 1)

    def test_unknown_evidence_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = write_tutorial_package(Path(temp_dir), evidence_source="src_bbbbbbbbbbbbbbbb")
            with self.assertRaises(ValueError):
                TUTORIAL_MODULE.validate_package(package)

    def test_template_placeholders_are_rejected(self) -> None:
        template = Path(__file__).parents[1] / "tutorial-package-template"
        with self.assertRaises(ValueError):
            TUTORIAL_MODULE.validate_package(template)

    def test_initializer_hashes_without_copying_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            source.mkdir()
            (source / "lesson.txt").write_text("crystal knowledge", encoding="utf-8")
            (source / "pdf-password.local.txt").write_text("private-password", encoding="utf-8")
            package, count, warnings = INIT_TUTORIAL_MODULE.initialize_package(
                source, root / "packages", "lesson-one", "Lesson One"
            )
            self.assertEqual(count, 1)
            self.assertEqual(warnings, ["skipped local secret file: pdf-password.local.txt"])
            record = json.loads((package / "inventory.jsonl").read_text(encoding="utf-8"))
            manifest = json.loads((package / "package.json").read_text(encoding="utf-8"))
            self.assertEqual(record["relative_path"], "lesson.txt")
            self.assertNotIn("private-password", (package / "inventory.jsonl").read_text(encoding="utf-8"))
            self.assertTrue(record["source_id"].endswith(record["sha256"][:16]))
            self.assertFalse((package / "lesson.txt").exists())
            self.assertEqual(manifest["publication"]["distribution"], "local-only")
            self.assertTrue(manifest["publication"]["upload_requires_explicit_user_approval"])

    def test_long_evidence_excerpt_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = write_tutorial_package(Path(temp_dir))
            unit_path = package / "units" / "part-0001.jsonl"
            unit = json.loads(unit_path.read_text(encoding="utf-8"))
            unit["claims"][0]["evidence"][0]["evidence_excerpt"] = "x" * 501
            unit_path.write_text(json.dumps(unit) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                TUTORIAL_MODULE.validate_package(package)


class PublicationSafetyTests(unittest.TestCase):
    def test_derived_markdown_requires_human_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "summary.md").write_text("Original scientific synthesis.", encoding="utf-8")
            result = PUBLICATION_MODULE.check_candidate(root)
            self.assertEqual(result["status"], "ready-for-human-review")
            self.assertFalse(result["upload_authorized"])

    def test_original_binary_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "tutorial.pdf").write_bytes(b"not a real pdf")
            result = PUBLICATION_MODULE.check_candidate(root)
            self.assertEqual(result["status"], "blocked")
            self.assertTrue(any("file type" in item for item in result["blockers"]))

    def test_author_metadata_is_blocked_from_public_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "unit.json").write_text(json.dumps({"summary": "Derived knowledge", "author": "A Name"}), encoding="utf-8")
            result = PUBLICATION_MODULE.check_candidate(root)
            self.assertEqual(result["status"], "blocked")
            self.assertTrue(any("author metadata" in item for item in result["blockers"]))


if __name__ == "__main__":
    unittest.main()
