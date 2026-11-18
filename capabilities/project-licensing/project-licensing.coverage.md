# Project licensing - Evidence map

Policy artifacts are not legal opinions. Integrity tests verify that required
terms and audit limitations remain visible, but do not establish legal validity
or confirm ownership of every included material.

The voice-preparation guide also identifies the operator-managed external
downloaded-input archive, its checksum/restore process and unencrypted local
storage boundary. This is documentary recovery guidance, not evidence that the
operator's encrypted backup completed or that a full system restore succeeded.

| Requirement | Evidence reference | Evidence scope |
| --- | --- | --- |
| Project materials permit commercial and non-commercial derivatives with attribution | [LICENSE](../../LICENSE), [NOTICE](../../NOTICE), [backend/README.md](../../backend/README.md), [frontend/README.md](../../frontend/README.md), [checks/tests/test_license_integrity.py](../../checks/tests/test_license_integrity.py) | Proposed grant, required derivative attribution, public status notice, and textual integrity check |
| Third-party materials retain their own licenses | [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md), [SOURCE_OFFER.md](../../SOURCE_OFFER.md), [backend/uv.lock](../../backend/uv.lock), [frontend/package-lock.json](../../frontend/package-lock.json), [frontend/Dockerfile](../../frontend/Dockerfile), [frontend/tests/docker.test.js](../../frontend/tests/docker.test.js), [checks/tests/test_license_integrity.py](../../checks/tests/test_license_integrity.py) | Lockfile findings, preserved Debian copyright files, generated runtime package inventory, written source offer, image-label and file assertions; fulfilling source requests remains an operational obligation |
| Optional VibeVoice assets and worker require separate review | [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md), [backend/vibevoice_worker/pyproject.toml](../../backend/vibevoice_worker/pyproject.toml), [backend/vibevoice_worker/uv.lock](../../backend/vibevoice_worker/uv.lock), [backend/README.md](../../backend/README.md), [backend/app/config.py](../../backend/app/config.py), [backend/tests/test_config.py](../../backend/tests/test_config.py), [checks/tests/test_license_integrity.py](../../checks/tests/test_license_integrity.py) | Owner-authorized private R&D requires an explicit research-only setting. Exact package artifacts and notices, model/voice provenance, German support, and safeguard behavior remain unverified; production and redistribution stay blocked. |
| Fish preparation separates documentation from restricted assets | [backend/voice-preparation.md](../../backend/voice-preparation.md), [backend/README.md](../../backend/README.md) | Documented storage/acquisition and review policy, including explicitly authorized non-sensitive checkpoint backups with provenance/license/hash records; not automated upload prevention or legal clearance. Voice/personal data remain excluded. Private Git hosting does not override dataset agreements or resolve voice/output privacy, and does not qualify or enable Fish. |
