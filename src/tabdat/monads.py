"""Small local monads used for explicit failure and absence handling."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import NoReturn, cast, overload


class Either[E, T]:
  """Recoverable failure or success value with railway-style composition."""

  def then[U](self, step: Callable[[T], Either[E, U]]) -> Either[E, U]:
    raise NotImplementedError

  def either[U](self, left_fn: Callable[[E], U], right_fn: Callable[[T], U]) -> U:
    raise NotImplementedError

  def map[U](self, transform: Callable[[T], U]) -> Either[E, U]:
    return self.then(lambda value: Right(transform(value)))

  def map_left[F](self, transform: Callable[[E], F]) -> Either[F, T]:
    return self.either(lambda error: Left(transform(error)), Right)


@dataclass(frozen=True)
class Left[E, T](Either[E, T]):
  value: E

  def then[U](self, step: Callable[[T], Either[E, U]]) -> Either[E, U]:
    return Left(self.value)

  def either[U](self, left_fn: Callable[[E], U], right_fn: Callable[[T], U]) -> U:
    return left_fn(self.value)


@dataclass(frozen=True)
class Right[E, T](Either[E, T]):
  value: T

  def then[U](self, step: Callable[[T], Either[E, U]]) -> Either[E, U]:
    return step(self.value)

  def either[U](self, left_fn: Callable[[E], U], right_fn: Callable[[T], U]) -> U:
    return right_fn(self.value)


class Maybe[T]:
  """Explicit optional value for pure-core absence handling."""

  def map[U](self, transform: Callable[[T], U]) -> Maybe[U]:
    raise NotImplementedError

  def bind[U](self, step: Callable[[T], Maybe[U]]) -> Maybe[U]:
    raise NotImplementedError

  def maybe[U](self, default: U, some_fn: Callable[[T], U]) -> U:
    raise NotImplementedError

  def to_either[E](self, error: E) -> Either[E, T]:
    raise NotImplementedError


@dataclass(frozen=True)
class Some[T](Maybe[T]):
  value: T

  def map[U](self, transform: Callable[[T], U]) -> Maybe[U]:
    return Some(transform(self.value))

  def bind[U](self, step: Callable[[T], Maybe[U]]) -> Maybe[U]:
    return step(self.value)

  def maybe[U](self, default: U, some_fn: Callable[[T], U]) -> U:
    return some_fn(self.value)

  def to_either[E](self, error: E) -> Either[E, T]:
    return Right(self.value)


@dataclass(frozen=True)
class _Nothing(Maybe[NoReturn]):
  def map[U](self, transform: Callable[[NoReturn], U]) -> Maybe[U]:
    return cast(Maybe[U], self)

  def bind[U](self, step: Callable[[NoReturn], Maybe[U]]) -> Maybe[U]:
    return cast(Maybe[U], self)

  def maybe[U](self, default: U, some_fn: Callable[[NoReturn], U]) -> U:
    return default

  def to_either[E](self, error: E) -> Either[E, NoReturn]:
    return Left(error)


Nothing: _Nothing = _Nothing()
type MaybeValue[T] = Some[T] | _Nothing


@overload
def maybe_from_optional(value: None) -> _Nothing: ...


@overload
def maybe_from_optional[T](value: T) -> Some[T]: ...


def maybe_from_optional[T](value: T | None) -> MaybeValue[T]:
  if value is None:
    return Nothing
  return Some(value)
