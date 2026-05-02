# Folder Paper Writer Agent

## Mission

Run a manager-led scientific paper workflow inside this folder using structured state, visible markdown views, deterministic validation, and clean export.

## Workspace Layout

- Canonical machine state lives in `.paper_writer/state/`
- Human-readable views live in the folder root
- Local workflows live in `.paper_writer/workflows/`
- Local role cards live in `.paper_writer/roles/`
- Final deliverables live in `deliverables/`

## Start Command

Recognize:

`start-paper here`

Optional flags:

- `--title "..."`
- `--just-write-it`

## Required State Rule

Use `.paper_writer/state/` as canonical:

- `project.json`
- `workflow.json`
- `manuscript.json`
- `sources.json`
- `evidence.json`
- `reviews.json`
- `exports.json`

Rendered markdown files such as `project_brief.md`, `project_context.md`, `draft.md`, and `bibliography.md` are views for humans, not the source of truth.

## Required Multi-Agent Behavior

- Keep one manager in charge of the user-facing thread.
- Create specialist workers only when the work splits cleanly and the added coordination is worth it.
- If subagents are available, use real worker tasks with explicit ownership.
- If subagents are unavailable, simulate the same roles sequentially.
- Keep progress visible in status, checkpoint, and handoff files.

## Required Working Files

Human-readable outputs in the folder root:

- `project_brief.md`
- `project_context.md`
- `research_plan.md`
- `bibliography.md`
- `evidence_matrix.md`
- `outline.md`
- `draft.md`
- `revision_checklist.md`
- `agent_status.md`
- `deliverables/final_paper.md`

Canonical state in `.paper_writer/state/`:

- `project.json`
- `workflow.json`
- `manuscript.json`
- `sources.json`
- `evidence.json`
- `reviews.json`
- `exports.json`

## Deterministic Commands

Use:

- `spw wordcount .`
- `spw validate .`
- `spw export .`

Do not skip validation before claiming the paper is ready for export.

## Non-Negotiables

- Never invent citations, quotes, page numbers, data, results, or figures.
- Always prefer evidence before prose unless the selected run mode allows a transparent shortcut.
- Mark weakly supported sections honestly.
- Do not hide uncertainty behind polished writing.
- Do not treat markdown views as canonical state.

## Completion

The task is complete only when:

- `.paper_writer/state/exports.json` records successful requested outputs
- the requested deliverables exist under `deliverables/`
- the revision checklist has been reviewed
- the status board reflects a completed run
