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

### Each successful build has a stable tag, unique version and traceable license metadata
<!-- touches: .github/workflows/publish-frontend.yml, frontend/Dockerfile -->
<!-- adopted: .github/workflows/publish-frontend.yml, frontend/Dockerfile -->

The image SHALL use the lowercase owner/repository name with a `-frontend`
suffix in GHCR. Each build publishes `latest` and a unique run/attempt tag
pointing at the same version. A version label differentiates repeated builds.
OCI metadata identifies the source repository, revision, version and in-image
third-party notice/source-offer locations. The final image preserves runtime
package copyright files, fails its build if any package lacks its copyright
file, and includes a versioned package/source inventory.
Build cache stays outside registry image-version retention.

#### Scenario: the same commit is rebuilt
- **WHEN** a new run or attempt publishes the same source
- **THEN** it receives a distinct build tag and version label, and `latest` moves to it.

### Successful publication keeps only the newest version
<!-- touches: .github/workflows/publish-frontend.yml -->
<!-- adopted: .github/workflows/publish-frontend.yml -->

Publishing and cleanup SHALL be serialized. After successful publication,
cleanup retains only the newest image version including `latest`; older tagged
and untagged versions are eligible for deletion. This also removes previously
published image variants that lack the current license notices and source offer.
Cleanup failures fail the run.
Separate provenance/SBOM manifests are disabled to avoid consuming retention slots;
the runtime package inventory is embedded in the image.

#### Scenario: a new version is published
- **WHEN** publication succeeds and cleanup has package administration permission
- **THEN** only the newly published version remains in the package.

#### Scenario: publication fails
- **WHEN** image publication fails
- **THEN** the cleanup step is not executed.

## Uncovered

- Registry availability and package administration permissions are external prerequisites.
- Retention is a workflow guarantee dependent on successful cleanup, not a claim
  that multiple historical images have been published and exercised in a live test.
