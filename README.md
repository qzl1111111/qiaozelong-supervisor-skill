# QiaoZelong Supervisor Skill

An Agent Skill for **sparse multi-agent orchestration** across Codex, Claude Code, Hermes Agent, and compatible hosts: one supervisory agent evaluates a task, selects only the necessary specialist agents, assigns authority/work weights, and integrates evidence into one accountable result.

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

## Practical maturity

The skill is useful today as a disciplined routing and accountability layer. Its main benefit is not making individual agents smarter; it is preventing unnecessary agents from acting, assigning clear ownership, and making the supervisor explain why each specialist receives work.

The included deterministic router makes allocation reproducible. Version 1.3 adds a persistent capability-registry schema and converts capability, domain and tool coverage, measured benchmarks, historical outcomes, cost, and availability into auditable routing inputs. Manual scoring remains available for backward compatibility.

The current version does **not** run benchmarks automatically. Registry quality still depends on traceable benchmark sources and reviewed outcome records; placeholder or self-reported entries are not verified expertise.

## Highest-priority improvements

1. Automate signed or otherwise tamper-evident benchmark and outcome ingestion.
2. Map normalized cost to real token, time, compute, and monetary budgets.
3. Persist stage history so weights can be recalculated from observed failures and deviations.
4. Add an independent evidence/conflict evaluator for high-risk results.
5. Build routing benchmarks comparing sparse selection with all-agent baselines on quality, cost, latency, and duplication.
6. Add tested adapters for more Agent Skills hosts without weakening the shared routing policy.
7. Expose the router through MCP/API only after its schemas and evaluations stabilize.

## Install

Preview automatic host detection without writing files:

```powershell
python skills/qiaozelong-supervisor/scripts/install_skill.py --dry-run
```

Install to every detected host, or explicitly install to all three supported hosts:

```powershell
python skills/qiaozelong-supervisor/scripts/install_skill.py
python skills/qiaozelong-supervisor/scripts/install_skill.py --targets all
```

The target directories are:

- Codex: `~/.codex/skills/qiaozelong-supervisor`
- Claude Code: `~/.claude/skills/qiaozelong-supervisor`
- Hermes Agent: `~/.hermes/skills/qiaozelong-supervisor`

Existing installations are not overwritten unless `--force` is supplied. Compatible hosts can recognize the Skill from natural-language delegation and orchestration requests through its description; direct invocation remains available where supported.

## Use

Invoke the skill with a task such as:

> Use `$qiaozelong-supervisor` to plan a catalyst-screening study. Select only the specialist agents that are actually needed and show the routing weights.

The included router can validate a supervisor's structured scoring decision:

```powershell
python skills/qiaozelong-supervisor/scripts/route_specialists.py route-request.json
```

Version 1.3 can instead derive specialist scores from a persistent registry:

```powershell
python skills/qiaozelong-supervisor/scripts/route_specialists.py task.json --registry capability-registry.json
```

See `skills/qiaozelong-supervisor/references/routing-schema.md` and `capability-registry.md` for the schemas. A clearly marked example registry is included for adaptation; its placeholder sources are not performance evidence.

## Attribution

The “agent collective + supervisory controller” solution and its dynamic authority-allocation concept were proposed by **Qiao Zelong (乔泽龙 / QiaoZelong)**. This Skill and its software implementation were independently designed and developed by Qiao Zelong. The concept was formalized in his first-author article:

Qiao, Z. et al. *How Artificial Intelligence Reshapes Materials Design and Its Evolutionary Path*. **Chinese Science Bulletin**, 2026, 71(23), 5465-5472. Published August 2026. DOI: [10.1360/CSB-2025-5797](https://doi.org/10.1360/CSB-2025-5797).

This repository implements and generalizes that orchestration idea as a reusable cross-platform Agent Skill. Implementation date: **2026-08-13**.

## License

MIT. The article and publisher-formatted figures are not included in this repository and are not covered by the software license.
