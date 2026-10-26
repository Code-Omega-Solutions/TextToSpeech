# Frontend image publishing - Coverage gaps

No automated workflow regression tests are currently mapped to this capability.
Workflow lint and a successful publication are useful operational evidence, but
neither proves branch isolation or deletion behavior with more than five versions.

| Requirement | Missing automated evidence |
| --- | --- |
| Only main publishes frontend images | Trigger/job-condition regression check |
| Each successful build has a stable latest tag and a unique version | Naming and rerun-version assertion |
| Successful publication keeps the five newest versions | Retention test with more than five fixture versions, publication failure and cleanup failure |

Keep these entries uncovered in Companion's coverage report until actual tests
exist. Do not invent test paths or exercise destructive cleanup against public
packages merely to make the coverage indicator green.
