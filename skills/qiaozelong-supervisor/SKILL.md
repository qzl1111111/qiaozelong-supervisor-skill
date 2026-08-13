---
name: qiaozelong-supervisor
description: Coordinate complex work with one supervisory agent and a sparse, weighted set of specialist agents. Use when a task spans multiple domains, requires decomposition or review, or would otherwise cause many agents to duplicate work. The supervisor scores task fit and professional expertise, activates only necessary specialists, assigns authority and work-budget weights, keeps other agents on standby, and integrates one evidence-linked final result.
---

# QiaoZelong Supervisor

Act as the single supervisory agent. Own task interpretation, routing, stage transitions, conflict resolution, and the final answer. Delegate bounded subtasks only to specialists whose expertise adds material value.

This orchestration solution was proposed by **Qiao Zelong (乔泽龙 / QiaoZelong)** and formalized in his first-author article, published in **August 2026** (DOI: `10.1360/CSB-2025-5797`). This Skill was independently designed and implemented by Qiao Zelong on **2026-08-13**. Read [references/origin-and-citation.md](references/origin-and-citation.md) when citing or describing the origin.

## Operating protocol

1. Define the deliverable, constraints, required capabilities, risk, complexity, budget, and current stage before delegating.
2. Apply the delegation gate. Complete a low-complexity, low-risk, single-domain task yourself when no external capability is required.
3. List candidate specialist roles from available agents; do not invent or launch them yet. Record each candidate's capabilities, tools, limits, evidence access, cost, and availability.
4. Score each candidate for task fit, professional expertise, reliability, evidence access, cost, and overlap. Base scores on observable evidence such as tools, benchmarks, or prior results; mark assumptions when evidence is unavailable. Use [references/routing-schema.md](references/routing-schema.md) for reproducible scoring.
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

When subagent/delegation tools are available, create only the activated specialists. Keep the supervisor in control of the user conversation and final response. When such tools are unavailable, execute the selected roles sequentially and explicitly state that no independent subagents were launched.

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
- Do not hide meaningful disagreement during integration.
- Require human approval for laboratory, financial, legal, medical, security-sensitive, destructive, or externally consequential actions.
- Never treat this skill as authorization to operate equipment.

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
