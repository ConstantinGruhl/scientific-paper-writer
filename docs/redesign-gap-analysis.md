# Redesign Gap Analysis

## Current Prototype Strengths

- File-first and easy to inspect
- Evidence-first in intent
- Manager-led orchestration model
- Visible progress artifacts
- Supports guided and faster autonomous workflow modes

## Gaps Against The Target System

### Workflow Engine

Current state:

- Markdown workflow instructions plus a shallow `agent_state.json`

Gap:

- No real stage machine
- No deterministic stage gates
- No resumable task objects
- No explicit blocked or partial outcomes

Redesign answer:

- `.paper_writer/state/workflow.json`
- explicit stages, tasks, checkpoints, and trace events

### Structured Project State

Current state:

- Markdown files act as both user views and system state

Gap:

- Machine enforcement is weak
- Workflow cannot validate completeness reliably

Redesign answer:

- canonical JSON state under `.paper_writer/state/`
- markdown files rendered as human-readable projections

### Word Count

Current state:

- no deterministic word-count engine

Gap:

- cannot enforce compliance or budget drift

Redesign answer:

- policy-driven word counting from normalized plain text
- bucket counts, section counts, subsection counts, and budget diagnostics

### Output Modes

Current state:

- output choice is mainly export format

Gap:

- raw vs formatted intent is not modeled

Redesign answer:

- explicit `output_mode` in structured state
- `raw`, `formatted`, and `both`

### Formatting And Profiles

Current state:

- formatting is implicit and under-specified

Gap:

- no paper-type defaults
- no profile-driven formatting
- no institution override model

Redesign answer:

- paper-type profiles
- formatting profiles
- citation profiles
- optional override merge

### Export Quality

Current state:

- naive markdown conversion to DOCX or LaTeX

Gap:

- markdown artifacts can leak
- PDF is not first-class
- professional layout is not guaranteed

Redesign answer:

- semantic rendering pipeline
- DOCX via `python-docx`
- PDF via `reportlab`
- export validation gate

### References And Evidence

Current state:

- bibliography is text-first

Gap:

- no normalized source registry
- no reliable claim-to-source mapping

Redesign answer:

- structured source records
- citation token rendering
- evidence registry
- verified-source validation

### Figures

Current state:

- no structured figure support

Gap:

- no metadata, placement, or integrity rules

Redesign answer:

- structured figure records
- figure marker resolution
- caption support
- export rendering hooks

### Testing And Evals

Current state:

- no meaningful tests

Gap:

- quality cannot be measured or reproduced

Redesign answer:

- unit tests
- export smoke test
- validation reports
- trace logging
