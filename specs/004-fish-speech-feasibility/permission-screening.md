# Fish Speech Permission Screening

**Screened**: 2026-11-16
**Permission status**: blocked
**Intended use**: unresolved
**Voice rights**: unresolved

## Findings

| Category | Evidence status | Finding |
| --- | --- | --- |
| Code terms | reviewed in existing research | Fish Audio Community License v1.0 applies to the reviewed Fish Speech source; this is not a blanket permissive-license clearance. |
| Weight terms | unverified | The reviewed README distinguishes S2-Pro weights under the Fish Audio Research License. Full checkpoint terms and model-card contents were unavailable to the research run. |
| Codec terms | unresolved | The reviewed Community License describes a specific Drama 3 codec scope. That does not clear every model/codec combination. |
| Intended use | unresolved | Private evaluation, internal business use, product-generated speech, and third-party self-service speech have not been distinguished by the requester. |
| Commercial/hosted conditions | unresolved for this use | The source terms include conditional commercial rights and a separate Hosted Service definition with exceptions. The concrete use and applicable permission require review. |
| Voice rights | unresolved | No proposed voice, consent, or provenance record has been supplied. Availability of a voice or cloning feature is not permission. |
| Runtime artifacts | unresolved | No candidate runtime inventory or artifact-level dependency review is approved by this screening. |

The existing research examined source revision
`0f8a12e8a651062fdee9c33a894bdccd3a8513f1`. Its public-source findings are
dated evidence, not a new retrieval or legal determination. The model-card and
weight-license requests returned redirects that were not followed. No later
terms, alternate checkpoints, or hosted-service agreements were reviewed here.

## Required Inputs

- Q1: A concrete use description and intended users, without private speech data.
- Q2: The accountable rights reviewer and person authorized to approve testing.
- Q3: The exact candidate, revision, codec, and runtime artifact inventory.
- Q4: Review of the applicable use and commercial/hosted-service conditions.
- Q8: Authoritative full model/weight terms and the proposed voice's provenance.

These refer to the [assessment questions](../../.specify/assessments/fish-speech/problem.md#open-questions).
No candidate or intended-use category has been chosen to fill the gaps.

## Stop Boundary

Permission remains blocked. Model downloads, package installation, host access,
and synthesis are withheld pending the required rights findings and separate
operator approval. The documentary feature may finish with this blocker;
production use and redistribution remain separate decisions.

## Evidence

- [Existing licensing research](../../.specify/assessments/fish-speech/research.md#licensing-and-intended-use)
  records source findings and unavailable model evidence.
- [Reviewed source license](https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/LICENSE)
  and [reviewed README](https://raw.githubusercontent.com/fishaudio/fish-speech/0f8a12e8a651062fdee9c33a894bdccd3a8513f1/README.md)
  identify the exact source revision; this screening did not fetch them again.
- [Project constitution](../../.specify/memory/constitution.md) and
  [third-party review boundaries](../../capabilities/project-licensing/project-licensing.spec.md)
  keep permissions, private research, and release qualification separate.
