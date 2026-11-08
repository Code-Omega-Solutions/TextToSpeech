# Isolation and Publication Boundary

This is a prerequisite for implementation, not a claim that controls have
already been installed or verified. The authorized operator chooses a private,
owner-controlled directory on local storage outside every Git worktree, Git
directory, build context, shared workspace, backup/sync/upload location and
release staging tree. Check real paths and ancestors, mount/sync settings and
symlinks; fail closed if any are unknown. Use restrictive owner-only directory
and file permissions, no shared accounts, and an approved local retention and
backup policy. No Git repository, submodule, worktree, symlink or hard link may
point from a publishable tree into private material.

The entire prototype source, tests, environments, weight caches, reference
recordings, consent/derived voice data, text, generated audio, raw measurements,
private reports, archives and copies stay inside that private boundary. Configure
all runtime, model, temporary and cache paths there explicitly; reject defaults
that escape it. Deny network access during inference and evaluation where the
host can enforce it; verify attempted egress is blocked. If enforcement cannot
be verified, stop rather than assuming an offline setting is sufficient. Any
future model acquisition is separately approved and reviewed, not part of this
planning run.

## Pre-implementation gate

1. Record the private root and resolved paths privately; check ownership,
   permissions, free space and quotas, absence of links and exclusion from
   repository/build/sync/upload/backup paths.
2. Place harmless synthetic canaries representing code, weights, recording,
   generated audio and a report in the private root. Independently test the
   actual candidate commit path, build context/image inspection, archive,
   upload and release staging mechanisms. Their inventories must contain zero
   canaries and zero links to the private root. If no such mechanism exists,
   mark it not applicable with rationale; repeat when one is introduced.
3. Inspect `git status --ignored`, proposed index and diff, untracked and
   ignored candidates, packaging manifests, Docker/other build contexts,
   image layers, CI uploads and release attachments. Ignore rules are
   defense-in-depth only: `git add -f`, archive tools, symlinks and broad
   contexts can bypass them. Use explicit allowlists and independently inspect
   the bytes actually staged for publication.
4. Scan every commit in the actual proposed push range, not only the current
   tree. Any prototype material or canary in history blocks publication even if
   later deleted. Do not rewrite or push history as part of this plan; escalate.
5. Store evidence and canary names privately; remove only test canaries after
   verification. A failure blocks implementation and release, and requires a
   fresh boundary review. Repeat before every new publication channel or
   proposed release.

The specification and plan may be reviewed for publication only after checking
that examples are synthetic and contain no private operational details. A
later explicit decision to publish prototype code is necessary but insufficient:
rights, consent, dependencies, security, history and release artifacts still
require separate review and approval. No such decision is made here.
