# Backend prerequisite management - Requirement-to-test map

These references cover mocked inspection and setup behavior. They do not
qualify a native macOS host, package publisher, or service deployment.

| Requirement | Test reference | Evidence scope |
| --- | --- | --- |
| Check-only inspection reports a stable diagnostic for each prerequisite | [backend/tests/test_prerequisites.py](../../backend/tests/test_prerequisites.py) | Stable IDs, statuses, reasons and remediation for platform, executable, voice, configuration, credential, destination, disk and port checks |
| Check-only inspection leaves the machine unchanged | [backend/tests/test_prerequisites.py](../../backend/tests/test_prerequisites.py) | No file, package, service or application-import side effects |
| Timed-out prerequisite checks return actionable diagnostics | [backend/tests/test_prerequisites.py](../../backend/tests/test_prerequisites.py) | Bounded timeout handling, safe output, and documented exit codes |
| Setup requires acceptance of the exact proposed changes | [backend/tests/test_setup.py](../../backend/tests/test_setup.py) | Explicit plan acceptance and no changes without matching approval |
| Setup changes only a dedicated user-owned environment | [backend/tests/test_setup.py](../../backend/tests/test_setup.py) | Unmanaged destination protection and credential preservation |
| Setup does not overlap changes to the same destination | [backend/tests/test_setup.py](../../backend/tests/test_setup.py) | Lock contention prevents concurrent installation |
| Setup verifies locked dependencies and readiness before reporting success | [backend/tests/test_setup.py](../../backend/tests/test_setup.py) | Locked install and dependency verification before success |
| Failed setup removes only artifacts created by that attempt | [backend/tests/test_setup.py](../../backend/tests/test_setup.py) | Failure cleanup, manual blockers, preserved credentials and repeat no-op |
| The launchd example requires explicit operator configuration | [backend/tests/test_service_example.py](../../backend/tests/test_service_example.py) | Portable plist paths, safe PATH, protected credential-file reference, no host identity/secret, and no automatic start |
