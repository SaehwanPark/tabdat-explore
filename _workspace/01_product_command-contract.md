# Phase 11 Completion Command Contract

## Request Summary

Finish the remaining Phase 11 prerequisites before Phase 12 by adding minimal script control flow
and narrow remote Parquet loading.

## Roadmap Phase

Phase 11: Data Workflow & Reproducibility Primitives.

## Script Control Flow

### Syntax

```stata
if <condition>
  command
else
  command
end
```

Rules:

- `if`, `else`, and `end` are script-only directives.
- A block may omit `else`.
- Conditions are evaluated after macro expansion.
- Supported conditions:
  - `true`, `on`, and `1` evaluate true.
  - `false`, `off`, and `0` evaluate false.
  - `<left> == <right>` and `<left> != <right>` compare trimmed token text.
- Commands inside an inactive branch are skipped and not echoed.
- Nested `if` blocks are not supported in this slice.
- Existing `seed`, `let`, `$macro`, and nested `run` behavior remains unchanged.

### User-Facing Errors

- Missing condition: `if expects a condition`
- Unsupported condition: `if condition expects true/false, 1/0, on/off, ==, or !=`
- Stray `else`: `else without matching if`
- Stray `end`: `end without matching if`
- Duplicate `else`: `if block already has an else branch`
- Nested blocks: `nested if blocks are not supported`
- Unterminated block: `if block is missing end`

## Remote Parquet Loading

### Syntax

```stata
use https://example.com/data.parquet
use s3://bucket/path/data.parquet, lazy
```

Rules:

- `use` accepts local paths and remote URIs with `http://`, `https://`, or `s3://`.
- All `use` targets must end in `.parquet`.
- Remote targets are passed to DuckDB `read_parquet`.
- `use <uri>, lazy` creates the same DuckDB scan-view boundary as local lazy loads.
- Unsupported URI schemes fail before DuckDB execution.
- Local path validation remains unchanged.
- Remote credentials, config, and DB connections are out of scope.

### User-Facing Errors

- Unsupported remote scheme: `use remote Parquet supports http, https, and s3 URLs`
- Non-Parquet target: `use only supports .parquet files`

## Acceptance Criteria

- Script helper tests cover conditional parsing/evaluation, branch selection, macro-expanded
  conditions, and diagnostics.
- CLI tests cover script output for true/false/else branches and line-numbered control-flow
  failures.
- Parser/backend tests cover remote `use` syntax and backend remote URI classification without
  depending on live internet.
- Existing parser, executor, CLI, shell, and script behavior remains compatible.
- Durable docs and `_workspace/` artifacts record Phase 11 completion and remaining future work.
