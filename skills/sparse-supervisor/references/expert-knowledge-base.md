# Expert knowledge-base format

Keep routing evidence and expert knowledge separate:

- `capability-registry.json` answers **which expert should work**.
- the expert knowledge base answers **what grounded knowledge that expert may use**.

## Directory layout

```text
knowledge-base/
├── materials-theory/
│   ├── expert.json
│   ├── knowledge.md
│   └── procedures.md          # optional
└── evidence-review/
    ├── expert.json
    └── knowledge.md
```

Use a stable lowercase `expert_id` containing letters, digits, and hyphens. Use the same value as the corresponding capability-registry specialist `name` when the records refer to the same expert.

## `expert.json`

```json
{
  "schema_version": "1.0",
  "expert_id": "materials-theory",
  "display_name": "Materials Theory Expert",
  "summary": "Evaluates theoretical materials hypotheses and simulation evidence.",
  "domains": ["materials-science"],
  "capabilities": ["theory", "simulation-review"],
  "knowledge_files": ["knowledge.md", "procedures.md"],
  "languages": ["zh-CN", "en"],
  "updated_at": "2026-08-14",
  "review_after": "2027-02-14",
  "limitations": ["Does not control laboratory equipment"],
  "escalation_triggers": ["Evidence conflicts with safety constraints"],
  "sources": [
    {
      "id": "S1",
      "title": "Full source title",
      "type": "paper",
      "locator": "https://doi.org/...",
      "published_at": "2025-01-01",
      "accessed_at": "2026-08-14",
      "authority": "primary"
    }
  ]
}
```

Required fields are `schema_version`, `expert_id`, `display_name`, `summary`, `domains`, `capabilities`, `knowledge_files`, `updated_at`, `limitations`, `escalation_triggers`, and `sources`. Every source needs a unique `id`, title, type, locator, and authority. Allowed authority values are `primary`, `official`, `review`, and `internal-reviewed`.

Do not put passwords, API keys, private personal data, unpublished confidential information, or copyrighted full-text articles in the knowledge base. Store citations and your own concise synthesis instead.

## Knowledge Markdown

Use this fixed section order so different hosts can retrieve content consistently:

```markdown
# Expert knowledge

## Scope
What this expert covers and does not cover.

## Core knowledge
- A concise, testable statement. [S1]

## Decision rules
1. If condition X holds, perform Y; record assumption Z. [S1]

## Workflow
1. Required inputs
2. Analysis steps
3. Acceptance criteria
4. Output fields

## Evidence standards
Which evidence is acceptable, preferred, or insufficient.

## Known limitations
Failure modes, uncertainty, temporal limits, and prohibited inference.

## Escalation triggers
Conditions requiring another expert, fresh evidence, or human approval.

## Terminology
- Term: operational definition.
```

Use source IDs such as `[S1]` after claims. Distinguish measured facts, expert heuristics, and assumptions. Give numerical values units and applicable conditions. Prefer small topic files over one very large file; list every loaded file in `knowledge_files`.

## Authoring workflow

1. Copy `knowledge-base-template/expert-template/` once per expert.
2. Rename the directory and set a matching `expert_id`.
3. Replace every `REPLACE_ME` marker.
4. Write concise synthesis in Markdown and attach source IDs to factual claims.
5. Run `validate_knowledge_base.py`.
6. Have a domain reviewer inspect scientific correctness before using the entry for consequential work.

The validator checks structure, paths, source IDs, dates, required headings, unresolved placeholders, and missing source references. It does not prove that the knowledge is true.
