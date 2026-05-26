import asyncio

from tabdat.monads import (
  AsyncResult,
  Err,
  Invalid,
  Nothing,
  Ok,
  Some,
  Valid,
  async_result,
  maybe_from_optional,
  option,
  option_maybe,
  option_to_result,
  result,
  result_either,
  validation,
)


def test_result_maps_binds_and_folds_success() -> None:
  value = Ok[int, str](2).map(lambda number: number + 3).bind(lambda number: Ok(number * 2))

  assert value == Ok(10)
  assert result_either(value, lambda error: f"error: {error}", str) == "10"


def test_result_bind_short_circuits_and_folds_error() -> None:
  value = Err[int, str]("parse failed").bind(lambda number: Ok(number + 3))

  assert value == Err("parse failed")
  assert result_either(value, lambda error: f"error: {error}", str) == "error: parse failed"


def test_result_block_short_circuits() -> None:
  @result.block
  def compute(raw: str):
    parsed = yield Ok[int, str](int(raw))
    if parsed < 0:
      return (yield Err[int, str]("must be non-negative"))
    return parsed + 1

  assert compute("2") == Ok(3)
  assert compute("-1") == Err("must be non-negative")


def test_option_maps_binds_and_folds_present_value() -> None:
  value = Some(3).map(lambda number: number + 1).bind(lambda number: Some(number * 2))

  assert value == Some(8)
  assert option_maybe(value, 0, lambda number: number + 5) == 13
  assert option_to_result(value, "missing") == Ok(8)


def test_option_short_circuits_and_converts_absence() -> None:
  assert Nothing.map(lambda value: value) is Nothing
  assert Nothing.bind(lambda value: Some(value)) is Nothing
  assert option_maybe(Nothing, "fallback", str) == "fallback"
  assert option_to_result(Nothing, "missing") == Err("missing")


def test_option_block_short_circuits() -> None:
  @option.block
  def first_clean(items: tuple[str, ...]):
    first = yield Some(items[0]) if items else Nothing
    cleaned = first.strip()
    if not cleaned:
      return (yield Nothing)
    return cleaned

  assert first_clean((" value ",)) == Some("value")
  assert first_clean(()) is Nothing
  assert first_clean((" ",)) is Nothing


def test_validation_accumulates_independent_errors() -> None:
  @validation.block
  def validate_profile(name: str, age: int):
    valid_name = yield Valid(name.strip()) if name.strip() else Invalid("name required")
    valid_age = yield Valid(age) if age >= 0 else Invalid("age must be non-negative")
    return valid_name, valid_age

  assert validate_profile("Ada", 36) == Valid(("Ada", 36))
  assert validate_profile("", -1) == Invalid(("name required", "age must be non-negative"))


def _read_positive(raw: str):
  parsed = yield AsyncResult.from_result(Ok[int, str](int(raw)))
  if parsed < 0:
    return (yield AsyncResult.from_result(Err[int, str]("must be non-negative")))
  return parsed + 1


async def _await_async_result(value: AsyncResult[int, str]):
  return await value


def test_async_result_block_short_circuits() -> None:
  compute = async_result.block(_read_positive)

  assert asyncio.run(_await_async_result(compute("2"))) == Ok(3)
  assert asyncio.run(_await_async_result(compute("-1"))) == Err("must be non-negative")


def test_maybe_from_optional() -> None:
  assert maybe_from_optional("value") == Some("value")
  assert maybe_from_optional(None) is Nothing
