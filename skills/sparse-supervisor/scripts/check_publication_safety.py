from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ALLOWED_EXTENSIONS = {".md", ".json", ".jsonl"}
BLOCKED_DIRECTORIES = {"raw", "raw-tutorials", "sources", "source", "extracted", "private", "private-provenance"}
BLOCKED_FILENAMES = {"inventory.jsonl"}
PRIVATE_KEYS = {
    "author", "authors", "creator", "creators", "instructor", "presenter",
    "local_path", "source_path", "absolute_path", "original_filename",
}
LOCAL_PATH = re.compile(r"(?:[A-Za-z]:\\|/home/|/Users/|\\Users\\)")


def inspect_value(value: Any, location: str, blockers: list[str], warnings: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in PRIVATE_KEYS:
                blockers.append(f"{location}: private or author metadata key '{key}'")
            if key == "evidence_excerpt" and len(str(item)) > 500:
                blockers.append(f"{location}: evidence excerpt exceeds 500 characters")
            inspect_value(item, f"{location}.{key}", blockers, warnings)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            inspect_value(item, f"{location}[{index}]", blockers, warnings)
    elif isinstance(value, str):
        if LOCAL_PATH.search(value):
            blockers.append(f"{location}: local filesystem path detected")
        if "REPLACE_ME" in value:
            blockers.append(f"{location}: unresolved template marker")


def check_candidate(root: Path) -> dict[str, Any]:
    if not root.is_dir():
        raise ValueError(f"candidate directory does not exist: {root}")
    blockers: list[str] = []
    warnings: list[str] = []
    file_count = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            blockers.append(f"{path}: symbolic links are not allowed")
            continue
        if not path.is_file():
            continue
        file_count += 1
        relative = path.relative_to(root)
        lower_parts = {part.lower() for part in relative.parts[:-1]}
        if lower_parts & BLOCKED_DIRECTORIES:
            blockers.append(f"{relative}: blocked private/source directory")
        if path.name.lower() in BLOCKED_FILENAMES:
            blockers.append(f"{relative}: private inventory must not be published")
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            blockers.append(f"{relative}: file type is not allowed in a public-derived candidate")
            continue
        if path.stat().st_size > 5_242_880:
            blockers.append(f"{relative}: file exceeds 5 MiB review limit")
        text = path.read_text(encoding="utf-8")
        if LOCAL_PATH.search(text):
            blockers.append(f"{relative}: local filesystem path detected")
        if "REPLACE_ME" in text:
            blockers.append(f"{relative}: unresolved template marker")
        if path.suffix.lower() == ".json":
            inspect_value(json.loads(text), str(relative), blockers, warnings)
        elif path.suffix.lower() == ".jsonl":
            for line_number, line in enumerate(text.splitlines(), 1):
                if not line.strip():
                    blockers.append(f"{relative}:{line_number}: blank JSONL line")
                    continue
                inspect_value(json.loads(line), f"{relative}:{line_number}", blockers, warnings)
    if file_count == 0:
        blockers.append("candidate contains no files")
    warnings.extend(
        [
            "Manual review is required for personal names embedded in prose.",
            "Manual review is required for substantial similarity, licensing, and whether the summary substitutes for a tutorial.",
            "A clean check is not upload authorization; explicit user approval for exact files and destination is still required.",
        ]
    )
    return {
        "status": "blocked" if blockers else "ready-for-human-review",
        "files_checked": file_count,
        "blockers": sorted(set(blockers)),
        "warnings": warnings,
        "upload_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a public-derived candidate without uploading it")
    parser.add_argument("root", type=Path, help="Candidate directory containing derived files only")
    args = parser.parse_args(argv)
    try:
        result = check_candidate(args.root)
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
