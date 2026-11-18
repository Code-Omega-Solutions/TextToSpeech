# Candidate validation guide

1. Review exact source, model, codec, dependency and reference terms and hashes; prepare a separate private candidate workspace.
2. Convert only the approved Fish 1.5 semantic checkpoint with the documented pinned candidate converter. Confirm actual packed weights and strict configuration/key/shape validation.
3. Review and approve the derived artifacts and runtime independently; do not modify the existing production manifests or trees.
4. Run targeted conversion, launcher, transport, preload and fallback tests. Mocked tests do not establish native synthesis.
5. On Apple Silicon, perform only explicitly authorized bounded validation and synchronize lazy computation before timing. Record exact workload, hardware, quality and memory limitations.
6. Do not deploy or restart services as part of this feature.
