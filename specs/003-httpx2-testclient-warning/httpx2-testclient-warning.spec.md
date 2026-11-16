# Feature Specification: Keep Backend Test Runs Warning-Free

**Status**: Draft
**Created**: 2026-11-15
**Source**: A deprecated test-client compatibility warning in backend test runs

## User Scenarios & Testing

### User Story 1 - Run backend tests without a deprecated warning (Priority: P1)

As a backend maintainer, I want routine backend test runs to be free of
deprecated test-client warnings, so useful failures remain visible and the
test environment follows supported compatibility paths.

**Why this priority**: The warning appears throughout the backend tests and
obscures useful diagnostics, while the supported alternative can be isolated
to development dependencies.

**Independent Test**: Run the backend test suite with the deprecated
test-client warning treated as an error. Confirm all tests pass, including
existing asynchronous request tests.

**Acceptance Scenarios**:

1. **Given** a backend test exercises an application through its test client,
  **When** the test is run, **Then** it emits no deprecated client-adapter
  warning.
2. **Given** existing asynchronous request tests are run, **When** the suite
  executes, **Then** their request and transport behavior remains unchanged.
3. **Given** the backend runtime is installed without development dependencies,
   **When** the application starts, **Then** the new test-client dependency is
   not required by the runtime.
4. **Given** the dependency lock is refreshed, **When** its package inventory
   is reviewed, **Then** the new package's license is recorded without
   changing unrelated license claims.

## Edge Cases

- The new client package must resolve with the project's supported Python and
  Starlette versions.
- If dependency resolution conflicts with the supported framework range, stop
  and record the conflict instead of widening runtime constraints.

## Requirements

### Functional Requirements

- **FR-001**: Backend test-client operations MUST complete without the
  deprecated compatibility warning.
- **FR-002**: The warning cleanup MUST NOT change the application runtime
  dependency set or runtime HTTP behavior.
- **FR-003**: The dependency lock MUST resolve reproducibly, and the third-party
  inventory MUST record the resolved package license and scope.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The backend test suite passes with the targeted test-client
  deprecation warning treated as an error.
- **SC-002**: Existing asynchronous request tests continue to pass.
- **SC-003**: The locked dependency graph is reproducible and the application
  runtime dependency set is unchanged.
- **SC-004**: The third-party inventory identifies the new package and its
  development-only scope.

## Assumptions

- Keep `httpx` for direct test imports that still require it.
- Use `httpx2` only for the test-client adapter that emits the warning.
- This change does not alter application routes, runtime HTTP behavior, or
  production dependencies.

## Approach

- Add `httpx2` to the backend development dependency group and refresh the
  backend lock while retaining `httpx` for direct test imports.
- Review the exact resolved package license and update the third-party notice.
- Run the warning-focused backend test suite, the lock consistency check, and
  the license-integrity check.
