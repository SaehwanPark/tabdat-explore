# Contributing to TabDat-Explore

Thank you for your interest in contributing. This guide covers development setup, validation, and
where to find deeper technical documentation.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) for environment and command execution

## Development setup

Clone the repository and sync dependencies:

```bash
git clone https://github.com/SaehwanPark/tabdat-explore.git
cd tabdat-explore
uv sync
```

Run the CLI locally:

```bash
uv run tabdat
```

## Validation

Run these checks before opening a pull request:

```bash
uv run mypy
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Fix formatting with `uv run ruff format .` when needed.

## Development expectations

- Use a **2-space** indent across project files.
- Follow **spec-driven** and **test-driven** development: update specs and add focused tests with
  new behavior.
- Prefer **functional-first** style with typed boundaries (`pydantic`, `basedpyright`) and explicit
  error handling via `tabdat.monads`.
- Keep command contracts predictable: Stata-inspired ergonomics, not Stata compatibility.

Agent-oriented workflows and tooling notes live in [AGENTS.md](AGENTS.md).

## Documentation map

| Document | Purpose |
|----------|---------|
| [AGENTS.md](AGENTS.md) | Repository-wide agent and contributor conventions |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Runtime flow, component boundaries, implementation detail |
| [SPEC.md](SPEC.md) | Feature state and verification criteria |
| [docs/dev_phase.md](docs/dev_phase.md) | Development roadmap and phase plan |
| [docs/project_proposal.md](docs/project_proposal.md) | Product intent and target users |
| [docs/phase0_product_guardrails.md](docs/phase0_product_guardrails.md) | Scope guardrails and non-goals |
| [docs/command_glossary_v0.md](docs/command_glossary_v0.md) | Historical Phase 0 command glossary |
| [docs/command-reference.md](docs/command-reference.md) | Current user-facing command index |
| [docs/user-guide.md](docs/user-guide.md) | End-user workflows and behavior |
| [docs/harness/tabdat/team-spec.md](docs/harness/tabdat/team-spec.md) | Multi-agent development harness |

## Agent skills

Reusable agent workflows live under `.agents/skills/`:

- `tabdat-orchestrator` — coordinate command contracts, implementation, and QA
- `tabdat-core-implementer` — vertical-slice implementation
- `tabdat-product-architect` — command semantics and acceptance criteria
- `tabdat-qa-reviewer` — cross-boundary coherence review
