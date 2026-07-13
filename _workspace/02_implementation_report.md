# Implementation Report: Phase 24 P0 Identifier Spelling and Quoted Identifiers

## Contract Consumed

- `_workspace/01_product_command-contract.md` — exact identifier spelling and backtick-quoting policy.

## Delivered Boundary

- `src/tabdat/parser.py`
  - Adds backtick-quoted identifier tokens with doubled-backtick escaping.
  - Keeps quoted identifiers distinct from unquoted command/control keywords.
  - Treats punctuation inside quoted identifiers as identifier content rather than command or
    expression syntax.
- Makes `by` and Bayes-prefix framing quote-aware and preserves positional quote metadata for
  command-level control words.
- Rejects unquoted punctuation in variable positions while retaining path parsing for `save`,
  `export`, and `set`.
- `src/tabdat/executor.py`
  - Quotes Bayes formula identifiers for the formula backend and explicitly rejects names containing
    an unrepresentable backtick.
- `tests/test_parser.py` and `tests/test_executor.py`
  - Cover whitespace, punctuation, escaped backticks, quoted `if`, exact case, variable lists,
    generated targets, replacement expressions, wrapper/control parsing, and unknown exact-spelling
    diagnostics.
- `tests/test_cli.py`
  - Covers `-c`, script execution, and a Unicode quoted identifier.
- `docs/language-semantics.md`, `docs/user-guide.md`, `SPEC.md`, `CHANGELOG.md`, and `_workspace/`
  - Record the stable spelling/quoting policy and the bounded follow-up scope.

## Implementation Notes By Boundary

- Bare identifiers retain existing exact, case-sensitive resolution and Unicode spelling.
- Backtick quoting is accepted only in variable positions and expression references; command names
  and option names remain unquoted keywords.
- Parser structural checks now inspect token kind, so quoted names containing `,`, `=`, `(`, `)`, or
  expression operators remain single identifiers.
- `by` and Bayes-prefix delimiters are found from unquoted symbol tokens, preserving colons inside
  quoted identifiers.
- Backend execution reuses the existing identifier quoting boundary, and the Bayes formula boundary
  receives safe backtick-wrapped names.

## Validation Commands And Outcomes

- `uv run pytest tests/test_parser.py -q` — passed, 488 tests.
- `uv run pytest tests/test_executor.py -k 'quoted_identifiers_execute or bayes_formula_identifier' -q` — passed, 2 tests.
- `uv run pytest tests/test_cli.py -k 'quoted_identifier or quoted_unicode_identifier' -q` — passed, 2 tests.
- `uv run basedpyright` — passed, 0 errors, warnings, or notes.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed, 34 files already formatted.
- `git diff --check` — passed.
- `uv run pytest` — passed, 976 tests, with 314 existing third-party warnings.
- `uv run python integrated_testing/run_e2e.py` — passed; all six integrated scenarios completed,
  including exact canonical replay.

## Known Limits And Follow-Up Work

- Missing values, coercion, arithmetic, categories, ordering, randomness, estimation samples,
  machine output, exit semantics, and full operation lineage remain separate Phase 24 slices.
- SQL identifiers retain SQL's own grammar and are intentionally outside this command-language slice.
