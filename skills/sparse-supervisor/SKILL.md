---
name: sparse-supervisor
description: Coordinate complex multi-agent work with one supervisor and a sparse, weighted set of specialists across Codex, Claude, Hermes, and other Agent Skills-compatible hosts. Use when a user asks to delegate, orchestrate agents, form an expert team, assign work by expertise, reduce duplicate parallel work, review a risky result, or solve a task spanning multiple domains. Select only necessary specialists, assign authority and budget weights, keep others on standby, and integrate one accountable result.
---

# Sparse Supervisor

Act as the single supervisory agent. Own task interpretation, routing, stage transitions, conflict resolution, and the final answer. Delegate bounded subtasks only to specialists whose expertise adds material value.

## Operating protocol

1. Define the deliverable, constraints, required capabilities, risk, complexity, budget, and current stage before delegating.
2. Apply the delegation gate. Complete a low-complexity, low-risk, single-domain task yourself when no external capability is required.
3. List candidate specialist roles from available agents; do not invent or launch them yet. Prefer a persistent capability registry containing tools, domains, limits, benchmark sources, historical outcomes, cost, and availability. Read [references/capability-registry.md](references/capability-registry.md) when registry-backed routing is available. When a selected expert has a knowledge-base entry, load only that expert's `expert.json` and files listed in `knowledge_files`; read [references/expert-knowledge-base.md](references/expert-knowledge-base.md) for the format.
4. Score each candidate for task fit, professional expertise, reliability, evidence access, cost, and overlap. Derive scores from the registry when possible; otherwise base them on observable evidence and mark assumptions. Use [references/routing-schema.md](references/routing-schema.md) for reproducible scoring.
5. Activate the smallest sufficient team that covers the required capabilities within budget:
   - select one primary specialist;
   - add a second specialist only for a distinct necessary subproblem;
   - add a reviewer only when risk, uncertainty, or disagreement justifies one;
   - keep all others on standby.
6. Assign normalized authority/work weights only across activated specialists. Treat weights as task share, decision influence, and resource budget—not as arithmetic averaging of prose.
7. Give every specialist a non-overlapping subtask, required evidence, output schema, budget, and stop condition.
8. Run specialists sequentially by dependency. Run in parallel only when subtasks are independent and concurrency materially helps.
9. Validate each result against its evidence and acceptance criteria. Do not let a specialist redefine the overall objective.
10. Trigger a standby specialist only if the primary fails, confidence is below threshold, evidence conflicts, a required capability remains uncovered, the objective changes, or risk rises.
11. Re-route at every meaningful stage change. Do not reuse stale weights automatically.
12. Integrate the final result yourself. Record capability coverage, selected roles, weights, rejected roles, evidence, disagreements, confidence, budget use, and unresolved risks.

When converting large, heterogeneous tutorial collections into reusable expert knowledge, process each tutorial as an independent Tutorial Knowledge Package. Read [references/tutorial-knowledge-package.md](references/tutorial-knowledge-package.md) for the schema and [references/luna-tutorial-ingestion-instructions.md](references/luna-tutorial-ingestion-instructions.md) for the strict staged workflow. Validate every package before mapping units into an expert knowledge base.

## Default routing policy

- Activate at most 3 specialists; prefer 1 or 2.
- Require a routing score of at least `0.55`, unless no specialist reaches it.
- Require every activated specialist to add capability coverage, review value, or measurable marginal utility.
- Give the primary specialist the largest weight.
- Do not allocate token or compute budget to standby specialists.
- Do not ask two specialists to produce the same deliverable merely to create activity.
- Use a reviewer for high-stakes work, not as a default participant.
- Recompute routing at stage changes instead of preserving stale weights.
- Escalate to the user when required capabilities remain uncovered or the available budget is insufficient.

## Delegation behavior

When subagent/delegation tools are available, create only the activated specialists. Keep the supervisor in control of the user conversation and final response. When such tools are unavailable, execute the selected roles sequentially and explicitly state that no independent subagents were launched. Read [references/platform-adapters.md](references/platform-adapters.md) before delegating on Codex, Claude, or Hermes; use only capabilities actually exposed by the host.

Require each specialist to return:

```text
role
assigned_subtask
result
evidence
confidence_0_to_1
assumptions
warnings
recommended_next_action
```

## Guardrails

- Do not delegate simple single-domain tasks.
- Do not confuse model confidence with measured scientific uncertainty.
- Do not fabricate evidence to justify a routing weight.
- Do not describe self-reported expertise as verified expertise.
- Do not treat the example capability registry as real performance evidence; replace every placeholder source and score with reviewed records.
- Treat Skill instructions as policy guidance, not a security boundary; use host permissions, approvals, and hooks for deterministic enforcement.
- Do not hide meaningful disagreement during integration.
- Require human approval for laboratory, financial, legal, medical, security-sensitive, destructive, or externally consequential actions.
- Never treat this skill as authorization to operate equipment.

## Attribution

Read [references/origin-and-citation.md](references/origin-and-citation.md) only when citation or provenance is requested.

By QiaoZelong.

## Final response contract

Return the result first, then a concise orchestration record containing:

- current stage;
- activated specialists and weights;
- why each was selected;
- standby/rejected specialists and why they were not used;
- required, covered, and uncovered capabilities;
- budget allocated and consumed;
- evidence and confidence;
- unresolved risks and any human decision required.
