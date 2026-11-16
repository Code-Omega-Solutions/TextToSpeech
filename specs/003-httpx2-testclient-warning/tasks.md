# Implementation Tasks: Remove Starlette TestClient Deprecation Warning

## Phase 1: Setup

- [ ] **T001** Add `httpx2` to backend development dependencies, retain direct `httpx` test usage, and refresh the lock · `backend/pyproject.toml`, `backend/uv.lock`
- [ ] **T002** Review the exact resolved package license and update the backend dependency inventory · `THIRD_PARTY_NOTICES.md`
- [ ] **T003** Run the backend suite with the targeted Starlette warning treated as an error, verify the lock is current, run license-integrity tests, and confirm the runtime dependency group is unchanged · `backend/tests/`, `checks/tests/test_license_integrity.py`
