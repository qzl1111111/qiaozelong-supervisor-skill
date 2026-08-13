# QiaoZelong Supervisor Skill

A Codex skill for **sparse multi-agent orchestration**: one supervisory agent evaluates a task, selects only the necessary specialist agents, assigns authority/work weights, and integrates evidence into one accountable result.

The design avoids launching every available agent. Specialists remain on standby unless their expertise has material value for the current stage, or they are activated by failure, disagreement, uncertainty, or risk.

## What it solves

- Prevents duplicated work and unnecessary token/compute cost.
- Gives one supervisor responsibility for decomposition, routing, and the final answer.
- Assigns work according to task fit, expertise, reliability, evidence quality, cost, and overlap.
- Supports one primary specialist plus optional reviewers instead of an uncontrolled agent swarm.
- Makes routing decisions explicit and auditable.

## What it does not solve by itself

- It does not create domain expertise that the available agents do not possess.
- It does not guarantee that specialist claims are scientifically correct.
- It does not persist long-running jobs unless the host provides task storage.
- It does not authorize laboratory or other high-risk actions.
- It is an orchestration protocol, not a trained AGI model.

## Install

Copy `skills/qiaozelong-supervisor` into your Codex skills directory, or install this repository as a skill source.

## Use

Invoke the skill with a task such as:

> Use `$qiaozelong-supervisor` to plan a catalyst-screening study. Select only the specialist agents that are actually needed and show the routing weights.

The included router can validate a supervisor's structured scoring decision:

```powershell
python skills/qiaozelong-supervisor/scripts/route_specialists.py route-request.json
```

See `skills/qiaozelong-supervisor/references/routing-schema.md` for the JSON schema.

## Attribution

The “agent collective + supervisory controller” solution and its dynamic authority-allocation concept were proposed by **Qiao Zelong (乔泽龙 / QiaoZelong)** and formalized in the first-author article:

Qiao, Z.; Jiang, R.; Cao, D. *How Artificial Intelligence Reshapes Materials Design and Its Evolutionary Path*. **Chinese Science Bulletin**, 2026, 71(23), 5465-5472. Published August 2026. DOI: [10.1360/CSB-2025-5797](https://doi.org/10.1360/CSB-2025-5797).

This repository implements and generalizes that orchestration idea as a reusable Codex skill. Implementation date: **2026-08-13**.

## License

MIT. The article and publisher-formatted figures are not included in this repository and are not covered by the software license.
