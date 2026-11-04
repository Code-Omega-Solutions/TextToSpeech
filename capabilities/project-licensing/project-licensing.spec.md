# Project licensing - Living Spec

> Status: Proposed custom terms pending legal review and recovered-source rights
> confirmation. This does not claim that all recovered material has been
> independently cleared for redistribution.

## Purpose

State how project-owned material may be reused and preserve the distinction
between this project and independently licensed dependencies and runtime tools.

## Requirements

### Project materials permit commercial and non-commercial derivatives with attribution
<!-- touches: LICENSE, NOTICE, backend/README.md, frontend/README.md, checks/tests/test_license_integrity.py -->
<!-- adopted: LICENSE, NOTICE, checks/tests/test_license_integrity.py -->

The proposed Code-Omega Attribution License SHALL permit use, copying,
modification, distribution, and sublicensing of covered project materials for
commercial and non-commercial purposes without requiring derivative source
publication. Every derivative SHALL include a prominent statement that it is
based on TextToSpeech by Code-Omega-Solutions; distributed derivatives SHALL
also retain applicable notices.
The custom terms SHALL be identified as a proposal pending legal review and
shall not be represented as OSI-approved.

#### Scenario: derivative software is created or used
- **WHEN** a recipient creates or uses software based on covered project materials
- **THEN** the derivative contains a visible statement that it is based on
  TextToSpeech by Code-Omega-Solutions.

#### Scenario: a derivative is distributed
- **WHEN** a recipient distributes software based on covered project materials
- **THEN** the distribution retains applicable notices and the required attribution.

### Third-party materials retain their own licenses
<!-- touches: THIRD_PARTY_NOTICES.md, SOURCE_OFFER.md, backend/uv.lock, frontend/package-lock.json, frontend/Dockerfile, frontend/tests/docker.test.js, checks/tests/test_license_integrity.py -->
<!-- adopted: THIRD_PARTY_NOTICES.md, SOURCE_OFFER.md, frontend/Dockerfile, frontend/tests/docker.test.js, checks/tests/test_license_integrity.py -->

Project notices SHALL distinguish project-owned material from dependencies and
external runtime components. Dependency lockfiles and published-image package
metadata SHALL remain the inventory sources. A container image SHALL preserve
its packages' copyright/license files, include a versioned package inventory,
and carry a written source offer when permitted by the relevant licenses. The
publisher SHALL fulfill source requests within the period and terms of that
offer.

#### Scenario: a release bundles third-party components
- **WHEN** a release includes a dependency, runtime tool, or base image
- **THEN** its license and required notices are reviewed and included separately
  from the project license.

#### Scenario: a public image includes reciprocal-license packages
- **WHEN** a release publishes an image containing packages with GPL, LGPL, or
  other source-availability conditions
- **THEN** the image carries required notices and a valid written source offer,
  and the publisher can provide the complete corresponding source on request.
  An inventory or SBOM alone is not source delivery.

#### Scenario: a container is rebuilt from a pinned runtime base
- **WHEN** the image is built and distributed
- **THEN** it retains package-level copyright/license files and includes
  traceable runtime package versions and OCI source/revision/notice metadata.

## Uncovered

- The license is a custom proposal, not legal advice or an OSI-approved license.
  Legal review and confirmation of rights to all recovered materials are release
  gates.
- The publisher must maintain the source-request mailbox and actually fulfill
  offers for at least three years after each image release.
- Previously published Alpine-based image digests do not receive the new
  notices, package inventory, or source offer from this source change.
