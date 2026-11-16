# Problem Definition: Suitable English and German speech within legal and resource limits

- **Slug**: fish-speech
- **Created**: 2026-11-16
- **Inputs used**: intake.md | research.md

## Problem Statement

For the project's intended English/German speech users and operator, it remains
unproven whether speech beyond the documented macOS baseline can deliver
worthwhile quality within the intended-use permissions and available machine
capacity. The reported restrictions on the previously considered option make
this uncertainty relevant now, but the intended users, deployment purpose, and
acceptable quality and performance thresholds still require clarification.
[Intake](intake.md); [research](research.md#users--demand).

## Affected Users & Stakeholders

- **Users**: Intended recipients of English and German speech. Their identities,
  workflows, and actual unmet needs are not established; these remain Q1 and Q5,
  rather than evidence of an existing service failure.
  [Intake](intake.md#first-glance-unknowns).
- **Requester**: Patrik Gfeller raised the idea. The intake does not establish
  that this role also carries funding, legal-review, or release authority (Q2).
  [Intake](intake.md#origin--context).
- **Operator**: The role responsible for the candidate machines is affected by
  speech resource use and competing inference workloads. The responsible person
  and authorized machines remain unconfirmed (Q2 and Q6).
  [Research](research.md#users--demand).
- **Rights and release reviewers**: Project policy requires review of intended
  use, artifacts, voices, and release boundaries. The people accountable for
  these decisions are not named by the available evidence (Q2).
  [Research](research.md#licensing-and-intended-use).

## Goals

- Establish whether the intended English/German use can proceed with reviewed
  permissions for the relevant materials and voices, without treating private
  research authorization as production or redistribution clearance.
  [Research](research.md#licensing-and-intended-use).
- Establish language-specific quality against the documented baseline. A
  worthwhile improvement is a provisional goal, not a demonstrated user need;
  the requester must confirm what improvement matters (Q5).
  [Research](research.md#users--demand).
- Establish whether the authorized machines can meet the agreed speech needs
  without compromising higher-priority inference workloads. Capacity and timing
  budgets are not yet defined (Q6).
  [Research](research.md#languages-platforms-and-capacity).
- Preserve existing speech availability, privacy, and rights boundaries while
  resolving these uncertainties; do not mistake upstream claims for local
  qualification. [Research](research.md#prior-art);
  [review constraints](research.md#data--constraints).

## Non-Goals

- Choosing Fish Speech, another model family, a checkpoint, or a deployment
  architecture in this problem-definition stage.
- Adding languages beyond the recorded English/German scope.
- Establishing a voice-cloning requirement from the availability of cloning
  functionality, or assuming permission to use an identifiable person's voice.
- Building a third-party hosted speech service or defining commercial terms
  before the intended use and applicable permissions are resolved.
- Claiming production readiness, native platform qualification, unrestricted
  redistribution, or legal approval from research documents or license labels.
- Installing models, changing the existing service, or selecting implementation
  features, interfaces, or tasks during this assessment stage.

These boundaries follow the recorded language scope and the research's explicit
distinction between an exploration, verified permissions, and approved use.
[Intake](intake.md); [research](research.md#scope--method);
[licensing constraints](research.md#licensing-and-intended-use).

## Success Metrics

The following are proposed assessment measures, not approved acceptance targets
or observed results. Numeric thresholds must be agreed before a later
qualification decision; no latency, quality, or memory target is invented here.
[Research gaps](research.md#gaps--open-questions).

| Outcome | Measure | Baseline | Success condition |
| --- | --- | --- | --- |
| Permitted intended use | Unresolved permission/provenance issues for the exact use and materials | Review remains incomplete; issue count not established | No unresolved required permission or provenance issue before that use is approved; reviewers and scope confirmed in Q2-Q4 and Q8 |
| English/German quality | Paired listener assessments and language-specific intelligibility results | No reviewed Fish Speech comparison; baseline scores unknown | Both languages satisfy requester-approved criteria; the required benefit over the baseline is resolved in Q5 and Q7 |
| Responsiveness | Measured time to first audio and total synthesis time under representative conditions | Local candidate measurements unknown | Agreed timing limits are met on the authorized machines; limits remain Q6 |
| Capacity and competing workloads | Measured peak RAM/VRAM, storage needs, and remaining higher-priority workload reserve | Candidate-machine measurements unknown | Agreed capacity and reserve bounds are met; bounds remain Q6 |
| Continuity and privacy | Evidence that existing speech availability and privacy obligations remain satisfied | Documented baseline contract, not a newly verified deployment | No unapproved loss of existing behavior or disclosure of private speech data; applicable use and review criteria resolved before any change |

The measures are grounded in the research's quality, latency, capacity,
baseline-contract, and rights-review gaps; they do not prescribe a solution.
[Research](research.md#data--constraints);
[baseline evidence](research.md#prior-art).

## Cost of Inaction

At the documented source level, the macOS baseline and the separately bounded
private VibeVoice research path remain unchanged. Not pursuing another candidate
avoids new candidate-specific review and resource commitments, but leaves the
recorded request for an alternative unresolved.
[Research](research.md#market--context);
[intake](intake.md).

A continuing quality gap is an assumption, not an established consequence.
The available evidence contains no quantified cost, usage volume, service-level
failure, or deadline showing that inaction harms users. Those missing facts must
not be replaced with an invented business case (Q1 and Q5).
[Research](research.md#users--demand);
[cost context](research.md#market--context).

## Open Questions

- **Q1**: [NEEDS CLARIFICATION: Who will use the speech, for which workflows, and
  is the intended use private evaluation, internal business operation,
  product-generated speech, or third-party self-service speech generation?]
- **Q2**: [NEEDS CLARIFICATION: Who owns the operational, rights/legal, and
  acceptance decisions, and who can authorize inspection, evaluation, and any
  later release or deployment?]
- **Q3**: [NEEDS CLARIFICATION: Which exact candidate model/checkpoint revision,
  codec, runtime artifacts, and accompanying terms require review, including
  any older Fish Speech candidate?]
- **Q4**: [NEEDS CLARIFICATION: Do those terms permit the concrete intended use,
  including relevant commercial or hosted-service conditions, or is a separate
  written agreement required?]
- **Q5**: [NEEDS CLARIFICATION: What unmet English/German speech need justifies
  this exploration, and what quality or other benefit over the documented
  baseline would make pursuing it worthwhile?]
- **Q6**: [NEEDS CLARIFICATION: Which machines are authorized for evaluation,
  and what measured storage, RAM/VRAM, higher-priority reserve, and speech
  latency budgets and workload conditions apply?]
- **Q7**: [NEEDS CLARIFICATION: Which permitted English/German texts, baseline
  recordings, listeners, and measurable acceptance thresholds will establish
  quality and practical value for both languages?]
- **Q8**: [NEEDS CLARIFICATION: What consent/provenance covers the intended voices,
  and how will authoritative model-card and full weight-license contents be
  obtained through a permitted mechanism to complete the rights review?]
