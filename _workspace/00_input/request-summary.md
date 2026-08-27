# Request Summary: Fix GitHub CI Issues

## Goal
Fix failures in GitHub Actions CI workflows:
1. `rpy2-rinterface` compilation failure on Ubuntu Linux runners by setting `RPY2_CFFI_MODE=ABI`.
2. `test_wheel_package_contains_topics_and_entrypoints` failure on fresh checkouts by building wheel on-demand into a temporary fixture directory if not pre-built in `dist/`.
3. `wheel-smoke` tool PATH discovery in GitHub Actions runners.

## Phase Fit
Phase 26 (CI & Release Automation).

## Touched Surfaces
- `.github/workflows/ci.yml`: Workflow environment and PATH.
- `.github/workflows/release.yml`: Workflow environment.
- `tests/test_packaging_and_installer.py`: Hermetic wheel test fixture.
- `scripts/install.sh`: Export ABI mode environment variable.
