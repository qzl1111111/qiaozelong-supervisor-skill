# Sparse Supervisor

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

The included deterministic router makes allocation reproducible. Version 2.0 uses a neutral project identity and combines a portable Skill, Python routing components, an evidence-backed capability registry, and a validated expert knowledge-base format. Manual scoring remains available for backward compatibility.

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
python skills/sparse-supervisor/scripts/install_skill.py --dry-run
```

Install to every detected host, or explicitly install to all three supported hosts:

```powershell
python skills/sparse-supervisor/scripts/install_skill.py
python skills/sparse-supervisor/scripts/install_skill.py --targets all
```

The target directories are:

- Codex: `~/.codex/skills/sparse-supervisor`
- Claude Code: `~/.claude/skills/sparse-supervisor`
- Hermes Agent: `~/.hermes/skills/sparse-supervisor`

Existing installations are not overwritten unless `--force` is supplied. Compatible hosts can recognize the Skill from natural-language delegation and orchestration requests through its description; direct invocation remains available where supported.

## Use

Invoke the skill with a task such as:

> Use `$sparse-supervisor` to plan a catalyst-screening study. Select only the specialist agents that are actually needed and show the routing weights.

The included router can validate a supervisor's structured scoring decision:

```powershell
python skills/sparse-supervisor/scripts/route_specialists.py route-request.json
```

The router can instead derive specialist scores from a persistent registry:

```powershell
python skills/sparse-supervisor/scripts/route_specialists.py task.json --registry capability-registry.json
```

See `skills/sparse-supervisor/references/routing-schema.md` and `capability-registry.md` for the schemas. A clearly marked example registry is included for adaptation; its placeholder sources are not performance evidence.

## Expert knowledge base

Write one directory per expert containing `expert.json` and one or more Markdown knowledge files. Start with the templates in `knowledge-base-template/` and validate your completed directory with:

```powershell
python skills/sparse-supervisor/scripts/validate_knowledge_base.py path/to/knowledge-base
```

The complete authoring format is in `skills/sparse-supervisor/references/expert-knowledge-base.md`.

For large mixed-format tutorial collections, first convert each tutorial into an independent Tutorial Knowledge Package. This preserves source locations, supports JSONL sharding and later deduplication, and keeps expert mapping separate from extraction:

- `skills/sparse-supervisor/references/tutorial-knowledge-package.md`: package specification;
- `skills/sparse-supervisor/references/luna-tutorial-ingestion-instructions.md`: strict model instructions;
- `tutorial-package-template/`: editable output template.

Tutorial sources, extracted full text, and generated knowledge packages are local-only by default. The repository ignores the recommended raw and working directories. No model or tool may upload any tutorial-related file without explicit approval for the exact reviewed files and destination. Public-derived summaries require a separate safety review; removing author names alone does not remove copyright.

Validate a completed tutorial package with:

```powershell
python skills/sparse-supervisor/scripts/validate_tutorial_package.py path/to/tutorial-package
```

Initialize a package and hash its source files before giving it to a model:

```powershell
python skills/sparse-supervisor/scripts/init_tutorial_package.py path/to/one-tutorial path/to/tutorial-packages --package-id tutorial-01 --title "Tutorial 01"
```

Check a separately prepared public-derived candidate without uploading it:

```powershell
python skills/sparse-supervisor/scripts/check_publication_safety.py path/to/public-export-candidate
```

A clean check only means “ready for human review.” Upload still requires explicit approval for the exact files and destination.

## Migration from v1

The project and Skill identifier changed to `sparse-supervisor`. Install v2 in its new directory, verify it, then manually remove the legacy `qiaozelong-supervisor` installation. The installer reports legacy copies but never deletes them automatically.

## Citation

Qiao, Z. et al. *How Artificial Intelligence Reshapes Materials Design and Its Evolutionary Path*. **Chinese Science Bulletin**, 2026, 71(23), 5465-5472. Published August 2026. DOI: [10.1360/CSB-2025-5797](https://doi.org/10.1360/CSB-2025-5797).

## License

MIT. The article and publisher-formatted figures are not included in this repository and are not covered by the software license.

By QiaoZelong.
