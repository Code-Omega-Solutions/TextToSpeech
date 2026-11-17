# UI Endpoint Configuration: Completed

## Outcome

Independent Inspector PASS was obtained in iteration 7. The feature was merged
into main as `1d57be6318d7fbf3344b84382c961adc78ecfa4b`, pushed without force to
origin/main, and the published merge SHA was verified against the remote.
No live installation was accessed or changed.

## Acceptance Results

| Criterion | Delivered |
| --- | --- |
| 1: Endpoint configuration | Accessible configuration tab, active/unsaved state, validation, runtime routing and stale-discovery isolation. |
| 2: Capabilities and legacy speech | Supported selectors, hidden unsupported controls, compatible legacy request defaults and distinct discovery errors. |
| 3: Persistence and documentation | Atomic shared settings, save-failure retention, restart/replacement persistence, file permissions and Compose instructions. |
| 4: Boundaries and existing behavior | Separate operator credential, exact destination allowlist, server-side backend secret, request ownership and preserved speech safeguards. |
| 5: Observable verification | Independent desktop/mobile keyboard verification, controlled-service routing, delayed-request regressions and retained-volume container/browser checks. |
| 6: Traceability | Companion artifacts, living specs, coverage and current evidence corrected to match actual behavior and checks. |
| 7: Delivery | Auditable Builder/Inspector commits, current origin/main incorporated, non-fast-forward local merge, non-force push and remote verification. |

## Configuration Location

The container stores the selected endpoint in
`/var/lib/private-speech-studio/endpoint.json`. Persist its containing directory
using the documented `tts_endpoint_config` volume or an appropriately protected
writable mount. See [frontend deployment documentation](../../frontend/README.md)
for permissions, precedence, `TTS_ALLOWED_UPSTREAMS` and the independent
`TTS_OPERATOR_TOKEN`. Updating the repository does not update a running container.

## Iteration History

| Iteration | Inspector result | Principal finding or resolution |
| --- | --- | --- |
| 1 | FAIL | Production routing/persistence and authorization were absent. |
| 2 | FAIL | Production MIME handling, tab visibility, stale responses and real feature coverage needed correction. |
| 3 | FAIL | Stale speech left generation disabled; static methods and production evidence needed work. |
| 4 | FAIL | Overlapping speech ownership, token-load editing and production-test synchronization needed correction. |
| 5 | FAIL | Product acceptance passed; keyboard evidence and recorded test count were inaccurate. |
| 6 | FAIL | Real keyboard input exposed an asynchronous test setup race. |
| 7 | PASS | Exact configuration-load synchronization passed three independent serial production runs. |

## Verification

The independent reports record 155 selected backend tests, 7 frontend unit
tests, 66 browser tests and 13 integrity tests passing through the mandatory
hook. Two optional fidelity tests were skipped. The Docker suite passed its
6 tests. The final production-container scenario passed three consecutive
independent serial runs, including two synthetic services, actual keyboard
editing, stale work, speech routing, same-volume recreation and a fresh browser.
See [final Inspector report](inspector-feedback-7.md).

## Recommendations

Keep the production-container browser scenario alongside the mandatory checks
when changing routing or runtime serving. Preserve the separation between
operator and backend credentials. Native model qualification, legal/rights
approval and deployment authorization remain separate gates.

## Optional Squash Command

Not executed. Main is already published; do not rewrite or force-push it.
Only for an unpublished disposable copy based on the recorded initial commit:

```powershell
git reset --soft e63512c4023e0bc93986d7b127f3d1947bc52967
git commit -m 'feat(frontend): add persistent endpoint configuration' -m 'Operators can choose an approved speech service, use compatible speech options, and retain settings across container updates.' -m 'Assisted-by: OpenAI:GPT-5.6 Luna' -m 'Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>'
```

The optional squash intentionally includes goal, feedback and status artifacts.
