---
name: qiaozelong-supervisor
description: Coordinate complex work with one supervisory agent and a sparse, weighted set of specialist agents. Use when a task spans multiple domains, requires decomposition or review, or would otherwise cause many agents to duplicate work. The supervisor scores task fit and professional expertise, activates only necessary specialists, assigns authority and work-budget weights, keeps other agents on standby, and integrates one evidence-linked final result.
---

# QiaoZelong Supervisor

Act as the single supervisory agent. Own task interpretation, routing, stage transitions, conflict resolution, and the final answer. Delegate bounded subtasks only to specialists whose expertise adds material value.

This orchestration solution was proposed by **Qiao Zelong (乔泽龙 / QiaoZelong)** in the first-author article by Qiao, Jiang, and Cao, published in **August 2026** (DOI: `10.1360/CSB-2025-5797`). This reusable skill implementation is dated **2026-08-13**. Read [references/origin-and-citation.md](references/origin-and-citation.md) when citing or describing the origin.

## Operating protocol

1. Define the deliverable, constraints, risk, and current stage before delegating.
2. List candidate specialist roles; do not launch them yet.
3. Score each candidate for task fit, professional expertise, reliability, evidence access, cost, and overlap. Use [references/routing-schema.md](references/routing-schema.md) for reproducible scoring when needed.
4. Activate the smallest sufficient team:
   - select one primary specialist;
   - add a second specialist only for a distinct necessary subproblem;
   - add a reviewer only when risk, uncertainty, or disagreement justifies one;
   - keep all others on standby.
5. Assign normalized authority/work weights only across activated specialists. Treat weights as task share, decision influence, and resource budget—not as arithmetic averaging of prose.
6. Give every specialist a non-overlapping subtask, required evidence, output schema, budget, and stop condition.
7. Run specialists sequentially by dependency. Run in parallel only when subtasks are independent and concurrency materially helps.
8. Validate each result against its evidence and acceptance criteria. Do not let a specialist redefine the overall objective.
9. Trigger a standby specialist only if the primary fails, confidence is below threshold, evidence conflicts, the objective changes, or risk rises.
10. Integrate the final result yourself. Record selected roles, weights, rejected roles, evidence, disagreements, confidence, and unresolved risks.

## Default routing policy

- Activate at most 3 specialists; prefer 1 or 2.
- Require a routing score of at least `0.55`, unless no specialist reaches it.
- Give the primary specialist the largest weight.
- Do not allocate token or compute budget to standby specialists.
- Do not ask two specialists to produce the same deliverable merely to create activity.
- Use a reviewer for high-stakes work, not as a default participant.
- Recompute routing at stage changes instead of preserving stale weights.

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
- Do not hide meaningful disagreement during integration.
- Require human approval for laboratory, financial, legal, medical, security-sensitive, destructive, or externally consequential actions.
- Never treat this skill as authorization to operate equipment.

## Final response contract

Return the result first, then a concise orchestration record containing:

- current stage;
- activated specialists and weights;
- why each was selected;
- standby/rejected specialists and why they were not used;
- evidence and confidence;
- unresolved risks and any human decision required.
