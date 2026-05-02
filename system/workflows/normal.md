# Guided Evidence-First Workflow

Use this workflow for the default `start-paper here` path.

## Stage 0: Intake

Goal: reach a minimum viable brief without over-interviewing the user.

Primary owner:

- `manager`

Optional specialists:

- `scientist` for scope realism

Tasks:

- Fill the essential brief fields
- Clarify the requested paper type, audience, length, and deadline
- Record open questions that still matter
- Choose the evidence expectation and run mode

Outputs:

- `project_brief.md`
- `project_context.md`

Stage gate:

- The brief is good enough to plan research
- Remaining unknowns are explicitly listed

## Stage 1: Research And Method Strategy

Goal: define how the paper will be supported and evaluated.

Primary owners:

- `manager`
- `scientist`

Optional parallel workers:

- one or more `researcher` agents for search strings, source families, or subtopics

Tasks:

- Define the core question or thesis
- Draft likely answer space and boundaries
- Build search strings and inclusion criteria
- Sanity-check methodology and feasibility
- Identify the minimum evidence needed before drafting

Outputs:

- `research_plan.md`
- `project_context.md`

Stage gate:

- The research plan is credible
- The manager knows what evidence would be enough to outline

## Stage 2: Source Collection And Evidence Matrix

Goal: gather inspected sources and map them to claims.

Primary owners:

- one or more `researcher` agents
- `source_checker`

Parallelization pattern:

- split researchers by topic branch, source family, or pro/con evidence slice
- let `source_checker` audit completed source notes and support mapping

Tasks:

- Create one note per meaningful source in `sources/`
- Maintain `bibliography.md`
- Build `evidence_matrix.md`
- Flag unsupported claims early

Outputs:

- `sources/*.md`
- `bibliography.md`
- `evidence_matrix.md`
- `notes/handoffs.md`

Stage gate:

- There is enough inspected support to structure the paper
- Weak spots are visible, not hidden

## Stage 3: Outline

Goal: turn the evidence package into a draftable structure.

Primary owners:

- `outliner`

Optional specialists:

- `scientist` for structure realism
- `reviewer` for argument stress-testing

Tasks:

- Group evidence into sections
- Order sections logically
- Estimate section lengths
- Flag sections that still need evidence

Outputs:

- `outline.md`

Stage gate:

- The drafter can work from the outline without guessing the structure

## Stage 4: Draft

Goal: produce a complete working manuscript from approved evidence and structure.

Primary owners:

- one or more `drafter` agents

Optional parallelization:

- split drafting by section clusters with clear file merge ownership

Tasks:

- Draft from the outline and evidence matrix
- Mark unsupported areas with `[TODO: evidence]`
- Keep tone, audience, and format constraints visible

Outputs:

- `draft.md`

Stage gate:

- A full draft exists
- Unsupported areas are explicit

## Stage 5: Review And Revision

Goal: stress-test the draft before final delivery.

Primary owners:

- `reviewer`
- `source_checker`
- `style_proofreader`
- `progress_auditor`

Parallelization pattern:

- `reviewer`: logic, overclaiming, structural drift
- `source_checker`: claim-to-source fidelity
- `style_proofreader`: tone, clarity, consistency, format
- `progress_auditor`: workflow and status completeness

Tasks:

- Challenge the argument
- Verify support for major claims
- Tighten style and formatting
- Record unresolved risks

Outputs:

- `revision_checklist.md`
- updated `draft.md`
- updated `project_context.md`

Stage gate:

- Remaining limitations are transparent
- The draft is ready for final packaging

## Stage 6: Final Delivery

Goal: produce the final project artifact and preserve the run state.

Primary owners:

- `manager`

Tasks:

- Copy the approved manuscript into `deliverables/final_paper.md`
- Update `project_context.md`
- Ensure the status board reflects completion

Outputs:

- `deliverables/final_paper.md`
- `project_context.md`
- `agent_status.md`

Exit criteria:

- Final paper exists
- Final caveats are documented
