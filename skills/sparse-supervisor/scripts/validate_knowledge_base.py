from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


EXPERT_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SOURCE_REF = re.compile(r"\[([A-Z][A-Z0-9_-]*)\]")
REQUIRED_FIELDS = {
    "schema_version",
    "expert_id",
    "display_name",
    "summary",
    "domains",
    "capabilities",
    "knowledge_files",
    "updated_at",
    "limitations",
    "escalation_triggers",
    "sources",
}
REQUIRED_HEADINGS = (
    "## Scope",
    "## Core knowledge",
    "## Decision rules",
    "## Workflow",
    "## Evidence standards",
    "## Known limitations",
    "## Escalation triggers",
    "## Terminology",
)
AUTHORITIES = {"primary", "official", "review", "internal-reviewed"}


def nonempty_strings(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a non-empty list")
    result = []
    for item in value:
        text = str(item).strip()
        if not text:
            raise ValueError(f"{field} must not contain empty values")
        result.append(text)
    return result


def iso_date(value: Any, field: str) -> str:
    text = str(value)
    try:
        date.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"{field} must use YYYY-MM-DD") from error
    return text


def validate_expert(directory: Path) -> dict[str, Any]:
    manifest_path = directory / "expert.json"
    if not manifest_path.is_file():
        raise ValueError(f"{directory}: missing expert.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_FIELDS - set(manifest))
    if missing:
        raise ValueError(f"{manifest_path}: missing fields: {', '.join(missing)}")
    if manifest["schema_version"] != "1.0":
        raise ValueError(f"{manifest_path}: schema_version must be 1.0")
    expert_id = str(manifest["expert_id"])
    if not EXPERT_ID.fullmatch(expert_id) or expert_id != directory.name:
        raise ValueError(f"{manifest_path}: expert_id must match directory name and use lowercase hyphen-case")
    for field in ("domains", "capabilities", "knowledge_files", "limitations", "escalation_triggers"):
        manifest[field] = nonempty_strings(manifest[field], field)
    if not str(manifest["display_name"]).strip() or not str(manifest["summary"]).strip():
        raise ValueError(f"{manifest_path}: display_name and summary are required")
    iso_date(manifest["updated_at"], "updated_at")
    if manifest.get("review_after"):
        iso_date(manifest["review_after"], "review_after")

    sources = manifest["sources"]
    if not isinstance(sources, list) or not sources:
        raise ValueError(f"{manifest_path}: sources must be a non-empty list")
    source_ids = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError(f"{manifest_path}: every source must be an object")
        for field in ("id", "title", "type", "locator", "authority"):
            if not str(source.get(field, "")).strip():
                raise ValueError(f"{manifest_path}: every source needs {field}")
        source_id = str(source["id"])
        if source_id in source_ids:
            raise ValueError(f"{manifest_path}: duplicate source id {source_id}")
        source_ids.add(source_id)
        if source["authority"] not in AUTHORITIES:
            raise ValueError(f"{manifest_path}: invalid authority for {source_id}")
        for field in ("published_at", "accessed_at"):
            if source.get(field):
                iso_date(source[field], f"{field} for {source_id}")

    referenced_ids = set()
    for relative_name in manifest["knowledge_files"]:
        relative = Path(relative_name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"{manifest_path}: unsafe knowledge file path {relative_name}")
        path = directory / relative
        if not path.is_file() or path.suffix.lower() != ".md":
            raise ValueError(f"{manifest_path}: missing Markdown knowledge file {relative_name}")
        text = path.read_text(encoding="utf-8")
        if "REPLACE_ME" in text or "REPLACE_ME" in json.dumps(manifest):
            raise ValueError(f"{directory}: unresolved REPLACE_ME marker")
        if path.name == "knowledge.md":
            positions = [text.find(heading) for heading in REQUIRED_HEADINGS]
            if any(position < 0 for position in positions) or positions != sorted(positions):
                raise ValueError(f"{path}: required headings are missing or out of order")
        referenced_ids.update(SOURCE_REF.findall(text))
    unknown = sorted(referenced_ids - source_ids)
    if unknown:
        raise ValueError(f"{directory}: unknown source references: {', '.join(unknown)}")
    if not referenced_ids:
        raise ValueError(f"{directory}: knowledge files must cite at least one declared source id")
    return {"expert_id": expert_id, "knowledge_files": len(manifest["knowledge_files"]), "sources": len(sources)}


def validate_knowledge_base(root: Path) -> list[dict[str, Any]]:
    if not root.is_dir():
        raise ValueError(f"knowledge-base directory does not exist: {root}")
    directories = sorted(path for path in root.iterdir() if path.is_dir())
    if not directories:
        raise ValueError("knowledge base must contain at least one expert directory")
    return [validate_expert(directory) for directory in directories]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Sparse Supervisor expert knowledge base")
    parser.add_argument("root", type=Path, help="Directory containing one subdirectory per expert")
    args = parser.parse_args(argv)
    try:
        results = validate_knowledge_base(args.root)
    except (ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    for result in results:
        print(f"{result['expert_id']}: valid ({result['knowledge_files']} files, {result['sources']} sources)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
