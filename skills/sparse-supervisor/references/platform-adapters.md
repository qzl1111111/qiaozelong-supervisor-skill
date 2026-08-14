# Platform adapters

Use the same routing policy on every host. Platform adapters only translate an activated routing plan into the host's available delegation mechanism; they must not change selection scores or activate standby specialists.

## Automatic recognition

Codex, Claude Code, and Hermes index the Skill's `name` and `description`. The shared description includes delegation, orchestration, expert-team, multi-domain, duplicate-work, and risk-review triggers so compatible hosts can load it from natural-language requests. Direct invocation remains available when a host supports it.

Automatic recognition means the host can discover and choose the Skill. It does not mean the router can infer verified expertise without capability evidence.

## Codex

- Install under `~/.codex/skills/sparse-supervisor/`.
- When collaboration/subagent tools are exposed, create only agents listed in `activated`.
- Keep the root agent as supervisor and final integrator.
- Do not spawn agents for `supervisor_only` or `blocked` plans.

## Claude Code

- Install under `~/.claude/skills/sparse-supervisor/`.
- Claude Code can automatically load project or personal skills from its skills directories.
- Use available subagent or agent-team capabilities only for `activated` roles. Tool names and team features may vary by Claude Code version and configuration.
- If no delegation capability is available, execute activated roles sequentially in the main session and disclose that limitation.
- Use Claude permissions and hooks when policy must be enforced beyond model instructions.

## Hermes Agent

- Install under `~/.hermes/skills/sparse-supervisor/`, or install the repository's raw `SKILL.md` using Hermes skill commands.
- Hermes exposes installed skills as slash commands and may select them from natural-language requests.
- Use `delegate_task` only for roles listed in `activated`; do not delegate standby roles.
- Respect Hermes toolset configuration and skill-write approval settings.
- If delegation is disabled, execute the selected roles sequentially and disclose that no isolated agents were created.

## Other Agent Skills hosts

Install the `sparse-supervisor` folder in the host's Agent Skills directory. The portable layer requires only `SKILL.md`, references, and the standard-library router. Unknown hosts should default to sequential execution rather than guessing a delegation API.

## Enforcement boundary

The Skill influences agent behavior, while `route_specialists.py` deterministically validates routing plans. Neither can sandbox tools or block unauthorized actions by itself. Use the host's permission system, approvals, hooks, containers, or tool allowlists for hard enforcement.
