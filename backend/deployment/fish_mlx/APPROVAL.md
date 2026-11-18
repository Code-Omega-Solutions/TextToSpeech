# Experimental candidate approval

The candidate uses a separate owner-controlled approval document; it does not
alter or replace the existing Fish source, model, codec or reference approvals.
The isolated bootstrap first revalidates those approvals, then binds the derived
weights and conversion metadata, converter and serving code, backend and launcher,
Python interpreter and standard library, Fish dependencies, MLX installation,
requirements, and operating-system version by hash or exact version.

`--review-output` writes a new private document with `status: review-required`.
It does not approve the candidate. A human must review the exact binding,
artifact provenance, terms, reference consent and intended private,
noncommercial use before changing the status to `approved`. Runtime startup
recomputes the binding and rejects changed files, an unapproved document,
unsafe POSIX ownership or write permissions, symlinks, extra candidate files
and overlapping protected trees. Any changed binding requires a new review.
See the feature quickstart for preparation and activation.

An approved binding is not evidence of speech quality, performance, native
qualification, distribution rights, or authorization to deploy.
