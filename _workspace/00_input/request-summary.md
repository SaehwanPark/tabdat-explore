# Request Summary: Phase 23 — Data Recoding & Ingestion Expansion

## Goal
Continue TabDat developments by implementing:
1. `recode` command for Stata-style numeric/categorical data recoding.
2. Ingestion expansion in `use` command to support `.csv`, `.feather`, and `.arrow` formats.

## Phase Fit
Phase 23: Data Recoding & Ingestion Expansion.

## Touched Surfaces
- `models.py` (Command definitions)
- `parser.py` (Parsing grammar)
- `executor.py` (Execution mapping)
- `backend.py` (File loaders and query logic)
- `shell.py` (CLI autocomplete & highlights)
- Tests (`test_parser.py`, `test_executor.py`, `test_cli.py`)

## Assumptions
- Lazy mode is restricted to Parquet.
- Range-based recodes are numeric-only.

## Non-Goals
- Complex multi-conditional recodes.
- Other formats like Excel/JSON.
