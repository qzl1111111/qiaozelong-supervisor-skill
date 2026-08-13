from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FIELDS = (
    "task_fit",
    "expertise",
    "reliability",
    "evidence_access",
    "availability",
    "cost",
    "overlap",
)


def bounded(value: Any, field: str) -> float:
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{field} must be between 0 and 1")
    return number


def score(candidate: dict[str, Any]) -> float:
    values = {field: bounded(candidate.get(field, 0.0), field) for field in FIELDS}
    result = (
        0.30 * values["task_fit"]
        + 0.30 * values["expertise"]
        + 0.18 * values["reliability"]
        + 0.12 * values["evidence_access"]
        + 0.10 * values["availability"]
        - 0.08 * values["cost"]
        - 0.12 * values["overlap"]
    )
    return round(max(0.0, min(1.0, result)), 6)


def route(request: dict[str, Any]) -> dict[str, Any]:
    specialists = request.get("specialists", [])
    if not specialists:
        raise ValueError("specialists must contain at least one candidate")

    threshold = bounded(request.get("threshold", 0.55), "threshold")
    risk = bounded(request.get("risk", 0.0), "risk")
    max_active = int(request.get("max_active", 3))
    if not 1 <= max_active <= 5:
        raise ValueError("max_active must be between 1 and 5")

    ranked = []
    seen = set()
    for item in specialists:
        name = str(item.get("name", "")).strip()
        if not name or name in seen:
            raise ValueError("specialist names must be non-empty and unique")
        seen.add(name)
        ranked.append({**item, "name": name, "score": score(item)})
    ranked.sort(key=lambda item: (-item["score"], item["name"]))

    selected = [item for item in ranked if item["score"] >= threshold][:max_active]
    low_confidence = False
    if not selected:
        selected = [ranked[0]]
        low_confidence = True

    if risk >= 0.70 and len(selected) < max_active and not any(item.get("reviewer") for item in selected):
        reviewer = next(
            (item for item in ranked if item.get("reviewer") and item not in selected and item["score"] >= threshold),
            None,
        )
        if reviewer:
            selected.append(reviewer)

    selected_names = {item["name"] for item in selected}
    total = sum(item["score"] for item in selected) or 1.0
    activated = [
        {
            "name": item["name"],
            "score": item["score"],
            "weight": round(item["score"] / total, 6),
            "role": "primary" if index == 0 else ("reviewer" if item.get("reviewer") else "specialist"),
        }
        for index, item in enumerate(selected)
    ]

    standby = []
    for item in ranked:
        if item["name"] in selected_names:
            continue
        reason = "below_threshold" if item["score"] < threshold else "team_capacity_or_lower_marginal_value"
        standby.append({"name": item["name"], "score": item["score"], "weight": 0.0, "reason": reason})

    return {
        "task": request.get("task", ""),
        "stage": request.get("stage", "unspecified"),
        "primary": activated[0]["name"],
        "activated": activated,
        "standby": standby,
        "low_confidence_routing": low_confidence,
        "human_review_required": risk >= 0.70,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a sparse specialist routing plan")
    parser.add_argument("request", type=Path, help="Path to a UTF-8 JSON routing request")
    parser.add_argument("--output", type=Path, help="Optional output JSON path")
    args = parser.parse_args()

    result = route(json.loads(args.request.read_text(encoding="utf-8")))
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
