from pathlib import Path

import pytest

from tabdat.config import TabDatConfig
from tabdat.errors import (
  ExecutionError,
  NoActiveDatasetError,
  TypeMismatchExecutionError,
  UnknownTableError,
  UnknownVariableError,
)
from tabdat.executor import Executor
from tabdat.models import (
  ActivateResult,
  BarCommand,
  BinaryExpression,
  ByCommand,
  CodebookCommand,
  CodebookResult,
  CollapseCommand,
  CountCommand,
  CountResult,
  DescribeCommand,
  DescribeResult,
  DropCommand,
  FunctionCallExpression,
  GenerateCommand,
  HeadCommand,
  HistogramCommand,
  IdentifierExpression,
  KeepCommand,
  LoadResult,
  NumberExpression,
  ParsedCommand,
  PlotResult,
  PreviewResult,
  RenameCommand,
  ReplaceCommand,
  SaveCommand,
  SaveResult,
  ScatterCommand,
  SelectCommand,
  SetCommand,
  SetResult,
  SqlCommand,
  SqlCreateResult,
  StringExpression,
  SummarizeCommand,
  SummarizeResult,
  TableResult,
  TabulateCommand,
  TailCommand,
  TransformResult,
  UseCommand,
)


def test_use_loads_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    result = executor.execute(UseCommand(sample_parquet))
  finally:
    executor.close()

  assert isinstance(result, LoadResult)
  assert result.dataset.row_count == 3
  assert result.dataset.column_count == 4
  assert result.dataset.execution_mode == "eager"
  assert result.dataset.lazy_engine is None
  assert [column.name for column in result.dataset.columns] == ["age", "bmi", "sex", "cost"]


@pytest.mark.parametrize("engine", ["duckdb", "polars"])
def test_use_lazy_loads_active_dataset(sample_parquet: Path, engine: str) -> None:
  executor = Executor()
  try:
    result = executor.execute(
      UseCommand(sample_parquet, execution_mode="lazy", lazy_engine=engine)  # type: ignore[arg-type]
    )
  finally:
    executor.close()

  assert isinstance(result, LoadResult)
  assert result.dataset.row_count is None
  assert result.dataset.column_count == 4
  assert result.dataset.execution_mode == "lazy"
  assert result.dataset.lazy_engine == engine


def test_failing_lazy_use_preserves_existing_active_dataset(
  sample_parquet: Path,
  tmp_path: Path,
) -> None:
  corrupt_parquet = tmp_path / "corrupt.parquet"
  corrupt_parquet.write_text("not parquet")
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="use could not read Parquet file"):
      executor.execute(UseCommand(corrupt_parquet, execution_mode="lazy", lazy_engine="duckdb"))
    result = executor.execute(CountCommand())
  finally:
    executor.close()

  assert isinstance(result, CountResult)
  assert result.row_count == 3


def test_count_queries_lazy_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet, execution_mode="lazy", lazy_engine="duckdb"))
    result = executor.execute(CountCommand())
  finally:
    executor.close()

  assert isinstance(result, CountResult)
  assert result.row_count == 3


@pytest.mark.parametrize("engine", ["duckdb", "polars"])
def test_lazy_transformations_compose_before_terminal_results(
  sample_parquet: Path,
  engine: str,
) -> None:
  executor = Executor()
  try:
    executor.execute(
      UseCommand(sample_parquet, execution_mode="lazy", lazy_engine=engine)  # type: ignore[arg-type]
    )
    executor.execute(SelectCommand(("age", "sex", "cost")))
    executor.execute(
      KeepCommand(
        condition=BinaryExpression(
          left=IdentifierExpression("age"),
          operator=">=",
          right=NumberExpression(42),
        )
      )
    )
    result = executor.execute(HeadCommand(5))
  finally:
    executor.close()

  assert isinstance(result, PreviewResult)
  assert result.columns == ("age", "sex", "cost")
  assert result.rows == ((42, "M", 150.0), (54, "F", None))


def test_describe_requires_active_dataset() -> None:
  executor = Executor()
  try:
    with pytest.raises(ExecutionError, match="describe requires an active dataset"):
      executor.execute(DescribeCommand())
  finally:
    executor.close()


def test_describe_returns_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(DescribeCommand())
  finally:
    executor.close()

  assert isinstance(result, DescribeResult)
  assert result.dataset.row_count == 3
  assert result.dataset.columns[0].name == "age"


def test_summarize_requested_numeric_columns(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(SummarizeCommand(("age", "cost")))
  finally:
    executor.close()

  assert isinstance(result, SummarizeResult)
  assert [row.variable for row in result.rows] == ["age", "cost"]
  age = result.rows[0]
  cost = result.rows[1]
  assert age.count == 3
  assert age.mean == 42
  assert age.minimum == 30
  assert age.maximum == 54
  assert cost.count == 2
  assert cost.mean == 125


def test_summarize_without_variables_uses_all_numeric_columns(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(SummarizeCommand(()))
  finally:
    executor.close()

  assert isinstance(result, SummarizeResult)
  assert [row.variable for row in result.rows] == ["age", "bmi", "cost"]


def test_summarize_rejects_missing_column(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="summarize unknown variable: missing"):
      executor.execute(SummarizeCommand(("missing",)))
  finally:
    executor.close()


def test_summarize_rejects_non_numeric_column(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="summarize requires numeric variables: sex"):
      executor.execute(SummarizeCommand(("sex",)))
  finally:
    executor.close()


def test_codebook_profiles_requested_columns(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(CodebookCommand(("age", "cost")))
  finally:
    executor.close()

  assert isinstance(result, CodebookResult)
  assert [row.variable for row in result.rows] == ["age", "cost"]
  age = result.rows[0]
  cost = result.rows[1]
  assert age.nonmissing == 3
  assert age.missing == 0
  assert age.distinct == 3
  assert age.examples == (30, 42, 54)
  assert cost.nonmissing == 2
  assert cost.missing == 1
  assert cost.distinct == 2


def test_codebook_without_variables_profiles_all_columns(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(CodebookCommand(()))
  finally:
    executor.close()

  assert isinstance(result, CodebookResult)
  assert [row.variable for row in result.rows] == ["age", "bmi", "sex", "cost"]


def test_codebook_rejects_missing_column(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="codebook unknown variable: missing"):
      executor.execute(CodebookCommand(("missing",)))
  finally:
    executor.close()


def test_count_returns_active_dataset_row_count(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(CountCommand())
  finally:
    executor.close()

  assert isinstance(result, CountResult)
  assert result.row_count == 3


def test_head_returns_first_rows(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(HeadCommand(2))
  finally:
    executor.close()

  assert isinstance(result, PreviewResult)
  assert result.columns == ("age", "bmi", "sex", "cost")
  assert result.rows == ((30, 22.5, "F", 100.0), (42, 25.0, "M", 150.0))


def test_tail_returns_last_rows(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(TailCommand(2))
  finally:
    executor.close()

  assert isinstance(result, PreviewResult)
  assert result.columns == ("age", "bmi", "sex", "cost")
  assert result.rows == ((42, 25.0, "M", 150.0), (54, 27.5, "F", None))


def test_keep_and_drop_columns_update_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(KeepCommand(variables=("age", "sex")))
    result = executor.execute(DropCommand(variables=("sex",)))
    preview = executor.execute(HeadCommand(1))
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert result.dataset.column_count == 1
  assert [column.name for column in result.dataset.columns] == ["age"]
  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("age",)
  assert preview.rows == ((30,),)


def test_select_and_row_filters_update_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(
      KeepCommand(
        condition=BinaryExpression(
          left=IdentifierExpression("age"),
          operator=">=",
          right=NumberExpression(42),
        )
      )
    )
    executor.execute(
      DropCommand(
        condition=BinaryExpression(
          left=IdentifierExpression("sex"),
          operator="==",
          right=StringExpression("M"),
        )
      )
    )
    result = executor.execute(SelectCommand(("age", "cost")))
    preview = executor.execute(HeadCommand(5))
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert result.dataset.row_count == 1
  assert result.dataset.column_count == 2
  assert isinstance(preview, PreviewResult)
  assert preview.rows == ((54, None),)


def test_rename_generate_and_replace_update_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(RenameCommand("sex", "gender"))
    executor.execute(
      GenerateCommand(
        "age_plus_one",
        BinaryExpression(
          left=IdentifierExpression("age"),
          operator="+",
          right=NumberExpression(1),
        ),
      )
    )
    executor.execute(
      ReplaceCommand(
        "cost",
        NumberExpression(0),
        BinaryExpression(
          left=IdentifierExpression("gender"),
          operator="==",
          right=StringExpression("F"),
        ),
      )
    )
    preview = executor.execute(HeadCommand(3))
  finally:
    executor.close()

  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("age", "bmi", "gender", "cost", "age_plus_one")
  assert preview.rows == (
    (30, 22.5, "F", 0.0, 31),
    (42, 25.0, "M", 150.0, 43),
    (54, 27.5, "F", 0.0, 55),
  )


def test_tabulate_one_way_and_two_way(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    one_way = executor.execute(TabulateCommand(("sex",)))
    two_way = executor.execute(
      TabulateCommand(("sex", "age"), row_percent=True, column_percent=True)
    )
  finally:
    executor.close()

  assert isinstance(one_way, TableResult)
  assert one_way.headers == ("sex", "Count", "Percent")
  assert one_way.rows == (("F", 2, pytest.approx(66.666666)), ("M", 1, pytest.approx(33.333333)))
  assert isinstance(two_way, TableResult)
  assert two_way.headers == ("sex", "age", "Count", "Row %", "Col %")
  assert two_way.rows[0] == ("F", 30, 1, pytest.approx(50.0), pytest.approx(100.0))


def test_by_summarize_and_count_do_not_change_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    summarized = executor.execute(ByCommand(("sex",), SummarizeCommand(("age",))))
    counted = executor.execute(ByCommand(("sex",), CountCommand()))
    preview = executor.execute(HeadCommand(1))
  finally:
    executor.close()

  assert isinstance(summarized, TableResult)
  assert summarized.headers == ("sex", "mean_age")
  assert summarized.rows == (("F", 42.0), ("M", 42.0))
  assert isinstance(counted, TableResult)
  assert counted.headers == ("sex", "Count")
  assert counted.rows == (("F", 2), ("M", 1))
  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("age", "bmi", "sex", "cost")


def test_by_summarize_without_varlist_uses_numeric_non_group_columns(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    summarized = executor.execute(ByCommand(("sex",), SummarizeCommand(())))
  finally:
    executor.close()

  assert isinstance(summarized, TableResult)
  assert summarized.headers == ("sex", "mean_age", "mean_bmi", "mean_cost")
  assert summarized.rows == (
    ("F", 42.0, 25.0, 100.0),
    ("M", 42.0, 25.0, 150.0),
  )


def test_collapse_replaces_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(CollapseCommand("mean", ("age", "cost"), ("sex",)))
    preview = executor.execute(HeadCommand(5))
  finally:
    executor.close()

  assert isinstance(result, TransformResult)
  assert result.dataset.column_count == 3
  assert [column.name for column in result.dataset.columns] == ["sex", "mean_age", "mean_cost"]
  assert isinstance(preview, PreviewResult)
  assert preview.rows == (("F", 42.0, 100.0), ("M", 42.0, 150.0))


def test_sql_queries_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(
      SqlCommand("select sex, avg(bmi) as mean_bmi from active group by sex order by sex")
    )
  finally:
    executor.close()

  assert isinstance(result, TableResult)
  assert result.headers == ("sex", "mean_bmi")
  assert result.rows == (("F", 25.0), ("M", 25.0))


def test_sql_into_replaces_active_dataset(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    result = executor.execute(
      SqlCommand(
        "select sex, count(*) as n from active group by sex order by sex",
        into="summary",
      )
    )
    described = executor.execute(DescribeCommand())
    preview = executor.execute(HeadCommand(5))
  finally:
    executor.close()

  assert isinstance(result, SqlCreateResult)
  assert result.table_name == "summary"
  assert result.dataset.row_count == 2
  assert [column.name for column in result.dataset.columns] == ["sex", "n"]
  assert isinstance(described, DescribeResult)
  assert [column.name for column in described.dataset.columns] == ["sex", "n"]
  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("sex", "n")
  assert preview.rows == (("F", 2), ("M", 1))


def test_sql_into_registers_named_table_for_later_activation(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(
      SqlCommand(
        "select sex, count(*) as n from active group by sex order by sex",
        into="summary",
      )
    )
    executor.execute(KeepCommand(variables=("sex",)))
    transformed_summary = executor.execute(DescribeCommand())
    activated = executor.execute(UseCommand(Path("summary")))
    preview = executor.execute(HeadCommand(5))
  finally:
    executor.close()

  assert isinstance(transformed_summary, DescribeResult)
  assert [column.name for column in transformed_summary.dataset.columns] == ["sex"]
  assert isinstance(activated, ActivateResult)
  assert activated.table_name == "summary"
  assert [column.name for column in activated.dataset.columns] == ["sex"]
  assert isinstance(preview, PreviewResult)
  assert preview.columns == ("sex",)
  assert preview.rows == (("F",), ("M",))


def test_use_unknown_named_table_reports_specific_error() -> None:
  executor = Executor()
  try:
    with pytest.raises(UnknownTableError, match="unknown table: missing_table"):
      executor.execute(UseCommand(Path("missing_table")))
  finally:
    executor.close()


def test_use_named_table_rejects_options(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(
      SqlCommand("select sex, count(*) as n from active group by sex order by sex", into="summary")
    )
    with pytest.raises(
      ExecutionError,
      match="use options are not supported for named table activation",
    ):
      executor.execute(UseCommand(Path("summary"), execution_mode="lazy", lazy_engine="duckdb"))
  finally:
    executor.close()


def test_sql_reports_user_facing_errors(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match="sql requires an active dataset"):
      executor.execute(SqlCommand("select * from active"))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="sql only supports select or with queries"):
      executor.execute(SqlCommand("drop table active"))
    with pytest.raises(ExecutionError, match="sql failed"):
      executor.execute(SqlCommand("select missing from active"))
  finally:
    executor.close()


def test_phase_6_visualizations_write_svg_artifacts(
  sample_parquet: Path,
  tmp_path: Path,
) -> None:
  histogram_path = tmp_path / "plots" / "age.svg"
  scatter_path = tmp_path / "plots" / "bmi-age.svg"
  bar_path = tmp_path / "plots" / "sex.svg"
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    histogram = executor.execute(HistogramCommand("age", bins=5, saving=histogram_path))
    scatter = executor.execute(ScatterCommand("bmi", "age", saving=scatter_path))
    bar = executor.execute(BarCommand("sex", saving=bar_path))
  finally:
    executor.close()

  assert isinstance(histogram, PlotResult)
  assert histogram.path == histogram_path
  assert histogram.should_open
  assert histogram_path.read_text().lstrip().startswith("<svg")
  assert isinstance(scatter, PlotResult)
  assert scatter.path == scatter_path
  assert scatter_path.read_text().lstrip().startswith("<svg")
  assert isinstance(bar, PlotResult)
  assert bar.path == bar_path
  assert bar_path.read_text().lstrip().startswith("<svg")


def test_phase_9_set_updates_plot_defaults(sample_parquet: Path, tmp_path: Path) -> None:
  executor = Executor(config=TabDatConfig(artifact_dir=tmp_path / "artifacts"))
  try:
    result = executor.execute(SetCommand("graph_format", "png"))
    executor.execute(UseCommand(sample_parquet))
    plot = executor.execute(HistogramCommand("age"))
  finally:
    executor.close()

  assert isinstance(result, SetResult)
  assert result.value == "png"
  assert isinstance(plot, PlotResult)
  assert plot.path == tmp_path / "artifacts" / "plots" / "histogram-age.png"
  assert plot.path.exists()


def test_phase_9_save_writes_transformed_active_dataset(
  sample_parquet: Path,
  tmp_path: Path,
) -> None:
  output_path = tmp_path / "filtered.parquet"
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    executor.execute(
      KeepCommand(
        condition=BinaryExpression(
          left=IdentifierExpression("age"),
          operator=">=",
          right=NumberExpression(42),
        )
      )
    )
    result = executor.execute(SaveCommand(output_path))
    with pytest.raises(ExecutionError, match="save target already exists"):
      executor.execute(SaveCommand(output_path))
    replaced = executor.execute(SaveCommand(output_path, replace=True))
  finally:
    executor.close()

  assert isinstance(result, SaveResult)
  assert result.dataset.row_count == 2
  assert output_path.exists()
  assert isinstance(replaced, SaveResult)


def test_phase_6_visualizations_report_user_facing_errors(
  sample_parquet: Path,
  tmp_path: Path,
) -> None:
  executor = Executor()
  try:
    with pytest.raises(ExecutionError, match="histogram requires an active dataset"):
      executor.execute(HistogramCommand("age"))
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="plot requires numeric variables: sex"):
      executor.execute(HistogramCommand("sex", saving=tmp_path / "sex.svg"))
    with pytest.raises(ExecutionError, match="plot requires numeric variables: sex"):
      executor.execute(ScatterCommand("age", "sex", saving=tmp_path / "scatter.svg"))
    with pytest.raises(ExecutionError, match="bar unknown variable: missing"):
      executor.execute(BarCommand("missing", saving=tmp_path / "missing.svg"))
    with pytest.raises(ExecutionError, match="plot saving path must end with"):
      executor.execute(HistogramCommand("age", saving=tmp_path / "age.txt"))
  finally:
    executor.close()


def test_phase_3_transformations_report_user_facing_errors(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(ExecutionError, match="generate target already exists: age"):
      executor.execute(GenerateCommand("age", NumberExpression(1)))
    with pytest.raises(ExecutionError, match="replace unknown variable: missing"):
      executor.execute(ReplaceCommand("missing", NumberExpression(1)))
    with pytest.raises(ExecutionError, match="drop would remove every column"):
      executor.execute(DropCommand(("age", "bmi", "sex", "cost")))
    with pytest.raises(ExecutionError, match="unsupported function"):
      executor.execute(GenerateCommand("bad", FunctionCallExpression("not_a_function", ())))
  finally:
    executor.close()


@pytest.mark.parametrize(
  ("command", "message"),
  [
    (CodebookCommand(()), "codebook requires an active dataset"),
    (CountCommand(), "count requires an active dataset"),
    (HeadCommand(), "head requires an active dataset"),
    (TailCommand(), "tail requires an active dataset"),
    (KeepCommand(variables=("age",)), "keep requires an active dataset"),
    (TabulateCommand(("sex",)), "tabulate requires an active dataset"),
  ],
)
def test_phase_3_inspection_commands_require_active_dataset(command, message: str) -> None:
  executor = Executor()
  try:
    with pytest.raises(NoActiveDatasetError, match=message):
      executor.execute(command)
  finally:
    executor.close()


def test_unknown_variable_and_type_errors_are_specific(sample_parquet: Path) -> None:
  executor = Executor()
  try:
    executor.execute(UseCommand(sample_parquet))
    with pytest.raises(UnknownVariableError, match="summarize unknown variable"):
      executor.execute(SummarizeCommand(("missing",)))
    with pytest.raises(TypeMismatchExecutionError, match="summarize requires numeric variables"):
      executor.execute(SummarizeCommand(("sex",)))
  finally:
    executor.close()


def test_executor_rejects_unsupported_by_child_command() -> None:
  executor = Executor()
  try:
    with pytest.raises(ExecutionError, match="unsupported command"):
      executor.execute(ParsedCommand(name="keep"))
  finally:
    executor.close()


def test_use_rejects_non_parquet(tmp_path: Path) -> None:
  csv_path = tmp_path / "patients.csv"
  csv_path.write_text("age\n42\n")
  executor = Executor()
  try:
    with pytest.raises(ExecutionError, match=r"\.parquet"):
      executor.execute(UseCommand(csv_path))
  finally:
    executor.close()
