# Migration Plan

## Goal

Move existing markdown-first projects into the structured runtime without preserving markdown-only state as canonical.

## What Changes

- Canonical state moves to `.paper_writer/state/*.json`
- Existing markdown files become rendered views
- Export moves from markdown conversion to semantic rendering
- Validation moves from prompt reminders to code checks

## Migration Path

### New Projects

Use:

- `spw bootstrap <folder>`
- `spw init-project <slug>`

These create structured state from the start.

### Existing Folder-Native Workspaces

Use:

- `spw migrate <folder>`

or:

- `python scripts/migrate_legacy_workspace.py <folder>`

The migrator:

- creates `.paper_writer/state/`
- imports title and settings where possible
- imports draft sections into structured manuscript state
- preserves raw bibliography text as notes when it cannot be normalized automatically
- regenerates markdown views

### Existing Repo Projects Under `projects/`

Use the same migration command against the project root:

- `spw migrate projects/<slug>`

## Manual Follow-Up After Migration

- normalize bibliography note text into verified source records
- add evidence claims and source links
- add `coverage` records for substantial uncited prose before export
- review output mode and paper type selection
- run `spw validate`
- export only after validation passes

## Backward Compatibility

Preserved:

- familiar top-level markdown files
- notes and handoff artifacts
- legacy script entry points

Not preserved as canonical:

- markdown-only workflow state
- naive markdown export behavior
