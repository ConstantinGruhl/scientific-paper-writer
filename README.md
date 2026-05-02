# Scientific Paper Writer

Scientific Paper Writer is a file-first academic writing workflow that now combines inspectable project files with structured machine-readable state, deterministic validation, and professional export.

The repo began as a strong prompt-driven prototype. It is now redesigned around a small runtime package that enforces the critical guarantees in code instead of relying on markdown instructions alone.

## What It Guarantees Better Now

- structured workflow state with explicit stages, tasks, checkpoints, and trace events
- deterministic word counting with configurable policies and target validation
- paper-type defaults and formatting profiles selected by config
- raw text, formatted, or both output modes
- clean DOCX and PDF export from semantic structure rather than naive markdown conversion
- structured references, evidence links, and export-time validation
- visible markdown views that remain easy to inspect without being the only source of truth

## Core Product Principles

- file-first and inspectable
- evidence-first writing
- manager-led orchestration where it is genuinely useful
- structured canonical state plus rendered markdown views
- deterministic validation for hard constraints
- transparent, resumable workflow state

## Repository Layout

```text
.
|-- AGENTS.md
|-- context.md
|-- docs/
|-- projects/
|-- scripts/
|-- src/scientific_paper_writer/
|-- system/
|-- templates/
`-- tests/
```

Inside each project root:

```text
project-root/
|-- .paper_writer/
|   `-- state/
|       |-- project.json
|       |-- workflow.json
|       |-- manuscript.json
|       |-- sources.json
|       |-- evidence.json
|       |-- reviews.json
|       |-- exports.json
|       `-- trace.jsonl
|-- notes/
|-- sources/
|-- deliverables/
|-- project_brief.md
|-- project_context.md
|-- research_plan.md
|-- bibliography.md
|-- evidence_matrix.md
|-- outline.md
|-- draft.md
|-- revision_checklist.md
`-- agent_status.md
```

The `.paper_writer/state/` directory is canonical. The markdown files are rendered views for humans.

## Install

```powershell
python -m pip install -e .
```

This installs:

- `python-docx` for DOCX export
- `reportlab` for PDF export

## Command Interface

Main CLI:

```powershell
spw --help
```

Key commands:

```powershell
spw bootstrap C:\path\to\paper-folder --title "Working Title"
spw init-project my-paper --title "Working Title"
spw render-views projects\my-paper
spw wordcount projects\my-paper
spw validate projects\my-paper
spw scaffold-coverage projects\my-paper
spw export projects\my-paper
spw migrate projects\legacy-paper
```

Legacy script entry points still exist as wrappers:

- `python scripts/bootstrap_folder_workspace.py`
- `python scripts/init_paper_project.py`
- `python scripts/export_manuscript.py`
- `python scripts/build_prompt_packet.py`
- `python scripts/migrate_legacy_workspace.py`

## Output Modes

Output mode is now explicit project state, not an afterthought.

- `raw`: content-first text output
- `formatted`: DOCX and PDF deliverables
- `both`: raw text plus formatted deliverables

If no preference is supplied, the system defaults to `both`.

## Paper-Type Profiles

Built-in paper types:

- empirical / IMRaD paper
- literature review
- theoretical / conceptual paper
- case study
- thesis / dissertation chapter
- short conference paper

Profiles define:

- section order
- required sections
- default section budgets
- review checklist defaults
- default formatting profile
- default citation style

## Formatting Profiles

Built-in formatting profiles:

- `house_academic`
- `conference_compact`
- `thesis_classic`

They define:

- page size and margins
- fonts
- spacing
- heading behavior
- caption and table defaults
- reference layout

Institution-specific overrides can be merged on top later.
The resolved formatting snapshot is persisted in canonical project state so export uses the same effective configuration that bootstrap selected.

## References And Evidence

The system now supports:

- structured source records
- verified source flags
- claim-to-source links in `evidence.json`
- paragraph/block coverage records in `evidence.json["coverage"]`
- reviewable coverage statuses: `suggested` and `confirmed`
- citation tokens like `[@source-id]`
- formatted bibliography generation
- export blocking when cited sources are missing, unverified, or insufficiently covered

Use `spw scaffold-coverage` to create deterministic suggested coverage records for reviewable prose blocks that do not already have explicit coverage. The command preserves existing records, writes only `status: "suggested"` entries, and keeps final validation strict until any required records are confirmed.

Current formatted export enforces the core profile fields directly:

- page size and margins
- font family and size
- line spacing
- first-line paragraph indentation
- heading numbering
- caption styling
- table presentation
- reference hanging-indent layout

## Figures And Visual Material

Figure support is structured and safety-aware.

- `figure_mode`: `off`, `suggest_only`, or `auto`
- figure metadata lives in `evidence.json`
- figure markers are resolved from structured metadata
- unresolved figure markers block clean export
- conceptual figures and evidence-bearing visuals can be distinguished explicitly

## Deterministic Word Count

Word counting is policy-driven and does not rely on AI.

Supported controls:

- exact target
- minimum/maximum range
- target plus or minus tolerance

Configurable inclusions:

- title
- abstract
- headings
- figure captions
- tables
- references
- appendices

Use:

```powershell
spw wordcount projects\my-paper
```

## Validation And Export Gates

Use:

```powershell
spw validate projects\my-paper
```

When you want help scaffolding explicit coverage before review, run:

```powershell
spw scaffold-coverage projects\my-paper
```

Validation checks include:

- word-count compliance
- unresolved TODO or markdown artifact markers
- missing or unverified cited sources
- missing claim-to-evidence links
- substantial argumentative passages without coverage classification

Suggested coverage records remain review prompts only. They are visible in `evidence.json` and `evidence_matrix.md`, but they do not satisfy export readiness on their own.

Export now fails fast when validation does not pass.

## Tests

Run:

```powershell
python -m unittest discover -s tests -v
```

Current tests cover:

- deterministic word counting
- section budget diagnostics
- nested subsection and appendix rollups
- figure-caption and table-count policy toggles
- citation formatting
- artifact detection
- evidence coverage validation
- formatting override persistence into export
- end-to-end export smoke behavior

## Redesign Docs

- [Redesign spec](docs/superpowers/specs/2026-05-02-scientific-paper-writer-redesign-design.md)
- [Gap analysis](docs/redesign-gap-analysis.md)
- [Migration plan](docs/migration-plan.md)

## Current Limitations

- bibliography formatting is structured and tested, but not yet a full CSL engine
- institution-specific formatting overrides are JSON merges, not a full template-ingestion system
- back-matter profile fields remain conservative and do not yet provide a fully custom ordering engine
- workflow orchestration is now structured, but AI worker execution still depends on the surrounding assistant platform

## License

MIT. See [LICENSE](LICENSE).
