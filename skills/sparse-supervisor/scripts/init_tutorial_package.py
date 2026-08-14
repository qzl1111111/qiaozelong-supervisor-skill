from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
from datetime import date
from pathlib import Path
from typing import Any


PACKAGE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SECRET_FILENAMES = {".env", "credentials.json", "secrets.json", "pdf-password.local.txt"}


def is_local_secret(path: Path) -> bool:
    name = path.name.lower()
    return name in SECRET_FILENAMES or ".local." in name or name.endswith((".secret", ".credentials"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory_source(source_root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not source_root.is_dir():
        raise ValueError(f"source directory does not exist: {source_root}")
    records = []
    warnings = []
    for path in sorted(source_root.rglob("*")):
        if path.is_symlink():
            warnings.append(f"skipped symbolic link: {path.relative_to(source_root).as_posix()}")
            continue
        if not path.is_file():
            continue
        if is_local_secret(path):
            warnings.append(f"skipped local secret file: {path.relative_to(source_root).as_posix()}")
            continue
        sha = sha256_file(path)
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        records.append(
            {
                "source_id": f"src_{sha[:16]}",
                "relative_path": path.relative_to(source_root).as_posix(),
                "sha256": sha,
                "size_bytes": path.stat().st_size,
                "media_type": media_type,
                "source_role": "primary-tutorial",
                "extraction_status": "pending",
                "extracted_artifacts": [],
                "warnings": [],
            }
        )
    if not records:
        raise ValueError("source directory contains no regular files")
    return records, warnings


def initialize_package(
    source_root: Path,
    output_root: Path,
    package_id: str,
    title: str,
    language: str = "zh-CN",
    today: date | None = None,
) -> tuple[Path, int, list[str]]:
    if not PACKAGE_ID.fullmatch(package_id):
        raise ValueError("package_id must use lowercase hyphen-case")
    if not title.strip():
        raise ValueError("title is required")
    package = output_root / package_id
    if package.exists():
        raise ValueError(f"output package already exists: {package}")
    records, warnings = inventory_source(source_root)
    current = (today or date.today()).isoformat()
    for relative in ("extracted", "units", "summaries", "mappings", "merge", "qa"):
        (package / relative).mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "1.1",
        "package_id": package_id,
        "title": title,
        "version": "1.0.0",
        "status": "draft",
        "languages": [language],
        "created_at": current,
        "updated_at": current,
        "description": "To be completed during tutorial ingestion.",
        "scope": ["unclassified"],
        "unit_shard_max_bytes": 5_242_880,
        "unit_shard_max_records": 500,
        "publication": {
            "distribution": "local-only",
            "source_metadata_visibility": "private",
            "contains_original_files": False,
            "upload_requires_explicit_user_approval": True,
        },
    }
    (package / "package.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    inventory_text = "".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n" for record in records)
    (package / "inventory.jsonl").write_text(inventory_text, encoding="utf-8")
    return package, len(records), warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize a Tutorial Knowledge Package and hash its source files")
    parser.add_argument("source_root", type=Path, help="Directory containing exactly one tutorial")
    parser.add_argument("output_root", type=Path, help="Parent directory for generated tutorial packages")
    parser.add_argument("--package-id", required=True, help="Stable lowercase hyphen-case package id")
    parser.add_argument("--title", required=True, help="Human-readable tutorial title")
    parser.add_argument("--language", default="zh-CN", help="Primary synthesis language")
    args = parser.parse_args(argv)
    try:
        package, count, warnings = initialize_package(
            args.source_root, args.output_root, args.package_id, args.title, args.language
        )
    except ValueError as error:
        parser.error(str(error))
    print(f"initialized: {package}")
    print(f"inventory records: {count}")
    for warning in warnings:
        print(f"warning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
