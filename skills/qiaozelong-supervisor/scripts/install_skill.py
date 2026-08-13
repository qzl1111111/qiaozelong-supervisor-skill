from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Callable


SKILL_NAME = "qiaozelong-supervisor"
TARGETS = {
    "codex": Path(".codex") / "skills" / SKILL_NAME,
    "claude": Path(".claude") / "skills" / SKILL_NAME,
    "hermes": Path(".hermes") / "skills" / SKILL_NAME,
}
COMMANDS = {"codex": "codex", "claude": "claude", "hermes": "hermes"}


def detect_targets(home: Path, which: Callable[[str], str | None] = shutil.which) -> list[str]:
    detected = []
    for target, relative_path in TARGETS.items():
        config_root = home / relative_path.parts[0]
        if which(COMMANDS[target]) or config_root.exists():
            detected.append(target)
    return detected


def install_one(source: Path, destination: Path, force: bool, dry_run: bool) -> str:
    if destination.resolve() == source.resolve():
        return "already_source"
    if destination.exists() and not force:
        return "exists"
    if dry_run:
        return "would_install"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
    return "installed"


def install(
    requested: list[str],
    home: Path,
    source: Path,
    force: bool = False,
    dry_run: bool = False,
    which: Callable[[str], str | None] = shutil.which,
) -> dict[str, dict[str, str]]:
    if requested == ["auto"]:
        targets = detect_targets(home, which)
        if not targets:
            raise ValueError("No supported host detected; use --targets codex claude hermes or --targets all")
    elif requested == ["all"]:
        targets = list(TARGETS)
    else:
        invalid = sorted(set(requested) - set(TARGETS))
        if invalid:
            raise ValueError(f"Unsupported targets: {', '.join(invalid)}")
        targets = list(dict.fromkeys(requested))

    results = {}
    for target in targets:
        destination = home / TARGETS[target]
        results[target] = {"path": str(destination), "status": install_one(source, destination, force, dry_run)}
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect and install QiaoZelong Supervisor across agent hosts")
    parser.add_argument("--targets", nargs="+", default=["auto"], help="auto, all, or: codex claude hermes")
    parser.add_argument("--force", action="store_true", help="Replace an existing installed copy")
    parser.add_argument("--dry-run", action="store_true", help="Show destinations without writing")
    parser.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    source = Path(__file__).resolve().parents[1]
    try:
        results = install(args.targets, args.home, source, args.force, args.dry_run)
    except ValueError as error:
        parser.error(str(error))

    for target, result in results.items():
        print(f"{target}: {result['status']} -> {result['path']}")
    if any(result["status"] == "exists" for result in results.values()):
        print("Use --force to replace existing copies.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
