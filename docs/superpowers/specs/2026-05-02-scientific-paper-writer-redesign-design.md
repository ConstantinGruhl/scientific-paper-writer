# Scientific Paper Writer Redesign Spec

Date: 2026-05-02
Status: Accepted for implementation
Scope: Repository-wide redesign from prompt-driven scaffold to structured workflow system

## 1. Why The Current Repo Is A Good Prototype But Not Robust Enough

The current repository gets several important product choices right:

- It is file-first and easy to inspect.
- It treats evidence tracking as a first-class concern.
- It uses a manager-led orchestration model instead of a single monolithic prompt.
- It keeps visible artifacts such as `agent_status.md`, notes, briefs, and draft files.
- It supports both guided and faster autonomous working modes.

Those strengths make it a strong prototype in spirit. The problem is that most guarantees currently depend on prompt compliance instead of machine-enforced state and validation.

Observed limitations in the current implementation:

- Canonical workflow state lives primarily in markdown files.
- `agent_state.json` exists, but it is too shallow to function as a real workflow engine.
- The export path is a naive markdown conversion pipeline that cannot guarantee professional DOCX/PDF output or prevent markdown artifact leakage.
- There is no deterministic word counting or section budgeting system.
- There is no structured reference registry or claim-to-evidence validation layer.
- There are no meaningful tests or reproducible evals.

The redesign therefore keeps the file-first workspace and visible artifacts, but moves core invariants into code, structured state, and tests.

## 2. Product Goals

The redesigned system must reliably:

- plan and draft papers
- track evidence and citations
- enforce word counts deterministically
- support raw-text vs formatted output modes
- generate professional DOCX and PDF outputs without markdown artifacts
- use sensible default formatting profiles by paper type when no institution template is provided
- optionally include figures and graphics when appropriate
- remain transparent, resumable, testable, and inspectable

Non-negotiables:

- never fabricate sources, quotes, page numbers, DOI values, data, or figures
- never present unsupported claims as settled fact
- prefer deterministic validation over prompt-only reminders
- preserve human-readable markdown views, but do not let them remain the only source of truth

## 3. Recommended Architecture

Recommended approach: a hybrid structured core with rendered markdown views.

Why this approach:

- It preserves file-first inspectability.
- It creates real machine-readable state without introducing a heavyweight database.
- It supports deterministic validation and resumable orchestration.
- It keeps the system pleasant to inspect and edit.

Rejected alternatives:

- Markdown-canonical with extra validators: too weak for stage gates, word counting, and export cleanliness.
- Heavy framework or database orchestration system: unnecessary complexity for a repository-first workflow tool.

## 4. System Layers

The redesign introduces six explicit layers.

### 4.1 Orchestration Layer

Responsibilities:

- stage machine
- task tracking
- checkpoints
- blocked/partial/success outcomes
- trace logging
- worker task ownership records

Key behavior:

- explicit stages
- explicit stage gates
- resumability from saved workflow state
- manager-controlled advancement
- worker tasks recorded as structured objects

### 4.2 Structured Project State Layer

The canonical project state lives under `.paper_writer/state/` inside each project root.

Canonical files:

- `project.json`
- `workflow.json`
- `manuscript.json`
- `sources.json`
- `evidence.json`
- `reviews.json`
- `exports.json`
- `trace.jsonl`

These files store machine-readable state for:

- project metadata
- paper type
- output mode
- target word count and count policy
- formatting profile
- citation profile
- source metadata
- claims/evidence links
- tasks/checkpoints/progress
- review findings
- export results
- figure metadata

Markdown files remain human-readable projections of this state, not the source of truth.

### 4.3 Manuscript Content And Evidence Layer

Canonical manuscript state is structured by section rather than by one freeform markdown blob.

The manuscript model stores:

- title
- abstract
- keywords
- ordered sections and subsections
- per-section content
- structured figure placements
- appendix content

Internal authoring content may still use constrained markdown at the section body level, but export must first parse it into a semantic document model. Export must never be a naive string conversion.

Evidence state is separate from draft text:

- claims are tracked as explicit records
- each claim maps to one or more supporting source IDs
- unsupported claims remain visibly unresolved until fixed or explicitly marked

### 4.4 Formatting And Profile Layer

Formatting is separated from content.

Profiles include:

- paper type profiles
- formatting profiles
- citation style profiles
- optional institution override files

Paper type profiles define:

- section order
- required and optional sections
- abstract and keyword expectations
- default section word budgets
- figure and table expectations
- default review checklist rules
- export structure defaults

Formatting profiles define:

- page size
- margins
- fonts
- line spacing
- paragraph indentation
- heading hierarchy
- caption styling
- table styling
- reference section behavior
- front matter and back matter rules

Institution overrides merge on top of defaults instead of replacing the whole system.

### 4.5 Export And Rendering Layer

Export is driven by a semantic manuscript model, not by raw markdown conversion.

Supported deliverable modes:

- raw text
- formatted
- both

Raw text deliverables:

- normalized content-first manuscript output with minimal presentation assumptions

Formatted deliverables:

- DOCX
- PDF

Formatted exports must:

- render real headings
- render real lists
- render figure/table captions
- format references cleanly
- apply intentional page and section breaks
- reject unresolved markdown artifacts before export succeeds

### 4.6 QA And Eval Layer

The QA layer provides:

- deterministic validators
- export linting
- word-count checks
- citation/reference checks
- stage-gate checks
- smoke tests
- measurable eval outputs

## 5. Workflow Engine Design

The workflow engine is a small, explicit state machine.

Primary stages:

1. intake
2. research_plan
3. evidence
4. outline
5. drafting
6. review
7. export
8. completed

Each stage stores:

- status
- owner
- started/completed timestamps
- gate criteria
- outcome
- blocker text if blocked

Worker tasks are explicit objects with:

- ID
- role
- description
- owned files or state slices
- status
- outcome
- blocker
- timestamps

Checkpoint records capture:

- checkpoint ID
- stage
- pass/partial/fail status
- unresolved risks
- next owner
- user-visible summary

The manager remains useful, but its authority becomes operationally real because stage advancement and completion are code-recorded.

## 6. Word Count Must Be Deterministic And Policy-Driven

Word count cannot depend on AI because it is a hard compliance requirement in academic work.

The system therefore counts words from a normalized plain-text representation derived from the semantic manuscript model.

Counting policy is configurable per project.

Configurable inclusions:

- title
- abstract
- headings
- figure captions
- tables
- references
- appendices

Default:

- references excluded unless profile says otherwise

Supported target policies:

- exact target
- minimum/maximum
- target plus or minus tolerance

Reports produced:

- whole-manuscript count
- per-section count
- per-subsection count
- included vs excluded buckets
- section budget variance

When under target:

- deterministic analysis identifies missing sections and thin sections first
- AI-facing suggestions then reference the outline, evidence matrix, and paper type instead of generic filler advice

When over target:

- deterministic section budget variance highlights the largest overruns first
- AI-facing cut suggestions prioritize low-centrality, redundant, or weakly supported material

## 7. Why Content And Formatting Must Be Separated

Universities, journals, and supervisors vary widely in formatting expectations. If content and formatting are mixed together, every new formatting requirement makes drafting and export logic messier.

Separation benefits:

- content remains reusable across institutions
- formatting changes do not corrupt manuscript structure
- raw-text and formatted modes can coexist cleanly
- default house styles can be sensible without pretending to be universal

This separation is also what makes word counting and clean DOCX/PDF export reliable.

## 8. Why Final Export Must Not Depend On Naive Markdown Conversion

The current exporter treats markdown as if it were a presentation format. That is good enough for a prototype, but not for professional deliverables.

Problems with naive conversion:

- markdown tokens can leak into the final document
- heading depth and list semantics are easily lost
- references remain raw text dumps instead of formatted bibliographies
- figure and table behavior becomes fragile
- page and section control is too weak

The redesign therefore parses authoring content into a semantic document model before rendering DOCX or PDF.

## 9. Profile System And Institution Overrides

Default paper types supported in the redesign:

- empirical / IMRaD paper
- literature review
- theoretical / conceptual paper
- case study
- thesis/dissertation chapter
- short conference paper

Default formatting profiles supported initially:

- `house_academic`
- `conference_compact`
- `thesis_classic`

Institution support model:

- use the selected paper type default first
- apply a formatting profile
- apply a citation style
- merge institution override rules if supplied

This avoids hardcoding university rules into prompts and avoids turning the system into a proliferation of one-off branches.

## 10. Citation And Reference Design

Bibliography handling becomes structured.

Every source record stores normalized metadata such as:

- source ID
- type
- authors
- title
- year
- venue or container
- volume
- issue
- pages
- DOI
- URL
- publisher
- verification flags

Claims link to source IDs through the evidence registry.

Final references are generated from structured metadata using citation style formatters. Unverified references may exist in working state, but export validation must reject unverified records from the final formatted bibliography unless the project is explicitly marked as draft-only.

## 11. Figures And Visual Material

Figure support is added safely and explicitly.

Figure preference modes:

- off
- suggest_only
- auto

Figure records distinguish:

- evidence-bearing data figures
- tables
- conceptual diagrams
- adapted visuals

Integrity rules:

- never fabricate data charts
- conceptual visuals must be labeled as conceptual where relevant
- adapted visuals preserve attribution metadata
- unresolved figure placeholders block formatted export

The system supports captions, numbering, placement metadata, and source attribution fields.

## 12. Multi-Agent Behavior Should Be Useful, Not Ornamental

The redesign keeps the manager pattern, but limits worker roles to cases where decomposition clearly helps.

Good worker use cases:

- parallel source-note extraction
- review by independent dimensions
- targeted drafting by section cluster
- synthesis under manager control

Bad worker use cases:

- routine work that adds coordination overhead without improving quality
- ornamental role splitting with overlapping ownership

Structured task objects and trace logs make worker usefulness measurable instead of theatrical.

## 13. User Experience And Intake

Required intake/config fields:

- title or topic
- paper type
- target word count or range
- citation style if known
- institution template or formatting rules if any
- output mode: raw / formatted / both
- figure preference: off / suggest / auto
- discipline if relevant
- deadline if relevant

If formatting rules are missing:

- choose the best default profile for the paper type
- record the selection transparently in project state and views

If output mode is not specified:

- default to `both`

## 14. Dependencies

The redesign should stay right-sized. Initial implementation uses:

- Python standard library for workflow, state, word counting, validation, and tests
- `python-docx` for high-quality DOCX rendering
- `reportlab` for direct PDF rendering

No database is introduced.

## 15. Testing, Evals, And Observability

Required tests:

- unit tests for deterministic word counting
- tests for section budget diagnostics
- tests for markdown artifact leak detection
- tests for reference normalization and formatting
- tests for export structure and output generation
- end-to-end smoke test for a sample project

Observability:

- trace events written to `trace.jsonl`
- workflow tasks and checkpoints stored in structured state
- render/validation/export status recorded in `exports.json` and `workflow.json`

Eval criteria:

- unsupported-claim rate
- citation fidelity
- section completeness
- word-count compliance
- export cleanliness

## 16. Migration Plan

Migration strategy:

1. introduce the structured runtime package and profile system
2. keep legacy scripts as thin wrappers over the new package
3. create new workspace initialization that writes canonical JSON state plus markdown views
4. provide a legacy migration command that imports old markdown-first projects into structured state
5. update documentation and examples

Backward compatibility goal:

- preserve existing file names where helpful for inspectability
- do not preserve markdown-only behavior as canonical state

## 17. Implementation Phases

Phase 1:

- package layout
- structured state files
- profile system
- workflow engine
- CLI
- markdown view generation

Phase 2:

- manuscript parser and semantic document model
- deterministic word count and budget diagnostics
- validation layer
- structured references and evidence registry

Phase 3:

- DOCX and PDF export pipeline
- raw/formatted/both output mode support
- figure metadata and rendering hooks
- export linting

Phase 4:

- migration tooling
- sample project refresh
- docs refresh
- tests and smoke runs

## 18. Success Criteria

The redesign is successful when:

- canonical workflow state is machine-readable and no longer markdown-only
- stage gates, task outcomes, and checkpoints are explicit and resumable
- word counts are deterministic and policy-driven
- raw/formatted/both output modes are stored and honored
- paper-type defaults and formatting profiles are selectable and documented
- DOCX and PDF exports are generated from semantic structure without markdown artifacts
- references and claims are structured and validated
- figures are supported with clear integrity rules
- tests and eval-oriented checks make quality measurable
