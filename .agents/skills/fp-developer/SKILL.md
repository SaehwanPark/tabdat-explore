---
name: fp-developer
description: Apply and enforce a functional-first development workflow with explicit state, pure core logic, typed boundaries, tests-as-specs, and Python/Rust-specific tooling.
---

# fp-developer

## Purpose

Use this skill when writing, reviewing, refactoring, or porting code toward a functional-first style.

Primary goals:

- Make state explicit.
- Keep core logic pure.
- Isolate side effects.
- Use types and tests as contracts.
- Prefer composable functions over hidden orchestration.
- Make code easier for agents and humans to reason about.
- Make cross-language porting safer.

---

# Part 1: General Principles

## Core Architecture

Organize code into:

```text
impure edge -> pure core -> impure edge
````

The pure core should contain domain logic, validation, transformations, scoring, modeling, and decision rules.

The impure edge should contain IO, filesystem access, database calls, logging, randomness, network calls, CLI parsing, environment reads, and framework adapters.

## State

Prefer explicit state passing.

Do:

```text
(new_state, output) = step(old_state, input)
```

Avoid:

```text
object.step(input) mutates hidden internal state
```

State should be:

* Passed as an argument
* Returned when changed
* Represented by typed domain structures
* Kept immutable unless mutation is locally justified

## Functions

Prefer small pure functions.

A good function:

* Has typed inputs and outputs
* Does one thing
* Avoids hidden dependencies
* Does not mutate inputs
* Does not perform IO
* Has deterministic behavior

## Failure and Absence

Represent absence and failure explicitly.

Prefer:

* `Option` / `Maybe` for absence
* `Result` / `Either` for recoverable failure
* Domain-specific error types

Avoid:

* Silent `None`
* Unstructured exceptions as normal control flow
* Boolean success flags without error context
* Stringly typed error states

## Types as Contracts

Use types to encode domain concepts.

Avoid primitive obsession:

```text
user_id: str
```

Prefer domain types where useful:

```text
UserId
```

Use types to make invalid states harder to represent.

## Tests as Specifications

Tests should describe expected behavior, not implementation details.

Treat unit tests as executable contracts. For new core behavior, write or update the focused unit tests before implementing the function. For refactors, first identify the existing contract tests or add them before changing internals.

Every core function should have tests for:

* Happy path
* Invalid input
* Boundary cases
* Absence/failure cases
* State transition behavior, if applicable

For agent work, tests act as executable specs. Do not make broad refactors or introduce new pure-core functions without first understanding or adding tests that lock the intended behavior.

## Portability

Write logic so that porting is translation, not redesign.

Prefer:

```text
config + state + input -> state + output
```

This structure maps well across Python, Rust, ML frameworks, and agent workflows.

---

# Part 2: Lint-Style Checklist

Use this checklist before finalizing any implementation, review, or refactor.

## A. State Checklist

* [ ] Is all required state visible in function signatures?
* [ ] Are state transitions represented as returned values?
* [ ] Are hidden mutable fields avoided?
* [ ] Are globals avoided?
* [ ] Is mutation either eliminated or tightly scoped?
* [ ] Could another agent understand the current state flow from signatures alone?

Red flags:

* Hidden caches
* Implicit lifecycle requirements
* Order-dependent method calls
* Mutable default arguments
* Shared mutable objects
* “Call `init()` before `run()`” protocols

## B. Purity Checklist

* [ ] Is domain logic free of IO?
* [ ] Is randomness injected rather than generated inside core logic?
* [ ] Is time injected rather than read inside core logic?
* [ ] Are logs/metrics emitted at the edge instead of inside core functions?
* [ ] Can the function be tested without mocks?

Red flags:

* Core function reads files
* Core function calls APIs
* Core function accesses environment variables
* Core function mutates external objects
* Core function depends on wall-clock time

## C. Type Checklist

* [ ] Are all public functions typed?
* [ ] Are domain concepts modeled explicitly?
* [ ] Are raw dicts avoided across stable boundaries?
* [ ] Are `None`/null cases reflected in the type?
* [ ] Are recoverable errors reflected in the return type?
* [ ] Are invalid states difficult or impossible to construct?

Red flags:

* `Any`
* Loose dictionaries
* Tuple blobs
* Stringly typed states
* Boolean flags with unclear meaning
* Unvalidated external input

## D. Error Handling Checklist

* [ ] Is absence represented explicitly?
* [ ] Is failure represented explicitly?
* [ ] Are errors typed or structured?
* [ ] Are exceptions reserved for exceptional or boundary failures?
* [ ] Are error cases tested?
* [ ] Does the caller have enough information to recover or report?

Red flags:

* `return None` without explanation
* `except Exception: pass`
* Raising generic exceptions from domain logic
* Encoding errors as strings only
* Losing original error context

## E. Composition Checklist

* [ ] Is the code organized as transformations?
* [ ] Are functions easy to compose?
* [ ] Are intermediate values named clearly?
* [ ] Is branching localized and explicit?
* [ ] Are pipelines readable without hidden side effects?

Red flags:

* Large orchestration methods
* Deeply nested conditionals
* Mixed validation/transformation/IO
* Functions that both compute and persist
* Objects that accumulate unrelated responsibilities

## F. Testing Checklist

* [ ] Do tests define expected behavior?
* [ ] Are pure functions tested directly?
* [ ] Are edge adapters tested separately?
* [ ] Are failure/absence paths tested?
* [ ] Are property-style tests considered for transformations?
* [ ] Can tests serve as porting specs?

Red flags:

* Only integration tests
* Tests require external services
* Tests depend on execution order
* Tests assert implementation details
* No tests for invalid inputs

## G. Agent-Friendliness Checklist

* [ ] Can the agent infer behavior from types, tests, and function names?
* [ ] Is the design documented in markdown-friendly rules?
* [ ] Are invariants explicit?
* [ ] Are side effects isolated?
* [ ] Are functions small enough for targeted edits?
* [ ] Is there a clear boundary between “change this logic” and “do not touch this adapter”?

Red flags:

* Hidden framework magic
* Implicit conventions
* Large classes with many responsibilities
* Scattered state mutation
* Behavior only explained in comments, not types/tests

---

# Part 3: Python Setup

## Recommended Tooling

Use:

* `mypy` for static type checking
* `pydantic` for validated boundary models
* `pymonad` for functional absence/failure/composition primitives
* `pytest` for tests

Add any missing dependencies via configured dependency manager (`uv` preferred). If project dependency policy blocks adding `pymonad`, use lightweight local `Result` / `Option` helpers as a fallback.

## Python Rules

### Type Everything Public

All public functions must have full type annotations.

Avoid:

```python
def process(x):
  ...
```

Prefer:

```python
def process(input: Input) -> Output:
  ...
```

### Use Pydantic at Boundaries

Use Pydantic models for external inputs, configs, and serialized data.

```python
from pydantic import BaseModel

class TrainConfig(BaseModel):
  learning_rate: float
  batch_size: int
  seed: int
```

Do not pass raw external dictionaries deep into core logic.

### Prefer Frozen Domain Models

Prefer immutable models where practical.

```python
from pydantic import BaseModel, ConfigDict

class ModelState(BaseModel):
  model_config = ConfigDict(frozen=True)

  step: int
  loss: float
```

### Avoid Hidden Mutation

Avoid mutating inputs.

Bad:

```python
def add_item(items: list[str], item: str) -> None:
  items.append(item)
```

Good:

```python
def add_item(items: tuple[str, ...], item: str) -> tuple[str, ...]:
  return (*items, item)
```

### Represent Failure Explicitly

Use `Optional` only for true absence.

Use PyMonad for absence and recoverable failure when dependency policy allows.

Prefer:

* `Maybe` / `Option`-style values for absence
* `Either` / `Result`-style values for recoverable failure
* `map`, bind/then-style composition, and pure transformation pipelines

Avoid deeply nested conditionals or exception-driven control flow for expected domain failures.

Keep monadic values in the pure/domain layer where they clarify composition. Convert at impure edges when frameworks, serializers, or external APIs expect plain Python values.

If `pymonad` is not available, use lightweight structured results for recoverable failure.

```python
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")

@dataclass(frozen=True)
class Ok(Generic[T]):
  value: T

@dataclass(frozen=True)
class Err(Generic[E]):
  error: E

Result = Ok[T] | Err[E]
```

### Keep Core Logic Mock-Free

If a function requires mocks to test, it probably contains effects. Move those effects outward.

Preferred shape:

```python
def compute_metrics(predictions: Predictions, labels: Labels) -> Metrics:
  ...

def load_predictions(path: Path) -> Predictions:
  ...
```

### Python Commands

Run before finalizing:

```bash
uvx mypy .
uvx pytest
```
(parameters might vary depending on codebase directory structures)

When available, also run the project’s formatter/linter.

---

# Part 4: Rust Setup

## Recommended Tooling

Use:

* `cargo test`
* `cargo clippy`
* `cargo fmt`
* `Option`
* `Result`
* Domain `struct` and `enum` types

## Rust Rules

### Prefer Immutable Bindings

Default to:

```rust
let value = compute(input);
```

Use `mut` only when it materially improves clarity or performance.

### Model Domains Explicitly

Avoid primitive obsession.

Bad:

```rust
fn train(model_type: String, status: String) {}
```

Good:

```rust
enum ModelType {
  Transformer,
  Linear,
}

enum TrainingStatus {
  Pending,
  Running,
  Finished,
  Failed,
}
```

### Use `Option` for Absence

```rust
fn find_user(id: UserId, users: &[User]) -> Option<User> {
  users.iter().find(|user| user.id == id).cloned()
}
```

### Use `Result` for Recoverable Failure

```rust
fn parse_config(raw: &str) -> Result<Config, ConfigError> {
  ...
}
```

Prefer domain-specific error enums.

### Compose with `map` and `and_then`

```rust
fn process(raw: &str) -> Result<Output, Error> {
  parse(raw)
    .and_then(validate)
    .map(transform)
}
```

### Keep IO at the Edge

Bad:

```rust
fn compute_score(path: &Path) -> Result<Score, Error> {
  let raw = std::fs::read_to_string(path)?;
  ...
}
```

Good:

```rust
fn compute_score(input: &Input) -> Score {
  ...
}

fn load_input(path: &Path) -> Result<Input, Error> {
  ...
}
```

### Avoid Fighting the Borrow Checker

If lifetimes become complex, revisit the data flow.

Prefer:

* Clear ownership
* Small structs
* Explicit state passing
* Owned domain values where appropriate

Do not introduce unsafe code to preserve an unnecessarily stateful design.

### Rust Commands

Run before finalizing:

```bash
cargo fmt
cargo clippy -- -D warnings
cargo test
```

---

# Part 5: Review Protocol for Agents

When reviewing or modifying code:

1. Identify the pure core and impure edge.
2. Check whether state is explicit.
3. Check whether errors and absence are typed.
4. Check whether tests describe behavior.
5. Add or update unit tests as contracts before implementing new core behavior or refactoring internals.
6. Refactor toward small pure functions.
7. Keep adapters thin.
8. Run relevant unit tests, then type checks and broader tests where configured.
9. Report remaining violations clearly.

When proposing changes, prefer small diffs that improve one of:

* Explicit state
* Purity
* Type contracts
* Error modeling
* Testability
* Portability

Do not introduce clever abstractions unless they reduce hidden context.

---

# Part 6: Final Response Expectations

When using this skill, summarize:

* What functional-first changes were made
* What state/effects were made explicit
* What tests/type checks were run
* Any remaining non-FP compromises
* Any follow-up refactors worth considering
