from tabdat.monads import Left, Nothing, Right, Some, maybe_from_optional


def test_right_then_applies_next_step() -> None:
  result = Right[str, int](2).then(lambda value: Right(value + 3))

  assert result == Right(5)


def test_left_then_short_circuits() -> None:
  result = Left[str, int]("parse failed").then(lambda value: Right(value + 3))

  assert result == Left("parse failed")


def test_either_folds_left_and_right() -> None:
  left = Left[str, int]("bad").either(lambda error: f"error: {error}", str)
  right = Right[str, int](42).either(lambda error: f"error: {error}", str)

  assert left == "error: bad"
  assert right == "42"


def test_either_maps_success_and_failure_branches() -> None:
  assert Right[str, int](4).map(lambda value: value * 2) == Right(8)
  assert Left[str, int]("bad").map(lambda value: value * 2) == Left("bad")
  assert Left[str, int]("bad").map_left(str.upper) == Left("BAD")


def test_some_maps_binds_and_converts_to_either() -> None:
  value = Some(3)

  assert value.map(lambda number: number + 1) == Some(4)
  assert value.bind(lambda number: Some(number * 2)) == Some(6)
  assert value.maybe(0, lambda number: number + 5) == 8
  assert value.to_either("missing") == Right(3)


def test_nothing_short_circuits_and_converts_to_either() -> None:
  assert Nothing.map(lambda value: value) is Nothing
  assert Nothing.bind(lambda value: Some(value)) is Nothing
  assert Nothing.maybe("fallback", str) == "fallback"
  assert Nothing.to_either("missing") == Left("missing")


def test_maybe_from_optional() -> None:
  assert maybe_from_optional("value") == Some("value")
  assert maybe_from_optional(None) is Nothing
