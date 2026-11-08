# Backend prerequisite management — Living Spec

## Requirements

### Check-only inspection reports a stable diagnostic for each prerequisite

The prerequisite checker SHALL inspect platform, architecture, Python, `say`,
environment tooling, ffmpeg codecs, required and optional voices, configuration,
credential accessibility, destination access, disk space, and port availability.
Each result SHALL include a stable identifier, status, reason, and remediation
in human-readable or JSON output.

#### Scenario: a supported and ready machine is inspected
- **WHEN** the operator runs check-only inspection
- **THEN** it reports a result for each listed prerequisite with its identifier, status, reason, and remediation.

### Check-only inspection leaves the machine unchanged

Inspection SHALL not install or download software, write files, import the
application, register services, or synthesize speech.

#### Scenario: check-only inspection completes
- **WHEN** the operator runs inspection on a machine with missing or available prerequisites
- **THEN** the command leaves files, packages, credentials, and services unchanged.

### Timed-out prerequisite checks return actionable diagnostics

Prerequisite checks SHALL be noninteractive and bounded. A blocker or timeout
SHALL produce a named diagnostic with its reason and remediation, and inspection
SHALL exit nonzero without exposing raw command output, secrets, or private
paths.

#### Scenario: a prerequisite check is blocked or times out
- **WHEN** a required prerequisite is missing or a check exceeds its bound
- **THEN** inspection reports the named result, exits nonzero, and omits raw output, secrets, and private paths.

### Setup requires acceptance of the exact proposed changes

Setup SHALL display its planned changes and require explicit acceptance of that
exact plan before making changes.

#### Scenario: a setup plan is not accepted
- **WHEN** the operator requests setup without accepting the displayed plan identifier
- **THEN** setup reports the plan and performs no installation or environment mutation.

### Setup changes only a dedicated user-owned environment

Setup SHALL make changes only in a dedicated, user-owned environment. It SHALL
not bootstrap missing package managers, install global packages, overwrite an
unmanaged environment or existing credentials, escalate privileges, or register
or start services.

#### Scenario: setup encounters an unmanaged destination or credential
- **WHEN** the selected destination is unmanaged or contains existing credentials
- **THEN** setup leaves it unchanged and reports that operator action is required.

### Setup does not overlap changes to the same destination

Setup SHALL serialize changes targeting the same environment.

#### Scenario: setup attempts overlap for one destination
- **WHEN** two setup attempts target the same environment at once
- **THEN** their changes do not run concurrently.

### Setup verifies locked dependencies and readiness before reporting success

Setup SHALL install dependencies from the backend lockfile, verify the installed
dependencies, and recheck readiness before reporting success.

#### Scenario: an accepted setup completes
- **WHEN** the operator accepts the displayed plan and setup finishes installing dependencies
- **THEN** setup reports success only after the locked dependencies and readiness checks pass.

### Failed setup removes only artifacts created by that attempt

When setup fails, it SHALL remove only artifacts created by the current attempt.
Prerequisites requiring manual installation SHALL remain explicit incomplete
results.

#### Scenario: setup fails with manual prerequisites still missing
- **WHEN** an accepted setup fails after creating environment artifacts and a manual prerequisite is unavailable
- **THEN** setup removes its created artifacts, preserves existing files, and reports the manual prerequisite as incomplete.

### The launchd example requires explicit operator configuration

The launchd example SHALL use operator-selected executable and working paths, a
safe `PATH`, and a protected credential-file reference. It SHALL contain no
real username, host path, or secret and SHALL not start automatically.

#### Scenario: an operator reviews the launchd example
- **WHEN** the example is inspected before deliberate configuration
- **THEN** it has operator-selected path placeholders, references only a protected credential file, and requires explicit service registration.
