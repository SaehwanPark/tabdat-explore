# Product Contract: Fix GitHub CI Issues

## Request Summary
Resolve CI workflow failures across Linux and macOS matrix environments.

## Invariants & Fixes

### 1. Rpy2 ABI Mode Configuration
- When R is not pre-installed on standard Linux runners (such as GitHub Actions `ubuntu-latest`), `rpy2-rinterface` must be built in ABI mode.
- Export `RPY2_CFFI_MODE: "ABI"` at workflow level in `.github/workflows/ci.yml` and `.github/workflows/release.yml`.

### 2. Hermetic Wheel Test Fixture
- `tests/test_packaging_and_installer.py::test_wheel_package_contains_topics_and_entrypoints` must not assume `dist/` was populated by an external job.
- If `dist/` contains no `.whl` files, it builds a wheel into `tmp_path` on demand.

### 3. Tool Path in CI
- In `wheel-smoke`, `$HOME/.local/bin` is exported to `$GITHUB_PATH` and invoked directly.

## Acceptance Criteria
- [ ] `pytest tests/test_packaging_and_installer.py` passes cleanly on a fresh checkout without prior `uv build`.
- [ ] GitHub Actions CI workflow passes 100% on `ubuntu-latest`, `macos-latest`, and `wheel-smoke`.
