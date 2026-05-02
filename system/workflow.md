# Workflow Index

This is the manager's entry point for every paper run.

## Canonical State First

Always read and update canonical state in `.paper_writer/state/` before treating markdown views as current.

Minimum state files:

- `project.json`
- `workflow.json`
- `manuscript.json`
- `sources.json`
- `evidence.json`
- `reviews.json`
- `exports.json`

Markdown files such as `project_brief.md`, `project_context.md`, and `draft.md` are rendered views for humans.

## Mode Selection

- Use `system/workflows/normal.md` for the default guided evidence-first workflow.
- Use `system/workflows/just_write_it.md` when the user explicitly requests `--just-write-it` or equivalent wording.

Record the selected mode in:

- `project.json`
- `workflow.json`
- the rendered project views

## Manager Loop

The manager should repeatedly:

1. Read canonical state and current rendered views
2. Decide the next stage and success criteria
3. Create explicit worker task objects only when decomposition is worthwhile
4. Run the work or delegate bounded slices
5. Merge the outputs back into canonical state
6. Run a checkpoint before stage advancement
7. Render views and give the user a brief status update

## Stages

1. `intake`
2. `research_plan`
3. `evidence`
4. `outline`
5. `drafting`
6. `review`
7. `export`
8. `completed`

## Parallelization Rules

- Parallelize only independent work.
- Prefer slices by section cluster, source family, review dimension, or evidence branch.
- Default to 2-4 workers in a wave when real parallelism helps.
- Avoid overlapping write ownership unless the manager is coordinating an immediate merge.
- When workers would conflict, use read-only analysis tasks and let the manager apply synthesis.

## Visibility Layer

Keep these artifacts current:

- `agent_status.md`
- `notes/<role>.md`
- `notes/handoffs.md`
- `project_context.md`
- `workflow.json`
- `trace.jsonl`

These are summaries and coordination artifacts, not raw reasoning dumps.

## Required Checkpoints

Run a checkpoint:

- after intake stabilizes
- after the research plan is credible
- before drafting
- before export
- whenever reviewer or auditor findings indicate drift

Each checkpoint should confirm:

- stage completion status
- evidence sufficiency
- unresolved blockers
- next owner
- whether the user needs an update

## Deterministic Gates

Use the runtime, not memory alone, for hard checks.

- `spw wordcount <project-root>`
- `spw validate <project-root>`
- `spw export <project-root>`

The manager should not mark review or export complete if deterministic validation fails.

## Role Map

- `manager`: orchestration, gating, synthesis
- `researcher`: source collection and evidence extraction
- `scientist`: methodology realism and claim calibration
- `source_checker`: citation fidelity and support audit
- `outliner`: structure and section planning
- `drafter`: section drafting
- `reviewer`: strict logical and evidence review
- `style_proofreader`: clarity and style
- `progress_auditor`: workflow adherence and status hygiene

## Fallback Rule

If subagents are unavailable, simulate the same workflow sequentially in one thread while preserving stages, checkpoints, and visible state updates.
