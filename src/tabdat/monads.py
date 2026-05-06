"""Functional helper boundary for explicit failure and absence handling.

TabDat imports computational helpers through this module so the pure core has a
stable repo-local vocabulary while the implementation delegates to comp-builders.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import NoReturn, overload

from comp_builders import (
  Err,
  Invalid,
  Nothing,
  Ok,
  Option,
  Result,
  Some,
  Valid,
  Validation,
  option,
  result,
  validation,
)

type MaybeValue[T] = Some[T] | Option[NoReturn]


def result_either[T, E, U](
  value: Result[T, E],
  error_fn: Callable[[E], U],
  success_fn: Callable[[T], U],
) -> U:
  """Fold a Result into one value at an impure edge."""
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
  """Fold an Option into one value at an impure edge."""
  match value:
    case Some(present):
      return some_fn(present)
  if value is Nothing:
    return default
  raise TypeError(f"unsupported Option value: {type(value).__name__}")


def option_to_result[T, E](value: Option[T], error: E) -> Result[T, E]:
  """Convert expected absence into a recoverable failure value."""
  match value:
    case Some(present):
      return Ok(present)
  if value is Nothing:
    return Err(error)
  raise TypeError(f"unsupported Option value: {type(value).__name__}")


@overload
def maybe_from_optional(value: None) -> Option[NoReturn]: ...


@overload
def maybe_from_optional[T](value: T) -> Some[T]: ...


def maybe_from_optional[T](value: T | None) -> MaybeValue[T]:
  if value is None:
    return Nothing
  return Some(value)


__all__ = [
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
  "maybe_from_optional",
  "option",
  "option_maybe",
  "option_to_result",
  "result",
  "result_either",
  "validation",
]
