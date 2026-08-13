from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def bounded(value: Any, field: str) -> float:
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{field} must be between 0 and 1")
    return number


def names(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    result = []
    for item in value:
        text = str(item).strip()
        if not text:
            raise ValueError(f"{field} must not contain empty values")
        if text not in result:
            result.append(text)
    return result


def ratio(required: list[str], available: list[str]) -> float | None:
    if not required:
        return None
    return len(set(required) & set(available)) / len(set(required))


def validate_registry(registry: dict[str, Any]) -> list[dict[str, Any]]:
    if registry.get("schema_version") != "1.0":
        raise ValueError("registry schema_version must be 1.0")
    specialists = registry.get("specialists")
    if not isinstance(specialists, list) or not specialists:
        raise ValueError("registry specialists must contain at least one entry")

    validated = []
    seen = set()
    for item in specialists:
        if not isinstance(item, dict):
            raise ValueError("each registry specialist must be an object")
        name = str(item.get("name", "")).strip()
        if not name or name in seen:
            raise ValueError("registry specialist names must be non-empty and unique")
        seen.add(name)
        history = item.get("history", {})
        if not isinstance(history, dict):
            raise ValueError(f"history for {name} must be an object")
        completed = int(history.get("completed", 0))
        successful = int(history.get("successful", 0))
        if completed < 0 or successful < 0 or successful > completed:
            raise ValueError(f"invalid history counts for {name}")

        benchmarks = item.get("benchmarks", [])
        if not isinstance(benchmarks, list):
            raise ValueError(f"benchmarks for {name} must be a list")
        checked_benchmarks = []
        for benchmark in benchmarks:
            if not isinstance(benchmark, dict):
                raise ValueError(f"each benchmark for {name} must be an object")
            capability = str(benchmark.get("capability", "")).strip()
            source = str(benchmark.get("source", "")).strip()
            sample_size = int(benchmark.get("sample_size", 0))
            if not capability or not source or sample_size <= 0:
                raise ValueError(f"benchmark capability, source, and positive sample_size are required for {name}")
            checked_benchmarks.append(
                {
                    **benchmark,
                    "capability": capability,
                    "source": source,
                    "sample_size": sample_size,
                    "score": bounded(benchmark.get("score"), f"benchmark score for {name}"),
                }
            )

        validated.append(
            {
                **item,
                "name": name,
                "capabilities": names(item.get("capabilities"), f"capabilities for {name}"),
                "domains": names(item.get("domains"), f"domains for {name}"),
                "tools": names(item.get("tools"), f"tools for {name}"),
                "limitations": names(item.get("limitations"), f"limitations for {name}"),
                "availability": bounded(item.get("availability", 0.0), f"availability for {name}"),
                "cost": bounded(item.get("cost", 0.0), f"cost for {name}"),
                "evidence_access": bounded(item.get("evidence_access", 0.0), f"evidence_access for {name}"),
                "history": {**history, "completed": completed, "successful": successful},
                "benchmarks": checked_benchmarks,
            }
        )
    return validated


def benchmark_expertise(item: dict[str, Any], required_capabilities: list[str]) -> tuple[float, str]:
    relevant = [
        entry
        for entry in item["benchmarks"]
        if not required_capabilities or entry["capability"] in required_capabilities
    ]
    if not relevant:
        return 0.35, "expertise fallback 0.35: no relevant measured benchmark"
    weights = [math.sqrt(min(entry["sample_size"], 100)) for entry in relevant]
    expertise = sum(entry["score"] * weight for entry, weight in zip(relevant, weights)) / sum(weights)
    sources = ", ".join(sorted({entry["source"] for entry in relevant}))
    return round(expertise, 6), f"expertise from {len(relevant)} benchmark(s): {sources}"


def history_reliability(item: dict[str, Any]) -> tuple[float, str]:
    completed = item["history"]["completed"]
    successful = item["history"]["successful"]
    reliability = (successful + 2) / (completed + 4)
    return round(reliability, 6), f"reliability from {successful}/{completed} outcomes with Beta(2,2) smoothing"


def derive_specialists(task: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    specialists = validate_registry(registry)
    required_capabilities = names(task.get("required_capabilities"), "required_capabilities")
    relevant_domains = names(task.get("relevant_domains"), "relevant_domains")
    required_tools = names(task.get("required_tools"), "required_tools")

    derived = []
    for item in specialists:
        matches = [
            value
            for value in (
                ratio(required_capabilities, item["capabilities"]),
                ratio(relevant_domains, item["domains"]),
                ratio(required_tools, item["tools"]),
            )
            if value is not None
        ]
        task_fit = sum(matches) / len(matches) if matches else 0.5
        expertise_capabilities = list(required_capabilities)
        if item.get("reviewer") and "evidence-review" not in expertise_capabilities:
            expertise_capabilities.append("evidence-review")
        expertise, expertise_basis = benchmark_expertise(item, expertise_capabilities)
        reliability, reliability_basis = history_reliability(item)
        derived.append(
            {
                "name": item["name"],
                "capabilities": item["capabilities"],
                "tools": item["tools"],
                "limitations": item["limitations"],
                "task_fit": round(task_fit, 6),
                "expertise": expertise,
                "reliability": reliability,
                "evidence_access": item["evidence_access"],
                "availability": item["availability"],
                "cost": item["cost"],
                "overlap": 0.0,
                "reviewer": bool(item.get("reviewer", False)),
                "score_basis": [
                    "task fit derived from declared capability/domain/tool coverage",
                    expertise_basis,
                    reliability_basis,
                    f"registry last verified: {item.get('last_verified', 'not recorded')}",
                ],
            }
        )

    for candidate in derived:
        candidate_caps = set(candidate["capabilities"])
        similarities = []
        for other in derived:
            if other["name"] == candidate["name"]:
                continue
            other_caps = set(other["capabilities"])
            union = candidate_caps | other_caps
            similarities.append(len(candidate_caps & other_caps) / len(union) if union else 0.0)
        candidate["overlap"] = round(max(similarities, default=0.0), 6)
    return derived


def enrich_request(task: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    if task.get("specialists"):
        raise ValueError("request must not contain specialists when --registry is used")
    return {**task, "specialists": derive_specialists(task, registry), "scoring_source": "capability_registry_v1"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Derive router candidates from a capability registry")
    parser.add_argument("registry", type=Path, help="UTF-8 capability registry JSON")
    parser.add_argument("request", type=Path, help="UTF-8 task request JSON without specialists")
    parser.add_argument("--output", type=Path, help="Optional enriched request output path")
    args = parser.parse_args(argv)

    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    request = json.loads(args.request.read_text(encoding="utf-8"))
    result = enrich_request(request, registry)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
