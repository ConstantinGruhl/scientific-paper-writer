# Workflow Index

This is the manager's entry point for every paper run.

## Mode Selection

- Use `system/workflows/normal.md` for the default guided evidence-first workflow.
- Use `system/workflows/just_write_it.md` when the user explicitly requests `--just-write-it` or equivalent wording.

Record the chosen mode in:

- `project_brief.md`
- `project_context.md`

## Manager Loop

The manager should repeatedly:

1. Read the current brief, context, and status artifacts
2. Decide the next stage and success criteria
3. Decompose the work into independent subtasks
4. Spawn specialist workers for parallel slices when subagents are available
5. Merge the outputs into the canonical project files
6. Run a checkpoint before advancing
7. Update the visibility layer and user-facing status

## Parallelization Rules

- Parallelize only independent work.
- Prefer slices by section, evidence cluster, method concern, or source family.
- Default to 2-4 workers in a wave.
- Avoid overlapping writes unless the manager is coordinating a merge step immediately after.
- When workers would otherwise conflict, assign them read-only analysis tasks and let the manager apply the synthesis.

## Visibility Layer

Keep these artifacts current:

- `agent_status.md`
- `notes/<role>.md`
- `notes/handoffs.md`
- `project_context.md`
- `agent_state.json` when supported

These are summaries and coordination artifacts, not raw internal reasoning dumps.

## Required Checkpoints

Run a checkpoint:

- after intake stabilizes
- after the research plan is credible
- before drafting
- before final export
- whenever a reviewer or auditor flags drift

Each checkpoint should confirm:

- stage completion
- evidence sufficiency
- unresolved blockers
- next owner
- whether the user needs an update

## Role Map

- `manager`: orchestration, gating, synthesis
- `researcher`: source collection and evidence extraction
- `scientist`: methodology realism and claim calibration
- `source_checker`: citation fidelity and support audit
- `outliner`: structure and section planning
- `drafter`: section drafting
- `reviewer`: strict logical and evidence review
- `style_proofreader`: clarity, tone, and formatting
- `progress_auditor`: workflow adherence and status hygiene

## Fallback Rule

If subagents are unavailable, simulate the same workflow sequentially in one thread while preserving the same stages, checkpoints, and status artifacts.
