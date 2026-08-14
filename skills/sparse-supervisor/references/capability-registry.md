# Capability registry

Use a registry when routing weights should come from reusable evidence instead of task-by-task manual scoring. Keep declarations separate from measured evidence and update historical counts only from completed, reviewed tasks.

## Registry schema

```json
{
  "schema_version": "1.0",
  "specialists": [
    {
      "name": "theory-agent",
      "capabilities": ["theory", "simulation"],
      "domains": ["materials-science"],
      "tools": ["python"],
      "limitations": ["no laboratory control"],
      "availability": 1.0,
      "cost": 0.25,
      "evidence_access": 0.8,
      "reviewer": false,
      "last_verified": "2026-08-13",
      "benchmarks": [
        {
          "capability": "theory",
          "score": 0.82,
          "sample_size": 20,
          "source": "benchmark-run-id-or-public-report"
        }
      ],
      "history": {"completed": 12, "successful": 9}
    }
  ]
}
```

All normalized numeric values use `0.0` to `1.0`. `cost` is the fraction of the routing budget used by one activation. A benchmark requires a capability, score, positive sample size, and traceable source. Do not enter invented scores merely to satisfy the schema.

## Task additions

A registry-backed task omits `specialists` and may add:

```json
{
  "required_capabilities": ["theory"],
  "relevant_domains": ["materials-science"],
  "required_tools": ["python"]
}
```

## Deterministic derivation

- `task_fit`: mean coverage of the non-empty required capability, domain, and tool sets.
- `expertise`: relevant benchmark scores weighted by the square root of sample size, capped at 100 samples per benchmark. For reviewer entries, include `evidence-review` benchmarks. Without a relevant measured benchmark, use the conservative fallback `0.35`.
- `reliability`: historical success rate with `Beta(2,2)` smoothing, `(successful + 2) / (completed + 4)`.
- `overlap`: largest Jaccard capability similarity with another registered specialist.
- `availability`, `cost`, and `evidence_access`: validated registry values.

The derived `score_basis` exposes sources and history counts. Registry facts still require governance: verify dates, benchmark provenance, task difficulty, and whether different hosts expose equivalent tools.

## Commands

Create an enriched request for inspection:

```powershell
python scripts/capability_registry.py registry.json task.json --output enriched-request.json
```

Route directly from the registry:

```powershell
python scripts/route_specialists.py task.json --registry registry.json
```

Use `capability-registry.example.json` and `registry-task.example.json` only as structural examples. Replace their placeholder benchmark records before using the result for a real decision.
