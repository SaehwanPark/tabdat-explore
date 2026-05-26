# ROP Dependency and Parser Refactor Request Summary

## User Goal

Review and update Railroad-Oriented Programming usage in TabDat-Explore, migrate `comp-builders`
from the previous Git direct dependency to the published PyPI package, make bounded parser-focused
ROP edits, commit meaningful checkpoints, update SDD/workspace docs, and open a review-ready PR.

## Scope

- Start from `main` on temporary branch `temp/rop-comp-builders-pypi-parser`.
- Replace the Git `comp-builders` dependency with PyPI `comp-builders>=1.0.0`.
- Preserve the local `tabdat.monads` boundary for all runtime `comp_builders` imports.
- Expand the boundary to cover async result helpers available in the PyPI package.
- Centralize parser `Result` flow so public `ParseError` conversion remains at the parser edge.
- Update focused tests, SDD docs, workspace handoff artifacts, and PR metadata.

## Constraints

- Preserve all command syntax, parse diagnostics, CLI output, executor behavior, and backend behavior.
- Keep ROP edits focused on parser entry flow and the local monad boundary.
- Use `uv` for dependency and validation commands.
- Keep checkpoints small enough to revert independently.

## Non-goals

- No broad parser rewrite.
- No executor/backend ROP conversion in this PR.
- No Phase 19 command implementation.
- No direct `comp_builders` imports outside `src/tabdat/monads.py`.
