# TabDat Implementation Boundaries

## Preferred Early Shape

Use the roadmap's vertical slice as the default architecture:

```text
CLI -> Parser -> Executor -> DuckDB/backend
```

Keep boundaries narrow enough that each layer can be tested directly.

## Boundary Responsibilities

CLI shell:

- read commands
- display formatted results and command-level errors
- avoid owning command semantics

Parser:

- turn text into a structured command representation
- validate syntax-level errors
- avoid backend calls

Executor:

- map parsed commands to operations
- validate active dataset state and semantic errors
- coordinate backend calls

Backend:

- load data and run tabular operations
- hide DuckDB, Polars, or Arrow specifics behind small interfaces
- return structured results rather than preformatted terminal text

Formatter:

- convert structured results to terminal output
- keep display choices out of backend operations

## Early Testing Shape

- parser unit tests for command strings
- executor tests with small in-memory or temporary datasets
- backend tests for load/query behavior
- CLI smoke tests for user-visible output

## Implementation Guardrails

- Do not add broad command grammar before the current vertical slice needs it.
- Do not let DuckDB SQL strings become the only command contract; keep command-level structures visible.
- Do not leak raw backend exceptions when a clear command-level error can be produced.
- Prefer deterministic fixtures over large sample data.
