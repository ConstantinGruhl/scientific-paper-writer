# Folder Workflow Index

Use this file as the manager's entry point for every folder-native run.

## Mode Selection

- Use `.paper_writer/workflows/normal.md` for the default guided workflow
- Use `.paper_writer/workflows/just_write_it.md` when `--just-write-it` is requested

Record the chosen mode in:

- `.paper_writer/project_brief.md`
- `.paper_writer/project_context.md`

## Manager Loop

1. Read the current brief, context, and status artifacts
2. Choose the next stage and success criteria
3. Split independent work into specialist tasks
4. Run parallel worker waves when available
5. Merge outputs into the canonical paper files
6. Run a checkpoint before advancing
7. Update status files and the user

## Visibility Layer

Keep these files current:

- `.paper_writer/agent_status.md`
- `.paper_writer/notes/<role>.md`
- `.paper_writer/notes/handoffs.md`
- `.paper_writer/project_context.md`
- `.paper_writer/agent_state.json`

## Parallelization Rules

- Prefer 2-4 workers in a wave
- Split by source family, topic branch, section cluster, or review dimension
- Avoid overlapping writes unless the manager is actively merging them

## Fallback Rule

If subagents are unavailable, simulate the same workflow sequentially in one thread while keeping the same stages and status artifacts.
