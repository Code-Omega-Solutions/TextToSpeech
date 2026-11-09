# Validation

From `backend/`, run `uv run --locked pytest tests/test_language.py tests/test_models.py tests/test_api.py`.
The tests cover unsupported automatic classifications, explicit locale
selection and validation, short-input defaults, and mocked speech responses.
Passing mocked tests is not native macOS qualification or deployment approval.
