# Decision: Proceed with bounded local feasibility evaluation

- **Slug**: fish-speech
- **Decided**: 2026-11-16
- **Verdict**: go
- **Artifacts reviewed**: intake.md | research.md | problem.md | concept.md
- **Chosen option**: Option B - Bounded local feasibility evaluation

## Scorecard

Ratings assess whether the bounded evaluation is worth specifying, not whether
Fish Speech is qualified, permitted for the eventual use, or better than the
baseline. The user's selection is evidence of interest in this evaluation,
not evidence of voice quality, legal clearance, or available capacity.

| Criterion | Rating | Justification |
| --- | --- | --- |
| Problem validity | adequate | The recorded English/German alternative request and the user's selection establish interest in resolving suitability; research identifies concrete permission and capacity uncertainties, not a demonstrated service failure. |
| Evidence strength | adequate | Pinned source terms and runtime guidance support a permission/capacity investigation; they do not establish full weight terms, German quality, or local performance. |
| Value vs. inaction | unknown | The user chooses the bounded exploration, but no quantified benefit, cost of inaction, or approved expenditure is established. |
| Feasibility / appetite | unknown | Documentary screening is a credible starting point, but the time budget, exact candidate, authorized host, and ability to complete testing remain unconfirmed. |
| Strategic fit | strong | English/German scope, evidence-based evaluation, and unchanged service/release boundaries align with the problem and constitution. |
| Risk posture | adequate | Screening first and requiring separate permission/host/testing approvals bound premature operational changes; candidate rights, capacity, and quality risks remain unresolved. |

Evidence: [intake](intake.md), [research](research.md),
[problem and measures](problem.md), [Option B](concept.md#option-b---bounded-local-feasibility-evaluation),
and [constitution](../../memory/constitution.md).

## Verdict & Rationale

**Go: proceed with Option B as a bounded, documentary-first feasibility
evaluation.** The user selected this option with "Proceed with option B" on
2026-11-16. The problem-validity and evidence-strength ratings support
specifying an investigation of the identified uncertainties, not asserting
that a candidate already satisfies them.

The unknown value-versus-inaction and feasibility/appetite ratings are not
resolved by this selection. The proposed small appetite remains an unapproved
budget ceiling, not an estimate or spending commitment. Specification must
retain these uncertainties and establish a stopping boundary before evaluation
work expands. An incomplete review or a documented blocker is a legitimate
evaluation outcome. [Concept recommendation](concept.md#recommendation).

This decision authorizes the assessment handoff for the chosen concept only.
It does not choose a checkpoint, clear licenses or voice rights, authorize
model/package downloads or installation, approve target-machine access or
changes, permit a synthesis test, or approve production use or redistribution.
The existing macOS baseline and separate VibeVoice research scope remain
unchanged. No fallback to Option C, purchase, extra model, platform port, or
larger budget is implicit. [Scope limits](concept.md#out-of-scope-for-the-recommended-option);
[research gates](research.md#licensing-and-intended-use).

## Handoff to Specification

- **Problem**: Establish whether an English/German speech candidate can deliver
  worthwhile quality for the intended use within reviewed permissions and
  available capacity, without compromising the baseline or higher-priority
  workloads. [Problem statement](problem.md#problem-statement).
- **Chosen approach**: Option B, starting with documentary permission and
  capacity screening. A limited comparison is conditional on resolving the
  required prerequisites and obtaining separate operator approval; it is not
  automatically authorized by this decision.
- **In scope**: A bounded feasibility assessment for one reviewed candidate;
  recorded intended-use and rights findings; capacity evidence from an
  authorized source; explicit complete, incomplete, or blocked findings;
  language-specific comparison evidence only if later approved.
- **Out of scope**: Service integration or replacement, production/redistribution
  claims, hosted offerings, private-data disclosure, unapproved installations,
  hardware purchases, broad model comparisons, training, fine-tuning,
  quantization research, and platform ports. Preserve all
  [Option B exclusions](concept.md#out-of-scope-for-the-recommended-option).
- **Success metrics**: Use the [problem's proposed measures](problem.md#success-metrics)
  for permission readiness, English/German quality, timing, capacity/reserve,
  and continuity/privacy. Agree actual thresholds before any qualification
  conclusion; distinguish upstream guidance from measurements. If testing
  remains blocked, record unavailable measures rather than claiming success.
- **Carried-forward open questions**: All eight
  [problem questions](problem.md#open-questions) remain unresolved: intended
  users/use (Q1), accountable approvals (Q2), exact candidate/artifacts (Q3),
  applicable terms (Q4), worthwhile benefit (Q5), authorized machines and
  budgets (Q6), evaluation material/listeners/criteria (Q7), and voice provenance
  plus authoritative weight/model-card evidence (Q8).
- **Budget and stopping boundary**: Agree the small appetite and review scope
  before execution. If permission, capacity, approval, or the agreed boundary
  prevents progress, report the blocker and stop rather than silently changing
  the candidate, machine, method, or budget.

The next workflow phase is `/speckit-specify` using this handoff. This decision
is not a feature specification, technical plan, task list, or completed
feasibility result.
