# Routing schema

Use the router when a reproducible allocation record is useful. The script does not judge semantics; the supervisor supplies normalized evidence-based scores from `0.0` to `1.0`.

## Input

```json
{
  "task": "Evaluate a catalyst hypothesis",
  "stage": "theory_validation",
  "risk": 0.7,
  "threshold": 0.55,
  "max_active": 3,
  "specialists": [
    {
      "name": "theory",
      "task_fit": 0.95,
      "expertise": 0.95,
      "reliability": 0.85,
      "evidence_access": 0.90,
      "availability": 1.0,
      "cost": 0.50,
      "overlap": 0.10,
      "reviewer": false
    }
  ]
}
```

## Score

```text
0.30 * task_fit
+ 0.30 * expertise
+ 0.18 * reliability
+ 0.12 * evidence_access
+ 0.10 * availability
- 0.08 * cost
- 0.12 * overlap
```

The router selects candidates above the threshold, capped by `max_active`. If none passes, it selects the highest-scoring candidate and marks the plan as low confidence. For high-risk tasks (`risk >= 0.70`), the best qualified reviewer may be added if capacity remains.

Weights are normalized selected scores. Unselected specialists receive zero work and remain on standby.

## Output

The output contains the primary specialist, activated specialists and weights, standby specialists with rejection reasons, and whether human review is required.
