"""Functional helper boundary for explicit failure and absence handling.

TabDat imports computational helpers through this module so the pure core has a
stable repo-local vocabulary while the implementation delegates to comp_builders.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import NoReturn

from comp_builders import (
  AsyncResult,
  Err,
  Invalid,
  Nothing,
  Ok,
  Option,
  Result,
  Some,
  Valid,
  Validation,
  async_result,
  option,
  result,
  validation,
)

# Option[NoReturn] is explicitly used for the Nothing variant because comp_builders.Option
# is invariant. This union design matches type checks under basedpyright for empty options.
type MaybeValue[T] = Some[T] | Option[NoReturn]


def result_either[T, E, U](
  value: Result[T, E],
  error_fn: Callable[[E], U],
  success_fn: Callable[[T], U],
) -> U:
  """Fold a Result into one value at an impure boundary edge.

  Avoids repetitive pattern-matching blocks at application boundaries (e.g., CLI,
  shell, or I/O entry points) where functional monadic structures must be translated
  into user-facing output or system exceptions.

  Args:
    value: The monadic Result container (either Ok or Err).
    error_fn: Callable mapping the error value E to the return type U.
    success_fn: Callable mapping the success value T to the return type U.

  Returns:
    The mapped value of type U.

  Raises:
    TypeError: If the value is not an instance of Ok or Err.
  """
  match value:
    case Ok(success):
      return success_fn(success)
    case Err(error):
      return error_fn(error)
  raise TypeError(f"unsupported Result value: {type(value).__name__}")


def option_maybe[T, U](
  value: Option[T],
  default: U,
  some_fn: Callable[[T], U],
) -> U:
  """Fold an Option into one value at an impure boundary edge.

  Standardizes resolving optional states at boundaries by providing a fallback value
  for Nothing or applying a transform function for Some(T).

  Args:
    value: The Option container (Some or Nothing).
    default: The fallback value of type U to return if the Option is Nothing.
    some_fn: Callable mapping the wrapped value T to the return type U.

  Returns:
    The mapped value or the default fallback value.

  Raises:
    TypeError: If the value is not Some or Nothing.
  """
  match value:
    case Some(present):
      return some_fn(present)
  if value is Nothing:
    return default
  raise TypeError(f"unsupported Option value: {type(value).__name__}")


def option_to_result[T, E](value: Option[T], error: E) -> Result[T, E]:
  """Convert expected absence (Option) into a recoverable failure (Result).

  Translates an expected/allowed missing state (Nothing) into an explicit error
  condition (Err) when a value is strictly required downstream.

  Args:
    value: The Option container to convert.
    error: The error value E to wrap in Err if the Option is Nothing.

  Returns:
    Ok containing the wrapped value, or Err containing the provided error.

  Raises:
    TypeError: If the value is not Some or Nothing.
  """
  match value:
    case Some(present):
      return Ok(present)
  if value is Nothing:
    return Err(error)
  raise TypeError(f"unsupported Option value: {type(value).__name__}")


def maybe_from_optional[T](value: T | None) -> MaybeValue[T]:
  """Convert a standard Python Optional (T | None) to a monadic Option (MaybeValue[T]).

  Bridges standard Python APIs returning None with the repository's functional
  monadic constructs to preserve pipeline purity.

  Args:
    value: The value which may be None.

  Returns:
    Some(value) if the value is not None, otherwise Nothing.
  """
  if value is None:
    return Nothing
  return Some(value)


__all__ = [
  "AsyncResult",
  "Err",
  "Invalid",
  "MaybeValue",
  "Nothing",
  "Ok",
  "Option",
  "Result",
  "Some",
  "Valid",
  "Validation",
  "async_result",
  "maybe_from_optional",
  "option",
  "option_maybe",
  "option_to_result",
  "result",
  "result_either",
  "validation",
]
