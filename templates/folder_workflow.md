# Folder Workflow Index

Use this file as the manager's entry point for every folder-native run.

## Canonical State Rule

Treat `.paper_writer/state/` as canonical:

- `project.json`
- `workflow.json`
- `manuscript.json`
- `sources.json`
- `evidence.json`
- `reviews.json`
- `exports.json`

Markdown files are views for humans, not the source of truth.

## Mode Selection

- Use `.paper_writer/workflows/normal.md` for the default guided workflow.
- Use `.paper_writer/workflows/just_write_it.md` when `--just-write-it` is requested.

Record the chosen mode in structured state and refresh the rendered views.

## Manager Loop

1. Read canonical state and current views
2. Choose the next stage and success criteria
3. Split truly independent work into worker tasks
4. Run parallel worker waves when it improves outcomes
5. Merge results back into structured state
6. Run a checkpoint before advancing
7. Render views and update the user

## Visibility Layer

Keep these files current:

- `agent_status.md`
- `notes/<role>.md`
- `notes/handoffs.md`
- `project_context.md`
- `.paper_writer/state/workflow.json`
- `.paper_writer/state/trace.jsonl`

## Deterministic Commands

Use:

- `spw wordcount .`
- `spw validate .`
- `spw export .`

Do not treat export as complete unless validation passes.

## Parallelization Rules

- Prefer 2-4 workers in a wave when decomposition is genuinely useful.
- Split by source family, topic branch, section cluster, or review dimension.
- Avoid overlapping writes unless the manager is actively merging them.

## Fallback Rule

If subagents are unavailable, simulate the same workflow sequentially while keeping stage, checkpoint, and status artifacts current.
