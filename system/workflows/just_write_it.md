# Just-Write-It Workflow

Use this workflow when the user explicitly wants the system to take the request, ask only the most necessary questions, and run end to end as autonomously as possible.

## Operating Principle

Move fast, but never fabricate. The manager may compress stages, but must keep evidence traceable, mark uncertainty explicitly, and finish with a real review pass.

## Intake Rule

- Ask at most 10 questions total
- Ask only if the answer would materially change research, structure, or output format
- If the user leaves a field open, make a transparent working assumption and record it

## Stage 0: Minimal Viable Brief

Goal: gather enough to act without stalling.

Primary owner:

- `manager`

Optional specialists:

- `scientist` for feasibility sanity-check

Tasks:

- Capture topic, context, paper type, length, output format, audience, and main goal
- Record assumptions and approved shortcuts

Outputs:

- `project_brief.md`
- `project_context.md`

Stage gate:

- The manager can proceed without another interview loop

## Stage 1: Fast Research Frame

Goal: define the minimum viable evidence and structure needed to draft credibly.

Primary owners:

- `manager`
- `scientist`

Optional parallel workers:

- one or more `researcher` agents for quick evidence slices

Tasks:

- Write a compact research plan
- Identify non-negotiable sources or evidence types
- Define which sections can be drafted now and which require explicit caveats

Outputs:

- `research_plan.md`
- `project_context.md`

Stage gate:

- The manager knows the minimum evidence needed for a credible first full draft

## Stage 2: Rapid Evidence Pass

Goal: collect enough inspected support to write a first defensible manuscript quickly.

Primary owners:

- one or more `researcher` agents
- `source_checker`

Parallelization pattern:

- split by topic branch or section evidence needs
- let `source_checker` audit the gathered support while research is still in progress

Tasks:

- Create high-value source notes first
- Build a lean but useful `bibliography.md`
- Populate `evidence_matrix.md` for major claims only

Outputs:

- `sources/*.md`
- `bibliography.md`
- `evidence_matrix.md`

Stage gate:

- Enough support exists to draft the whole paper with explicit caveats where needed

## Stage 3: Rapid Outline And Draft

Goal: get to a full manuscript as soon as possible without pretending unsupported certainty.

Primary owners:

- `outliner`
- one or more `drafter` agents

Tasks:

- Build a pragmatic outline
- Draft the full paper
- Use `[TODO: evidence]` and limitation language instead of guessing

Outputs:

- `outline.md`
- `draft.md`

Stage gate:

- A complete draft exists
- Remaining unsupported spots are visible

## Stage 4: Hard Review

Goal: prevent the fast path from becoming a sloppy path.

Primary owners:

- `reviewer`
- `source_checker`
- `style_proofreader`
- `progress_auditor`

Tasks:

- Challenge reasoning and support
- Remove overclaiming
- Tighten style and compliance
- Confirm that shortcuts and assumptions are recorded

Outputs:

- `revision_checklist.md`
- updated `draft.md`
- updated `project_context.md`

Stage gate:

- The final paper is the best credible version the system can produce under the available information

## Stage 5: Final Delivery

Goal: package the best available final artifact quickly and transparently.

Primary owner:

- `manager`

Tasks:

- Finalize `deliverables/final_paper.md`
- Record remaining gaps and assumptions
- Mark the run complete in the status board

Outputs:

- `deliverables/final_paper.md`
- `project_context.md`
- `agent_status.md`

Exit criteria:

- Final paper exists
- Any remaining uncertainty is visible to the user
