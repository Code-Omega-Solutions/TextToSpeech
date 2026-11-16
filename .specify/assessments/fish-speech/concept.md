# Concept: Permission-gated English and German speech evaluation

- **Slug**: fish-speech
- **Created**: 2026-11-16
- **Recommended option**: Option B - Bounded local feasibility evaluation

## Options

These are concept-level alternatives to address the
[defined problem](problem.md#problem-statement), not approved work or a model
selection. Appetite labels express proposed budget ceilings, not delivery
estimates; no operator, funding, or time commitment is established by the inputs.
The [problem's open questions](problem.md#open-questions) remain unresolved.

### Option A - Keep the baseline and defer another candidate

- **Sketch**: Users continue with the documented macOS speech baseline, and the
  existing private VibeVoice research boundary remains unchanged. The requester
  defers another candidate until a concrete unmet English/German need and an
  acceptable evaluation budget are established. This is the do-nothing option,
  not a finding that the baseline already meets every need.
  [Baseline and inaction](problem.md#cost-of-inaction).
- **Appetite**: small (days), only as a provisional decision/review ceiling; no
  implementation is proposed. [NEEDS CLARIFICATION: Confirm whether any further
  review time is wanted or funded; no budget has been approved.]
- **Trade-offs**: Avoids new candidate-specific installation, rights review,
  and competition for machine resources, but leaves the alternative request
  unresolved. The evidence does not quantify the cost of that delay or prove
  an existing quality failure. [Research](research.md#market--context).
- **Rabbit holes**: Indefinite comparisons without agreed user needs; treating
  a deferred candidate as a legal rejection; allowing this decision to expand
  the separate VibeVoice research authorization.

### Option B - Bounded local feasibility evaluation

- **Sketch**: The requester receives a bounded answer about whether a reviewed
  Fish Speech candidate merits further consideration for English/German.
  First establish the concrete use, required permissions, and whether an
  authorized machine is a credible fit. Only if those prerequisites clear and
  the operator separately approves testing would a limited comparison provide
  language-specific quality, timing, and resource evidence against the baseline.
  An unresolved permission or capacity blocker is a valid outcome, not a reason
  to install anyway. Existing speech behavior stays unchanged.
  [Goals](problem.md#goals); [constraints](research.md#data--constraints).
- **Appetite**: small (days), a proposed ceiling for one candidate's feasibility
  assessment, not an estimate that review or testing can finish in days.
  [NEEDS CLARIFICATION: Agree the evaluation budget and whether rights review
  and authorized testing can fit it; otherwise pause rather than widen scope.]
- **Trade-offs**: Addresses the permission, bilingual-quality, responsiveness,
  and capacity measures without committing to production adoption. It may end
  at documentary review, produce incomplete evidence, or show that no available
  machine is suitable. Full weight terms, German quality, local latency, and
  capacity are not yet verified. Drama 3's documented NVIDIA/48 GB requirement
  and S2-Pro's separate weight terms make screening substantive; this concept
  selects neither model. [Metrics](problem.md#success-metrics);
  [research](research.md#languages-platforms-and-capacity);
  [terms](research.md#licensing-and-intended-use).
- **Rabbit holes**: Testing several generations or model families; pursuing
  quantization, training, or platform ports to make a failed candidate fit;
  custom voice acquisition; open-ended commercial negotiations; moving from a
  private experiment to routine service use before the separate review gates.

### Option C - Evaluate a managed speech offering instead of a local model

- **Sketch**: The requester considers obtaining English/German speech from a
  managed provider rather than running another model on the project's machines.
  A comparison would be considered only after provider-specific usage rights,
  privacy, voice provenance, cost, and permitted evaluation inputs are reviewed.
  No provider is selected and no speech text or audio is sent externally by this
  concept. Upstream advertises a hosted offering, but the research did not verify
  its terms, prices, retention, or fitness for this project.
  [Market evidence](research.md#market--context).
- **Appetite**: small (days), a provisional ceiling for a terms/cost/suitability
  assessment, not a purchase, integration, or procurement estimate.
  [NEEDS CLARIFICATION: Confirm whether external processing, a paid offering,
  and this review budget are acceptable for the intended use.]
- **Trade-offs**: Could avoid local model resource demands, but that benefit
  is an assumption, not a measured result. It introduces dependence on provider
  availability, data handling, network access, and recurring terms/costs. A
  provider's service agreement must be reviewed on its own merits; neither a
  public playground nor the local source license proves permission for this use.
  [Research gaps](research.md#gaps--open-questions).
- **Rabbit holes**: Multi-provider procurement, unbounded pricing comparisons,
  privacy exceptions, bespoke service contracts, or treating a purchased service
  as justification to build a third-party hosted speech business.

## Recommendation

Provisionally recommend **Option B - Bounded local feasibility evaluation**,
starting with documentary permission and capacity screening only. It is the
smallest proposed change that could produce evidence about the original Fish
Speech idea while addressing the problem's permission, quality, timing, and
resource measures and preserving the existing baseline.
[Intake](intake.md); [success measures](problem.md#success-metrics).

This is a recommendation for a bounded concept, not a go decision, a chosen
checkpoint, installation consent, or clearance for private testing, production,
or redistribution. The unresolved use, rights, voice, and host questions must
be addressed before any separately authorized test. If the agreed appetite
expires or a prerequisite cannot be resolved, record the blocker and stop;
do not silently substitute a model, host, paid service, or larger scope.
[Open questions](problem.md#open-questions);
[review gates](research.md#licensing-and-intended-use).

Option A remains a credible alternative because neither the cost of inaction
nor a required quality improvement is established. Option C warrants further
consideration only if the requester accepts external processing and provider
terms; that acceptance cannot be inferred from this local-model idea.
[Inaction](problem.md#cost-of-inaction);
[market context](research.md#market--context).

## Out of Scope (for the recommended option)

- Production adoption, routine service changes, or replacement of the baseline.
- A specification, implementation architecture, interfaces, data models, or
  task breakdown in this assessment artifact.
- Choosing a model/checkpoint before exact terms and host suitability are known.
- Broad model tournaments, training, fine-tuning, quantization research, or
  platform ports to bypass a capacity or support blocker.
- Buying hardware or expanding the agreed time or cost budget without approval.
- Languages beyond English and German, and voice cloning as an assumed need.
- Unapproved model/package installation, target-machine changes, or voice use.
- Sending private texts, audio, credentials, or operational details to a provider
  or committing them to the repository.
- Building a third-party hosted speech service, asserting legal permission,
  or treating private evaluation as production or redistribution qualification.

These limits preserve the [inherited non-goals](problem.md#non-goals) and the
[research's rights and operational boundaries](research.md#data--constraints).

## Assumptions to Validate

- [NEEDS CLARIFICATION: Confirm the intended users, workflow, and concrete
  evaluation/use purpose; private non-commercial use is not assumed (Q1).]
- [NEEDS CLARIFICATION: Name the people authorized to approve rights review,
  host inspection, testing, and acceptance, and agree the small appetite (Q2).]
- [NEEDS CLARIFICATION: Establish an exact candidate revision, codec, runtime
  inventory, and applicable terms through authoritative sources; the current
  unverified weight/model-card evidence cannot support approval (Q3-Q4, Q8).]
- [NEEDS CLARIFICATION: Confirm that the required voice provenance and intended
  use permissions can be satisfied before any candidate test (Q4, Q8).]
- [NEEDS CLARIFICATION: Confirm an unmet need and worthwhile benefit, agree
  English/German criteria, and provide permitted comparison material and
  appropriate listeners; improved quality is not established (Q5, Q7).]
- [NEEDS CLARIFICATION: Establish an authorized machine, measured capacity,
  higher-priority reserve, timing limits, and evaluation conditions; an upstream
  platform claim is not local qualification (Q6).]

Question identifiers refer to the [problem definition](problem.md#open-questions).
None of these assumptions is resolved or authorized by creating this concept.
