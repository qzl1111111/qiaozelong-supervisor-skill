from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Iterator


PACKAGE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
VERSION = re.compile(r"^\d+\.\d+\.\d+$")
PACKAGE_STATUS = {"draft", "review", "approved", "superseded"}
EXTRACTION_STATUS = {"pending", "partial", "complete", "failed", "not-needed"}
KNOWLEDGE_TYPES = {
    "concept", "procedure", "formula", "method", "example", "warning",
    "troubleshooting", "data-interpretation", "code-pattern", "terminology",
}
UNIT_STATUS = {"active", "deprecated", "superseded"}
REVIEW_STATUS = {"needs-review", "model-reviewed", "human-reviewed"}
MAPPING_ROLES = {"core", "support", "procedure", "warning", "reference"}
MAPPING_STATUS = {"candidate", "approved", "rejected"}
MERGE_ACTIONS = {"keep-separate", "merge", "related", "conflict", "supersede"}
OVERVIEW_HEADINGS = (
    "## Scope and audience", "## Source coverage", "## Topic hierarchy",
    "## Prerequisites", "## Key knowledge units",
    "## Formulas, units, and conventions",
    "## Limitations and unresolved questions", "## Candidate expert mappings",
)


def fail(condition: bool, message: str) -> None:
    if condition:
        raise ValueError(message)


def iso_date(value: Any, field: str) -> str:
    text = str(value)
    try:
        date.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"{field} must use YYYY-MM-DD") from error
    return text


def safe_relative(value: Any, field: str) -> str:
    text = str(value)
    path = Path(text)
    fail(not text or path.is_absolute() or ".." in path.parts, f"{field} must be a safe relative path")
    return text


def nonempty_list(value: Any, field: str) -> list[Any]:
    fail(not isinstance(value, list) or not value, f"{field} must be a non-empty list")
    return value


def read_json(path: Path) -> dict[str, Any]:
    fail(not path.is_file(), f"missing {path}")
    text = path.read_text(encoding="utf-8")
    fail("REPLACE_ME" in text, f"{path}: unresolved REPLACE_ME marker")
    value = json.loads(text)
    fail(not isinstance(value, dict), f"{path}: expected a JSON object")
    return value


def read_jsonl(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    fail(not path.is_file(), f"missing {path}")
    with path.open("r", encoding="utf-8") as stream:
        found = False
        for line_number, line in enumerate(stream, 1):
            fail(not line.strip(), f"{path}:{line_number}: blank JSONL lines are not allowed")
            fail("REPLACE_ME" in line, f"{path}:{line_number}: unresolved REPLACE_ME marker")
            value = json.loads(line)
            fail(not isinstance(value, dict), f"{path}:{line_number}: expected a JSON object")
            found = True
            yield line_number, value
        fail(not found, f"{path}: JSONL file must not be empty")


def validate_package(root: Path) -> dict[str, Any]:
    fail(not root.is_dir(), f"package directory does not exist: {root}")
    package = read_json(root / "package.json")
    package_id = str(package.get("package_id", ""))
    fail(package.get("schema_version") != "1.0", "package schema_version must be 1.0")
    fail(not PACKAGE_ID.fullmatch(package_id), "package_id must use lowercase hyphen-case")
    fail(not str(package.get("title", "")).strip(), "package title is required")
    fail(not VERSION.fullmatch(str(package.get("version", ""))), "package version must use MAJOR.MINOR.PATCH")
    fail(package.get("status") not in PACKAGE_STATUS, "invalid package status")
    nonempty_list(package.get("languages"), "languages")
    nonempty_list(package.get("scope"), "scope")
    iso_date(package.get("created_at"), "created_at")
    iso_date(package.get("updated_at"), "updated_at")
    max_bytes = int(package.get("unit_shard_max_bytes", 5_242_880))
    max_records = int(package.get("unit_shard_max_records", 500))
    fail(max_bytes <= 0 or max_bytes > 10_485_760, "unit_shard_max_bytes must be between 1 and 10485760")
    fail(max_records <= 0 or max_records > 1000, "unit_shard_max_records must be between 1 and 1000")

    sources: dict[str, dict[str, Any]] = {}
    extraction_failures = 0
    for line_number, item in read_jsonl(root / "inventory.jsonl"):
        context = f"inventory.jsonl:{line_number}"
        sha = str(item.get("sha256", ""))
        source_id = str(item.get("source_id", ""))
        fail(not SHA256.fullmatch(sha), f"{context}: invalid sha256")
        fail(source_id != f"src_{sha[:16]}", f"{context}: source_id must match sha256 prefix")
        fail(source_id in sources, f"{context}: duplicate source_id {source_id}")
        safe_relative(item.get("relative_path"), f"{context} relative_path")
        fail(int(item.get("size_bytes", -1)) < 0, f"{context}: size_bytes must be non-negative")
        fail(not str(item.get("media_type", "")).strip(), f"{context}: media_type is required")
        status = item.get("extraction_status")
        fail(status not in EXTRACTION_STATUS, f"{context}: invalid extraction_status")
        fail(not isinstance(item.get("extracted_artifacts", []), list), f"{context}: extracted_artifacts must be a list")
        fail(not isinstance(item.get("warnings", []), list), f"{context}: warnings must be a list")
        sources[source_id] = item
        extraction_failures += int(status == "failed")

    unit_files = sorted((root / "units").glob("part-*.jsonl"))
    fail(not unit_files, "units must contain part-*.jsonl")
    unit_ids: set[str] = set()
    unknown_source_refs = 0
    units_without_evidence = 0
    unit_count = 0
    expected_unit = re.compile(rf"^ku_{re.escape(package_id)}_\d{{6,}}$")
    for path in unit_files:
        fail(path.stat().st_size > max_bytes, f"{path}: shard exceeds unit_shard_max_bytes")
        record_count = 0
        for line_number, unit in read_jsonl(path):
            record_count += 1
            unit_count += 1
            context = f"{path}:{line_number}"
            unit_id = str(unit.get("unit_id", ""))
            fail(unit.get("schema_version") != "1.0", f"{context}: schema_version must be 1.0")
            fail(unit.get("package_id") != package_id, f"{context}: package_id mismatch")
            fail(not expected_unit.fullmatch(unit_id), f"{context}: invalid unit_id")
            fail(unit_id in unit_ids, f"{context}: duplicate unit_id")
            unit_ids.add(unit_id)
            fail(not str(unit.get("title", "")).strip() or not str(unit.get("summary", "")).strip(), f"{context}: title and summary are required")
            nonempty_list(unit.get("domain_path"), f"{context} domain_path")
            fail(unit.get("knowledge_type") not in KNOWLEDGE_TYPES, f"{context}: invalid knowledge_type")
            fail(unit.get("status") not in UNIT_STATUS, f"{context}: invalid unit status")
            nonempty_list(unit.get("keywords"), f"{context} keywords")
            claims = nonempty_list(unit.get("claims"), f"{context} claims")
            has_evidence = False
            for claim in claims:
                fail(not isinstance(claim, dict) or not str(claim.get("claim_id", "")).strip() or not str(claim.get("text", "")).strip(), f"{context}: invalid claim")
                evidence = nonempty_list(claim.get("evidence"), f"{context} evidence")
                for reference in evidence:
                    fail(not isinstance(reference, dict), f"{context}: evidence must be objects")
                    source_id = str(reference.get("source_id", ""))
                    fail(not str(reference.get("locator", "")).strip(), f"{context}: evidence locator is required")
                    has_evidence = True
                    if source_id not in sources:
                        unknown_source_refs += 1
            units_without_evidence += int(not has_evidence)
            review = unit.get("review", {})
            fail(not isinstance(review, dict) or review.get("status") not in REVIEW_STATUS, f"{context}: invalid review")
            confidence = float(review.get("confidence", -1))
            fail(not 0.0 <= confidence <= 1.0, f"{context}: review confidence must be 0..1")
        fail(record_count > max_records, f"{path}: shard exceeds unit_shard_max_records")

    overview_path = root / "summaries" / "course-overview.md"
    fail(not overview_path.is_file(), "missing summaries/course-overview.md")
    overview = overview_path.read_text(encoding="utf-8")
    fail("REPLACE_ME" in overview, "course overview contains REPLACE_ME")
    positions = [overview.find(heading) for heading in OVERVIEW_HEADINGS]
    fail(any(position < 0 for position in positions) or positions != sorted(positions), "course overview headings are missing or out of order")

    mapping_count = 0
    for line_number, mapping in read_jsonl(root / "mappings" / "expert-units.jsonl"):
        mapping_count += 1
        context = f"expert-units.jsonl:{line_number}"
        fail(mapping.get("unit_id") not in unit_ids, f"{context}: unknown unit_id")
        fail(not PACKAGE_ID.fullmatch(str(mapping.get("expert_id", ""))), f"{context}: invalid expert_id")
        fail(mapping.get("role") not in MAPPING_ROLES, f"{context}: invalid role")
        fail(mapping.get("status") not in MAPPING_STATUS, f"{context}: invalid status")
        fail(not 0.0 <= float(mapping.get("relevance", -1)) <= 1.0, f"{context}: relevance must be 0..1")

    merge_count = 0
    conflict_clusters = 0
    for line_number, decision in read_jsonl(root / "merge" / "decisions.jsonl"):
        merge_count += 1
        context = f"decisions.jsonl:{line_number}"
        fail(decision.get("action") not in MERGE_ACTIONS, f"{context}: invalid action")
        members = nonempty_list(decision.get("member_unit_ids"), f"{context} member_unit_ids")
        fail(any(member not in unit_ids for member in members), f"{context}: unknown member unit")
        canonical = decision.get("canonical_unit_id")
        fail(canonical and canonical not in members, f"{context}: canonical unit must be a member")
        conflict_clusters += int(decision.get("action") == "conflict")

    report = read_json(root / "qa" / "report.json")
    fail(report.get("schema_version") != "1.0" or report.get("package_id") != package_id, "QA report identity mismatch")
    expected_counts = {
        "inventory_records": len(sources),
        "knowledge_units": unit_count,
        "units_without_evidence": units_without_evidence,
        "unknown_source_references": unknown_source_refs,
        "extraction_failures": extraction_failures,
        "conflict_clusters": conflict_clusters,
    }
    for field, expected in expected_counts.items():
        fail(int(report.get(field, -1)) != expected, f"QA report {field} must be {expected}")
    fail(units_without_evidence > 0 or unknown_source_refs > 0, "package contains ungrounded units")
    fail(report.get("validation_status") == "pass" and report.get("unresolved_items"), "QA report cannot pass with unresolved items")

    return {
        "package_id": package_id,
        "sources": len(sources),
        "units": unit_count,
        "shards": len(unit_files),
        "mappings": mapping_count,
        "merge_decisions": merge_count,
        "extraction_failures": extraction_failures,
        "package_fingerprint": hashlib.sha256("\n".join(sorted(unit_ids)).encode("utf-8")).hexdigest(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Tutorial Knowledge Package")
    parser.add_argument("root", type=Path, help="Tutorial package directory")
    args = parser.parse_args(argv)
    try:
        result = validate_package(args.root)
    except (ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
