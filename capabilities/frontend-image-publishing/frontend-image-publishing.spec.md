# Frontend image publishing - Living Spec

> [DRAFT] Adopted from the implemented GitHub Actions workflow.

## Purpose

Publish reproducible frontend images from the main branch and limit retained
registry versions without distributing local runtime state.

## Requirements

### Only main publishes frontend images
<!-- touches: .github/workflows/publish-frontend.yml -->
<!-- adopted: .github/workflows/publish-frontend.yml -->

The workflow SHALL publish on pushes to `main`, and allow manual runs only
when the selected ref is `main`. It builds the frontend for Linux AMD64 and
uses the repository token with contents-read and packages-write permissions.

#### Scenario: manual dispatch selects another branch
- **WHEN** a manual run targets a ref other than `main`
- **THEN** the publishing job is skipped.

### Each successful build has a stable latest tag and a unique version
<!-- touches: .github/workflows/publish-frontend.yml -->
<!-- adopted: .github/workflows/publish-frontend.yml -->

The image SHALL use the lowercase owner/repository name with a `-frontend`
suffix in GHCR. Each build publishes `latest` and a unique run/attempt tag
pointing at the same version. A version label differentiates repeated builds.
Build cache stays outside registry image-version retention.

#### Scenario: the same commit is rebuilt
- **WHEN** a new run or attempt publishes the same source
- **THEN** it receives a distinct build tag and version label, and `latest` moves to it.

### Successful publication keeps the five newest versions
<!-- touches: .github/workflows/publish-frontend.yml -->
<!-- adopted: .github/workflows/publish-frontend.yml -->

Publishing and cleanup SHALL be serialized. After successful publication,
cleanup retains the five newest image versions including `latest`; older tagged
and untagged versions are eligible for deletion. Cleanup failures fail the run.
Separate provenance/SBOM manifests are disabled to avoid consuming retention slots.

#### Scenario: a sixth version is published
- **WHEN** publication succeeds and cleanup has package administration permission
- **THEN** only the five newest versions remain.

#### Scenario: publication fails
- **WHEN** image publication fails
- **THEN** the cleanup step is not executed.

## Uncovered

- Registry availability and package administration permissions are external prerequisites.
- Retention is a workflow guarantee dependent on successful cleanup, not a claim
  that six historical images have been published and exercised in a live test.
