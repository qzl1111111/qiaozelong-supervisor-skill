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

SCORE_WEIGHTS = {
    "task_fit": 0.30,
    "expertise": 0.30,
    "reliability": 0.18,
    "evidence_access": 0.12,
    "availability": 0.10,
    "cost": -0.08,
    "overlap": -0.12,
}


def bounded(value: Any, field: str) -> float:
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{field} must be between 0 and 1")
    return number


def normalized_names(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    result = []
    for item in value:
        name = str(item).strip()
        if not name:
            raise ValueError(f"{field} must not contain empty names")
        if name not in result:
            result.append(name)
    return result


def score(candidate: dict[str, Any]) -> tuple[float, dict[str, float]]:
    values = {field: bounded(candidate.get(field, 0.0), field) for field in FIELDS}
    components = {field: round(values[field] * weight, 6) for field, weight in SCORE_WEIGHTS.items()}
    result = sum(components.values())
    return round(max(0.0, min(1.0, result)), 6), components


def candidate_cost(candidate: dict[str, Any]) -> float:
    return bounded(candidate.get("cost", 0.0), "cost")


def validate_request(request: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    specialists = request.get("specialists", [])
    if not isinstance(specialists, list) or not specialists:
        raise ValueError("specialists must contain at least one candidate")

    required_capabilities = normalized_names(request.get("required_capabilities"), "required_capabilities")
    ranked = []
    seen = set()
    for item in specialists:
        if not isinstance(item, dict):
            raise ValueError("each specialist must be an object")
        name = str(item.get("name", "")).strip()
        if not name or name in seen:
            raise ValueError("specialist names must be non-empty and unique")
        seen.add(name)
        capabilities = normalized_names(item.get("capabilities"), f"capabilities for {name}")
        score_basis = normalized_names(item.get("score_basis"), f"score_basis for {name}")
        value, components = score(item)
        ranked.append(
            {
                **item,
                "name": name,
                "capabilities": capabilities,
                "score_basis": score_basis,
                "score": value,
                "score_components": components,
            }
        )
    ranked.sort(key=lambda item: (-item["score"], item["name"]))
    return ranked, required_capabilities


def route(request: dict[str, Any]) -> dict[str, Any]:
    ranked, required = validate_request(request)
    scoring_source = str(request.get("scoring_source", "manual_scores"))
    threshold = bounded(request.get("threshold", 0.55), "threshold")
    risk = bounded(request.get("risk", 0.0), "risk")
    complexity = bounded(request.get("complexity", 0.5), "complexity")
    simple_task_threshold = bounded(request.get("simple_task_threshold", 0.30), "simple_task_threshold")
    budget = bounded(request.get("budget", 1.0), "budget")
    max_active = int(request.get("max_active", 3))
    if not 1 <= max_active <= 5:
        raise ValueError("max_active must be between 1 and 5")

    if complexity <= simple_task_threshold and risk < 0.70 and not required:
        return {
            "task": request.get("task", ""),
            "stage": request.get("stage", "unspecified"),
            "mode": "supervisor_only",
            "scoring_source": scoring_source,
            "primary": "supervisor",
            "activated": [],
            "standby": [
                {"name": item["name"], "score": item["score"], "weight": 0.0, "reason": "simple_task"}
                for item in ranked
            ],
            "required_capabilities": required,
            "covered_capabilities": [],
            "uncovered_capabilities": [],
            "budget": budget,
            "budget_used": 0.0,
            "low_confidence_routing": False,
            "human_review_required": False,
        }

    selected: list[dict[str, Any]] = []
    covered: set[str] = set()
    budget_used = 0.0
    remaining = list(ranked)

    while remaining and len(selected) < max_active:
        best = None
        best_key = None
        for item in remaining:
            cost = candidate_cost(item)
            if budget_used + cost > budget + 1e-9:
                continue
            new_capabilities = set(item["capabilities"]) & set(required) - covered
            coverage_gain = len(new_capabilities) / max(1, len(required))
            redundancy_penalty = bounded(item.get("overlap", 0.0), "overlap") if selected else 0.0
            marginal_utility = item["score"] + 0.35 * coverage_gain - 0.15 * redundancy_penalty
            key = (round(marginal_utility, 6), coverage_gain, item["score"], item["name"])
            if best_key is None or key > best_key:
                best = item
                best_key = key

        if best is None:
            break
        new_caps = set(best["capabilities"]) & set(required) - covered
        if selected and not new_caps and best["score"] < threshold:
            break
        if selected and not new_caps and covered >= set(required):
            break
        selected.append({**best, "marginal_utility": best_key[0], "new_capabilities": sorted(new_caps)})
        covered.update(new_caps)
        budget_used += candidate_cost(best)
        remaining.remove(best)
        if covered >= set(required) and selected:
            break

    low_confidence = False
    if not selected:
        return {
            "task": request.get("task", ""),
            "stage": request.get("stage", "unspecified"),
            "mode": "blocked",
            "scoring_source": scoring_source,
            "primary": "supervisor",
            "activated": [],
            "standby": [
                {"name": item["name"], "score": item["score"], "weight": 0.0, "reason": "budget_exceeded"}
                for item in ranked
            ],
            "required_capabilities": required,
            "covered_capabilities": [],
            "uncovered_capabilities": required,
            "budget": budget,
            "budget_used": 0.0,
            "low_confidence_routing": True,
            "human_review_required": True,
        }

    uncovered = sorted(set(required) - covered)
    if any(item["score"] < threshold for item in selected) or uncovered:
        low_confidence = True

    if risk >= 0.70 and len(selected) < max_active and not any(item.get("reviewer") for item in selected):
        reviewer = next(
            (
                item
                for item in ranked
                if item.get("reviewer")
                and item["name"] not in {selected_item["name"] for selected_item in selected}
                and item["score"] >= threshold
                and budget_used + candidate_cost(item) <= budget + 1e-9
            ),
            None,
        )
        if reviewer:
            selected.append({**reviewer, "marginal_utility": reviewer["score"], "new_capabilities": []})
            budget_used += candidate_cost(reviewer)

    selected_names = {item["name"] for item in selected}
    allocation_utilities = [max(item["marginal_utility"], 0.01) for item in selected]
    if allocation_utilities:
        primary_floor = max(allocation_utilities[1:], default=0.0) + 0.01
        allocation_utilities[0] = max(allocation_utilities[0], primary_floor)
    total = sum(allocation_utilities)
    activated = []
    for index, item in enumerate(selected):
        activated.append(
            {
                "name": item["name"],
                "score": item["score"],
                "score_components": item["score_components"],
                "score_basis": item["score_basis"],
                "weight": round(allocation_utilities[index] / total, 6),
                "cost": candidate_cost(item),
                "capabilities": item["capabilities"],
                "new_capabilities": item["new_capabilities"],
                "role": "primary" if index == 0 else ("reviewer" if item.get("reviewer") else "specialist"),
            }
        )

    standby = []
    for item in ranked:
        if item["name"] in selected_names:
            continue
        if budget_used + candidate_cost(item) > budget + 1e-9:
            reason = "budget_exceeded"
        elif item["score"] < threshold:
            reason = "below_threshold"
        elif not (set(item["capabilities"]) & set(uncovered)):
            reason = "no_additional_capability_coverage"
        else:
            reason = "team_capacity_or_lower_marginal_value"
        standby.append({"name": item["name"], "score": item["score"], "weight": 0.0, "reason": reason})

    return {
        "task": request.get("task", ""),
        "stage": request.get("stage", "unspecified"),
        "mode": "delegated",
        "scoring_source": scoring_source,
        "primary": activated[0]["name"],
        "activated": activated,
        "standby": standby,
        "required_capabilities": required,
        "covered_capabilities": sorted(covered),
        "uncovered_capabilities": uncovered,
        "budget": budget,
        "budget_used": round(budget_used, 6),
        "low_confidence_routing": low_confidence,
        "human_review_required": risk >= 0.70 or bool(uncovered),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a sparse specialist routing plan")
    parser.add_argument("request", type=Path, help="Path to a UTF-8 JSON routing request")
    parser.add_argument("--registry", type=Path, help="Optional capability registry used to derive specialist scores")
    parser.add_argument("--output", type=Path, help="Optional output JSON path")
    args = parser.parse_args()

    request = json.loads(args.request.read_text(encoding="utf-8"))
    if args.registry:
        from capability_registry import enrich_request

        registry = json.loads(args.registry.read_text(encoding="utf-8"))
        request = enrich_request(request, registry)
    result = route(request)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
