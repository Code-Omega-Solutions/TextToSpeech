# Experimental candidate approval contract

This is a proposed contract, not an implemented approval mechanism. Do not
start a candidate based on this document alone.

A separate private, owner-controlled approval document must bind all of:

- The existing approved source revision and complete source-tree digest; the
  approved original semantic-model tree and decoder digests; and the existing
  source, model and codec terms and private noncommercial intended use.
- The complete approved reference manifest and each of the four qualified
  reference pairs, including their existing consent and dataset terms. Reference
  paths, transcripts and contents must remain private.
- The exact converter and inference source trees and installed runtime files,
  including the MLX and MLX Metal distributions and their platform-specific
  hashes. A version string alone is not a runtime integrity check.
- Every derived file and digest, exact source checkpoint digest, configuration,
  tensor inventory and shapes, 4-bit affine group size 64, excluded matrices,
  converter version and runtime version.

Verification must independently validate the existing approval documents,
check the candidate document's approved status and ownership/permissions, and
recompute all file digests. Reject missing or additional files, symlinks,
overlap with approved source/checkpoint trees, changed terms, incompatible
configuration, and mismatched inventory. No production manifest is rewritten.
