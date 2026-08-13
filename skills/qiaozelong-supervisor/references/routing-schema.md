# Routing schema

Use the router when a reproducible allocation record is useful. The router enforces delegation gates, capability coverage, sparse selection, budget limits, and risk review. It does not judge semantic truth; the supervisor must ground scores in observable evidence.

## Input

```json
{
  "task": "Evaluate a catalyst hypothesis and prepare a report",
  "stage": "theory_validation",
  "complexity": 0.8,
  "risk": 0.7,
  "budget": 0.8,
  "threshold": 0.55,
  "max_active": 3,
  "required_capabilities": ["theory", "reporting"],
  "specialists": [
    {
      "name": "theory-agent",
      "capabilities": ["theory", "simulation"],
      "task_fit": 0.95,
      "expertise": 0.95,
      "reliability": 0.85,
      "evidence_access": 0.90,
      "availability": 1.0,
      "cost": 0.25,
      "overlap": 0.10,
      "reviewer": false,
      "score_basis": ["validated benchmark", "has simulation tool"]
    }
  ]
}
```

All numeric fields use the range `0.0` to `1.0`. `cost` is the fraction of the total normalized budget consumed by activating the specialist.

## Delegation gate

If `complexity <= 0.30`, `risk < 0.70`, and no required external capability is declared, the router returns `mode: supervisor_only`. No specialist is activated.

## Base score

```text
0.30 * task_fit
+ 0.30 * expertise
+ 0.18 * reliability
+ 0.12 * evidence_access
+ 0.10 * availability
- 0.08 * cost
- 0.12 * overlap
```

Do not invent precision. Use coarse evidence-based values when measurements are limited and record their basis. The router returns every score component for audit.

## Sparse selection

The router greedily selects the candidate with the highest marginal utility:

```text
base score
+ capability coverage gain
- redundancy penalty
```

Selection stops as soon as required capabilities are covered. A specialist that adds neither coverage nor review value stays on standby. The total specialist cost must remain within `budget`.

If a required capability remains uncovered, the output is low-confidence and requires human review. For high-risk tasks (`risk >= 0.70`), a qualified reviewer is added only when team capacity and budget allow it.

## Output

The output contains:

- execution mode and primary specialist;
- activated specialists, score components, score evidence, weights, costs, and capability gains;
- standby specialists with explicit rejection reasons;
- required, covered, and uncovered capabilities;
- budget and budget used;
- low-confidence and human-review flags.

If no candidate fits within the declared budget, the router returns `mode: blocked`, activates nobody, and requests human review. It never silently exceeds the budget.
