# Project licensing - Evidence map

Policy artifacts are not legal opinions. Integrity tests verify that required
terms and audit limitations remain visible, but do not establish legal validity
or confirm ownership of every included material.

| Requirement | Evidence reference | Evidence scope |
| --- | --- | --- |
| Project materials permit commercial and non-commercial derivatives with attribution | [LICENSE](../../LICENSE), [NOTICE](../../NOTICE), [backend/README.md](../../backend/README.md), [frontend/README.md](../../frontend/README.md), [checks/tests/test_license_integrity.py](../../checks/tests/test_license_integrity.py) | Proposed grant, required derivative attribution, public status notice, and textual integrity check |
| Third-party materials retain their own licenses | [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md), [SOURCE_OFFER.md](../../SOURCE_OFFER.md), [backend/uv.lock](../../backend/uv.lock), [frontend/package-lock.json](../../frontend/package-lock.json), [frontend/Dockerfile](../../frontend/Dockerfile), [frontend/tests/docker.test.js](../../frontend/tests/docker.test.js), [checks/tests/test_license_integrity.py](../../checks/tests/test_license_integrity.py) | Lockfile findings, preserved Debian copyright files, generated runtime package inventory, written source offer, image-label and file assertions; fulfilling source requests remains an operational obligation |
| Optional VibeVoice assets and worker require separate review | [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md), [backend/vibevoice_worker/pyproject.toml](../../backend/vibevoice_worker/pyproject.toml), [backend/vibevoice_worker/uv.lock](../../backend/vibevoice_worker/uv.lock), [backend/README.md](../../backend/README.md), [checks/tests/test_license_integrity.py](../../checks/tests/test_license_integrity.py) | Exact-version PyPI metadata was reviewed and surfaced LGPL/MPL declarations, conditional NVIDIA proprietary metadata, and freeform-only records. Exact distributions and notices, model/voice artifact provenance, and intended-use approval remain unresolved; metadata is not legal clearance or release approval. |
