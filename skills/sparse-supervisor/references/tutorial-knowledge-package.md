# Tutorial Knowledge Package standard

Use this standard to turn one heterogeneous tutorial into a portable, mergeable knowledge package. Keep original files outside the package and immutable. Never use a single large summary as the canonical knowledge store.

## Design goals

- Preserve exact provenance from every knowledge claim to a source location.
- Process large collections incrementally without loading the whole corpus into one model context.
- Deduplicate without deleting disagreements or source-specific variants.
- Support PDFs, presentations, Word files, spreadsheets, scripts, notebooks, images, audio, video, archives, and plain text.
- Let humans, language models, search systems, and the expert knowledge base use the same output.

## Package layout

```text
tutorial-packages/
└── <package-id>/
    ├── package.json
    ├── inventory.jsonl
    ├── extracted/                    # optional intermediate artifacts
    │   └── <source-id>/...
    ├── units/
    │   ├── part-0001.jsonl
    │   └── part-0002.jsonl
    ├── summaries/
    │   └── course-overview.md
    ├── mappings/
    │   └── expert-units.jsonl
    ├── merge/
    │   └── decisions.jsonl
    └── qa/
        └── report.json
```

The canonical reusable content is `units/*.jsonl`. Summaries and expert mappings are derived views and may be regenerated.

Initialize one package from one tutorial directory with deterministic file hashes:

```powershell
python scripts/init_tutorial_package.py path/to/one-tutorial path/to/tutorial-packages --package-id crystallography-course-01 --title "Crystallography Course 01"
```

The initializer inventories files but does not parse or copy them. Keep the source directory unchanged and available while extraction is performed.

## `package.json`

```json
{
  "schema_version": "1.0",
  "package_id": "crystallography-course-01",
  "title": "Tutorial title",
  "version": "1.0.0",
  "status": "draft",
  "languages": ["zh-CN", "en"],
  "created_at": "2026-08-14",
  "updated_at": "2026-08-14",
  "description": "What this tutorial covers.",
  "scope": ["crystallography", "structure-analysis"],
  "unit_shard_max_bytes": 5242880,
  "unit_shard_max_records": 500
}
```

Allowed status values are `draft`, `review`, `approved`, and `superseded`. Publish a new package version when source files or scientific interpretation change; do not silently rewrite an approved package.

## `inventory.jsonl`

Write one UTF-8 JSON object per source file. Compute SHA-256 with software rather than asking a language model to invent it.

```json
{"source_id":"src_a1b2c3d4e5f60708","relative_path":"slides/chapter-01.pptx","sha256":"64-lowercase-hex-characters","size_bytes":123456,"media_type":"application/vnd.openxmlformats-officedocument.presentationml.presentation","source_role":"primary-tutorial","extraction_status":"complete","extracted_artifacts":[{"path":"extracted/src_a1b2c3d4e5f60708/slides.md","kind":"normalized-text"}],"warnings":[]}
```

Set `source_id` to `src_` plus the first 16 characters of the file SHA-256. Use relative paths only. `extraction_status` is `pending`, `partial`, `complete`, `failed`, or `not-needed`.

## Source locators

Every factual claim must point to a source and a location using these conventions:

| Type | Locator example |
|---|---|
| PDF | `page=12;section=2.1` |
| PPT/PPTX | `slide=8;shape=title-and-body` |
| DOC/DOCX | `heading=Unit Cell;paragraph=4` |
| XLS/XLSX/CSV | `sheet=Data;range=A2:F28` |
| Script/notebook | `path=src/refine.py;lines=40-88;symbol=refine_cell` |
| Image | `image=figure-03;region=top-right` |
| Audio/video | `time=00:13:20-00:15:05` |
| Plain text | `heading=Example;lines=120-168` |

If pagination or line numbers are unstable, include a heading, sheet, symbol, slide, cell range, timestamp, or other reproducible anchor.

## Atomic knowledge unit

Write one unit per JSONL line. A unit should express one concept, procedure, formula, warning, troubleshooting rule, data interpretation, or code pattern. Target roughly 300–1200 tokens; split units larger than 2000 tokens.

```json
{
  "schema_version": "1.0",
  "unit_id": "ku_crystallography-course-01_000001",
  "package_id": "crystallography-course-01",
  "title": "Reciprocal lattice definition",
  "domain_path": ["crystallography", "reciprocal-space"],
  "knowledge_type": "concept",
  "summary": "A concise self-contained explanation.",
  "claims": [
    {
      "claim_id": "C1",
      "text": "A precise factual or procedural statement.",
      "evidence": [
        {
          "source_id": "src_a1b2c3d4e5f60708",
          "locator": "slide=8",
          "evidence_excerpt": "Short excerpt or faithful description, not a long copyrighted passage."
        }
      ]
    }
  ],
  "prerequisites": ["ku_crystallography-course-01_000000"],
  "keywords": ["reciprocal lattice", "倒易点阵"],
  "applicability": ["single-crystal diffraction"],
  "limitations": ["Convention-dependent notation must be stated"],
  "relations": [
    {"type": "related-to", "target_unit_id": "ku_external_or_local", "note": "Relationship explanation"}
  ],
  "merge_key": "crystallography/reciprocal-lattice/definition",
  "status": "active",
  "supersedes": [],
  "review": {
    "status": "needs-review",
    "confidence": 0.8,
    "reviewer": "",
    "notes": ""
  }
}
```

Allowed `knowledge_type` values:

- `concept`
- `procedure`
- `formula`
- `method`
- `example`
- `warning`
- `troubleshooting`
- `data-interpretation`
- `code-pattern`
- `terminology`

Allowed unit status values are `active`, `deprecated`, and `superseded`. Allowed review status values are `needs-review`, `model-reviewed`, and `human-reviewed`.

Do not average incompatible definitions, formulas, conventions, or scientific conclusions. Create separate units and link them using `contradicts`, `alternative-to`, or `convention-variant` relations.

## Course overview

`summaries/course-overview.md` is a derived human-readable guide. Include:

1. scope and intended audience;
2. source coverage and extraction failures;
3. topic hierarchy;
4. prerequisite graph in prose;
5. key concepts and procedures with unit IDs;
6. important formulas, units, and conventions;
7. limitations, contradictions, and unresolved questions;
8. suggested expert mappings.

Do not introduce facts that do not exist in a knowledge unit.

## Expert mapping

Write one mapping per JSONL line:

```json
{"unit_id":"ku_crystallography-course-01_000001","expert_id":"materials-theory","role":"core","relevance":0.95,"reason":"Required for reciprocal-space interpretation","status":"candidate"}
```

Allowed roles are `core`, `support`, `procedure`, `warning`, and `reference`. Mapping status is `candidate`, `approved`, or `rejected`. A candidate mapping does not modify the expert knowledge base; approval is a separate review step.

## Merge decisions

Never overwrite original package units. Record intrapackage or cross-package decisions as JSONL:

```json
{"cluster_id":"cluster_000001","action":"merge","canonical_unit_id":"ku_course-a_000010","member_unit_ids":["ku_course-a_000010","ku_course-b_000044"],"rationale":"Same definition and convention","conflicts":[],"status":"needs-review"}
```

Allowed actions are `keep-separate`, `merge`, `related`, `conflict`, and `supersede`. Preserve every member ID and its source evidence. Exact hashes can identify byte duplicates; semantic similarity only proposes a cluster and never authorizes deletion.

## QA report

`qa/report.json` records counts and unresolved issues:

```json
{
  "schema_version": "1.0",
  "package_id": "crystallography-course-01",
  "inventory_records": 1,
  "knowledge_units": 1,
  "units_without_evidence": 0,
  "unknown_source_references": 0,
  "extraction_failures": 0,
  "duplicate_candidates": 0,
  "conflict_clusters": 0,
  "unresolved_items": [],
  "validation_status": "pass"
}
```

The validator calculates structural counts independently. A model-written `pass` value is not proof of validity.

## Scale and sharding rules

- Process one source file or one logical section at a time; never ask a model to synthesize the entire 1.7 GB collection in one context.
- Limit each knowledge-unit shard to 5 MiB or 500 records, whichever comes first.
- Keep one unit below 2000 tokens and one topic summary below roughly 20,000 tokens.
- Split extracted content by chapter, heading, slide range, worksheet, function, or time range.
- Stream JSONL line by line. Do not load all units into memory for validation or merging.
- Keep large images, raw tables, binaries, and full extracted text outside the canonical unit files; reference them by relative path and source locator.

## File-type requirements

- PDF: preserve page anchors; flag OCR and scanned pages; describe figures needed for interpretation.
- PPT/PPTX: preserve slide numbers, speaker notes, diagrams, and build-dependent meaning.
- DOC/DOCX: preserve heading hierarchy, tables, captions, footnotes, and tracked uncertainty.
- Excel/CSV: preserve sheet names, ranges, formulas, units, missing-value semantics, and whether values are calculated or literal.
- Code/notebooks: preserve paths, symbols, dependencies, inputs, outputs, side effects, assumptions, and line/cell anchors.
- Images: retain captions, labels, axes, legends, scale bars, and uncertainty about unreadable details.
- Audio/video: use timestamps and distinguish transcript content from visual demonstration.

## Integration with expert knowledge bases

After review, select approved units by `expert_id`, domain, capability, and role. Convert them into the expert Markdown structure or let retrieval load the units directly. Keep unit IDs and evidence links in the expert entry so later package updates can be traced, compared, and rolled back.
