from pathlib import Path

import pytest

from tabdat.errors import ParseError
from tabdat.models import (
  AppendCommand,
  BarCommand,
  BayesCommand,
  BayesPrefixCommand,
  BinaryExpression,
  ByCommand,
  CfRegressCommand,
  CodebookCommand,
  CollapseCommand,
  CommandOption,
  CountCommand,
  CvelasticnetCommand,
  CvlassoCommand,
  CvridgeCommand,
  DescribeCommand,
  DidCommand,
  DmlCommand,
  DrDidCommand,
  DropCommand,
  ElasticnetCommand,
  EstatCommand,
  ExitCommand,
  ExportCommand,
  FunctionCallExpression,
  GenerateCommand,
  HeadCommand,
  HeckmanCommand,
  HelpCommand,
  HistogramCommand,
  IdentifierExpression,
  IvRegressCommand,
  JoinCommand,
  KeepCommand,
  LassoCommand,
  LogitCommand,
  LowessCommand,
  NbregCommand,
  NlCommand,
  NumberExpression,
  PanelCommand,
  ParsedCommand,
  PoissonCommand,
  PostlassoCommand,
  PredictCommand,
  ProbitCommand,
  QregCommand,
  RegressCommand,
  RenameCommand,
  ReplaceCommand,
  ReshapeCommand,
  RidgeCommand,
  RunCommand,
  SaveCommand,
  ScatterCommand,
  SelectCommand,
  SetCommand,
  SqlCommand,
  StregCommand,
  StringExpression,
  SummarizeCommand,
  TabulateCommand,
  TailCommand,
  TobitCommand,
  UseCommand,
  XtAbondCommand,
  XtDataCommand,
  XtLogitCommand,
  XtRegCommand,
  ZinbCommand,
  ZipCommand,
)
from tabdat.parser import parse_command, parse_expression


def test_parse_use_command() -> None:
  assert parse_command("use data.parquet") == UseCommand(Path("data.parquet"))
  assert parse_command("use data.parquet, lazy") == UseCommand(
    Path("data.parquet"),
    execution_mode="lazy",
    lazy_engine="duckdb",
  )
  assert parse_command("use data.parquet, lazy engine=duckdb") == UseCommand(
    Path("data.parquet"),
    execution_mode="lazy",
    lazy_engine="duckdb",
  )
  assert parse_command("use data.parquet, lazy engine=polars") == UseCommand(
    Path("data.parquet"),
    execution_mode="lazy",
    lazy_engine="polars",
  )
  assert parse_command("use https://example.com/data.parquet") == UseCommand(
    "https://example.com/data.parquet"
  )
  assert parse_command("use s3://bucket/data.parquet, lazy") == UseCommand(
    "s3://bucket/data.parquet",
    execution_mode="lazy",
    lazy_engine="duckdb",
  )


def test_parse_help_command() -> None:
  assert parse_command("help summarize") == HelpCommand("summarize")
  assert parse_command("? summarize") == HelpCommand("summarize")
  assert parse_command("help") == HelpCommand()
  assert parse_command("?") == HelpCommand()


def test_parse_phase_11_join_command() -> None:
  assert parse_command("join lookup on id") == JoinCommand(
    table_name="lookup",
    keys=("id",),
  )
  assert parse_command("join lookup on firm_id year, how=left suffix(_lookup)") == JoinCommand(
    table_name="lookup",
    keys=("firm_id", "year"),
    how="left",
    suffix="_lookup",
  )


def test_parse_phase_11_append_command() -> None:
  assert parse_command("append followup") == AppendCommand(table_name="followup")


def test_parse_phase_11_reshape_commands() -> None:
  assert parse_command("reshape long income cost, i(id) j(year)") == ReshapeCommand(
    direction="long",
    variables=("income", "cost"),
    identifiers=("id",),
    j_variable="year",
  )
  assert parse_command("reshape wide income cost, i(firm_id person_id) j(year)") == (
    ReshapeCommand(
      direction="wide",
      variables=("income", "cost"),
      identifiers=("firm_id", "person_id"),
      j_variable="year",
    )
  )


def test_parse_phase_11_panel_commands() -> None:
  assert parse_command("panel") == PanelCommand(action="report")
  assert parse_command("panel firm_id year") == PanelCommand(
    action="set",
    id_variable="firm_id",
    time_variable="year",
  )
  assert parse_command("panel clear") == PanelCommand(action="clear")


def test_parse_by_rejects_help_child_command() -> None:
  with pytest.raises(ParseError, match="help is not supported inside by commands"):
    parse_command("by sex: help summarize")


def test_parse_describe_command() -> None:
  assert parse_command("describe") == DescribeCommand()


def test_parse_summarize_command_with_variables() -> None:
  assert parse_command("summarize age bmi") == SummarizeCommand(("age", "bmi"))


def test_parse_summarize_preserves_punctuated_variable_names() -> None:
  assert parse_command("summarize bmi-zscore cost.2024 x/y") == SummarizeCommand(
    ("bmi-zscore", "cost.2024", "x/y")
  )


def test_parse_summarize_command_without_variables() -> None:
  assert parse_command("summarize") == SummarizeCommand(())


def test_parse_phase_3_inspection_commands() -> None:
  assert parse_command("codebook") == CodebookCommand(())
  assert parse_command("codebook age sex") == CodebookCommand(("age", "sex"))
  assert parse_command("count") == CountCommand()
  assert parse_command("head") == HeadCommand(5)
  assert parse_command("head 10") == HeadCommand(10)
  assert parse_command("head 01") == HeadCommand(1)
  assert parse_command("head 0") == HeadCommand(0)
  assert parse_command("tail") == TailCommand(5)
  assert parse_command("tail 2") == TailCommand(2)
  assert parse_command("tail 000") == TailCommand(0)


def test_parse_summarize_with_if_as_structured_phase_2_command() -> None:
  assert parse_command("summarize age bmi-zscore if age >= 18") == ParsedCommand(
    name="summarize",
    arguments=("age", "bmi-zscore"),
    condition=BinaryExpression(
      left=IdentifierExpression("age"),
      operator=">=",
      right=NumberExpression(18),
    ),
  )


def test_parse_summarize_with_options_as_structured_phase_2_command() -> None:
  assert parse_command("summarize age bmi, detail limit=10") == ParsedCommand(
    name="summarize",
    arguments=("age", "bmi"),
    options=(
      CommandOption("detail", True),
      CommandOption("limit", 10),
    ),
  )


def test_parse_condition_and_options() -> None:
  assert parse_command('summarize age if sex == "F", detail') == ParsedCommand(
    name="summarize",
    arguments=("age",),
    condition=BinaryExpression(
      left=IdentifierExpression("sex"),
      operator="==",
      right=StringExpression("F"),
    ),
    options=(CommandOption("detail", True),),
  )


def test_parse_phase_3_transformation_commands() -> None:
  assert parse_command("keep age bmi") == KeepCommand(variables=("age", "bmi"))
  assert parse_command("keep if age >= 18") == KeepCommand(
    condition=BinaryExpression(
      left=IdentifierExpression("age"),
      operator=">=",
      right=NumberExpression(18),
    ),
  )
  assert parse_command("drop cost") == DropCommand(variables=("cost",))
  assert parse_command("drop if sex == 'F'") == DropCommand(
    condition=BinaryExpression(
      left=IdentifierExpression("sex"),
      operator="==",
      right=StringExpression("F"),
    ),
  )
  assert parse_command("select age sex") == SelectCommand(("age", "sex"))
  assert parse_command("rename sex gender") == RenameCommand("sex", "gender")


def test_parse_phase_3_generate_and_replace_commands() -> None:
  assert parse_command("generate log_cost = log(cost)") == GenerateCommand(
    variable="log_cost",
    expression=FunctionCallExpression(
      name="log",
      arguments=(IdentifierExpression("cost"),),
    ),
  )
  assert parse_command("replace cost = cost * 2 if sex == 'F'") == ReplaceCommand(
    variable="cost",
    expression=BinaryExpression(
      left=IdentifierExpression("cost"),
      operator="*",
      right=NumberExpression(2),
    ),
    condition=BinaryExpression(
      left=IdentifierExpression("sex"),
      operator="==",
      right=StringExpression("F"),
    ),
  )


def test_parse_phase_3_grouping_commands() -> None:
  assert parse_command("tabulate sex") == TabulateCommand(("sex",))
  assert parse_command("tabulate sex age, row col missing") == TabulateCommand(
    variables=("sex", "age"),
    row_percent=True,
    column_percent=True,
    include_missing=True,
  )
  assert parse_command("collapse mean age cost, by(sex)") == CollapseCommand(
    statistic="mean",
    variables=("age", "cost"),
    groups=("sex",),
  )
  assert parse_command("by sex: summarize age cost") == ByCommand(
    groups=("sex",),
    command=SummarizeCommand(("age", "cost")),
  )
  assert parse_command("by sex age: count") == ByCommand(
    groups=("sex", "age"),
    command=CountCommand(),
  )


def test_parse_phase_4_sql_commands() -> None:
  assert parse_command("use summary") == UseCommand(Path("summary"))
  assert parse_command(
    "sql select sex, avg(bmi) as mean_bmi from active group by sex"
  ) == SqlCommand(query="select sex, avg(bmi) as mean_bmi from active group by sex")
  assert parse_command(
    "sql select sex, avg(bmi) from active group by sex into summary"
  ) == SqlCommand(
    query="select sex, avg(bmi) from active group by sex",
    into="summary",
  )
  assert parse_command("sql select * from active   into summary") == SqlCommand(
    query="select * from active",
    into="summary",
  )
  assert parse_command('sql """\nselect sex, count(*) as n\nfrom active\n"""') == SqlCommand(
    query="select sex, count(*) as n\nfrom active"
  )
  assert parse_command(
    'sql """\nselect sex, count(*) as n\nfrom active\n""" into grouped'
  ) == SqlCommand(
    query="select sex, count(*) as n\nfrom active",
    into="grouped",
  )


def test_parse_phase_8_run_command() -> None:
  assert parse_command("run analysis.td") == RunCommand(Path("analysis.td"))


def test_parse_phase_9_configuration_and_persistence_commands() -> None:
  assert parse_command("set graph_format png") == SetCommand("graph_format", "png")
  assert parse_command("set artifact_dir artifacts/custom") == SetCommand(
    "artifact_dir",
    "artifacts/custom",
  )
  assert parse_command('set artifact_dir "my plots"') == SetCommand(
    "artifact_dir",
    "my plots",
  )
  assert parse_command("set graph_open off") == SetCommand("graph_open", "off")
  assert parse_command("save output.parquet") == SaveCommand(Path("output.parquet"))
  assert parse_command("export output.parquet, replace") == ExportCommand(
    Path("output.parquet"),
    replace=True,
  )
  assert parse_command("export output.csv") == ExportCommand(Path("output.csv"))
  assert parse_command("export output.feather") == ExportCommand(Path("output.feather"))


def test_parse_phase_13_regress_command() -> None:
  assert parse_command("regress cost age bmi") == RegressCommand(
    outcome="cost",
    predictors=("age", "bmi"),
  )
  assert parse_command("regress cost age, wls(weight)") == RegressCommand(
    outcome="cost",
    predictors=("age",),
    estimator="wls",
    weight_variable="weight",
  )
  assert parse_command("regress cost age, gls(sigma)") == RegressCommand(
    outcome="cost",
    predictors=("age",),
    estimator="gls",
    weight_variable="sigma",
  )
  assert parse_command("regress cost age, robust") == RegressCommand(
    outcome="cost",
    predictors=("age",),
    robust=True,
  )
  assert parse_command("regress cost age, cluster(sex)") == RegressCommand(
    outcome="cost",
    predictors=("age",),
    cluster_variable="sex",
  )
  assert parse_command("regress cost age, noconstant") == RegressCommand(
    outcome="cost",
    predictors=("age",),
    include_intercept=False,
  )
  assert parse_command("regress cost age, wls(weight) cluster(firm)") == RegressCommand(
    outcome="cost",
    predictors=("age",),
    estimator="wls",
    weight_variable="weight",
    cluster_variable="firm",
  )
  assert parse_command("regress cost age, gls(sigma) robust") == RegressCommand(
    outcome="cost",
    predictors=("age",),
    estimator="gls",
    weight_variable="sigma",
    robust=True,
  )


def test_parse_phase_17_qreg_command() -> None:
  assert parse_command("qreg cost age bmi") == QregCommand(
    outcome="cost",
    predictors=("age", "bmi"),
  )
  assert parse_command("qreg cost age, quantile(0.25)") == QregCommand(
    outcome="cost",
    predictors=("age",),
    quantile=0.25,
  )
  assert parse_command("qreg cost age, robust") == QregCommand(
    outcome="cost",
    predictors=("age",),
    robust=True,
  )
  assert parse_command("qreg cost age, noconstant") == QregCommand(
    outcome="cost",
    predictors=("age",),
    include_intercept=False,
  )


def test_parse_phase_19_lasso_command() -> None:
  assert parse_command("lasso linear cost age bmi") == LassoCommand(
    outcome="cost",
    predictors=("age", "bmi"),
  )
  assert parse_command("lasso linear cost age, alpha(0.25)") == LassoCommand(
    outcome="cost",
    predictors=("age",),
    alpha=0.25,
  )
  assert parse_command("lasso linear cost age, noconstant") == LassoCommand(
    outcome="cost",
    predictors=("age",),
    include_intercept=False,
  )


def test_parse_phase_19_dml_command() -> None:
  assert parse_command("dml linear y x1 x2, treat(d)") == DmlCommand(
    outcome="y",
    controls=("x1", "x2"),
    treatment_variable="d",
  )
  assert parse_command("dml linear y x1, treat(d) folds(3)") == DmlCommand(
    outcome="y",
    controls=("x1",),
    treatment_variable="d",
    folds=3,
  )
  assert parse_command("dml linear y x1 x2, treat(d) alpha(0.5)") == DmlCommand(
    outcome="y",
    controls=("x1", "x2"),
    treatment_variable="d",
    alpha=0.5,
  )
  assert parse_command("dml linear y x1, treat(d) robust") == DmlCommand(
    outcome="y",
    controls=("x1",),
    treatment_variable="d",
    robust=True,
  )
  assert parse_command("dml linear y x1, treat(d) seed(42)") == DmlCommand(
    outcome="y",
    controls=("x1",),
    treatment_variable="d",
    seed=42,
  )
  assert parse_command("dml linear y x1, treat(d) noconstant") == DmlCommand(
    outcome="y",
    controls=("x1",),
    treatment_variable="d",
    include_intercept=False,
  )
  assert parse_command("estat dml") == EstatCommand(subcommand="dml")


def test_parse_phase_19_postlasso_command() -> None:
  assert parse_command("postlasso linear cost age bmi") == PostlassoCommand(
    outcome="cost",
    predictors=("age", "bmi"),
  )
  assert parse_command("postlasso linear cost age, alpha(0.25)") == PostlassoCommand(
    outcome="cost",
    predictors=("age",),
    alpha=0.25,
  )
  assert parse_command("postlasso linear cost age, robust") == PostlassoCommand(
    outcome="cost",
    predictors=("age",),
    robust=True,
  )
  assert parse_command("postlasso linear cost age, noconstant") == PostlassoCommand(
    outcome="cost",
    predictors=("age",),
    include_intercept=False,
  )


def test_parse_phase_19_cvlasso_command() -> None:
  assert parse_command("cvlasso linear cost age bmi") == CvlassoCommand(
    outcome="cost",
    predictors=("age", "bmi"),
    cv=5,
  )
  assert parse_command("cvlasso linear cost age, cv(3)") == CvlassoCommand(
    outcome="cost",
    predictors=("age",),
    cv=3,
  )
  assert parse_command("cvlasso linear cost age, noconstant") == CvlassoCommand(
    outcome="cost",
    predictors=("age",),
    cv=5,
    include_intercept=False,
  )


def test_parse_phase_19_cvridge_command() -> None:
  assert parse_command("cvridge linear cost age bmi") == CvridgeCommand(
    outcome="cost",
    predictors=("age", "bmi"),
    cv=5,
  )
  assert parse_command("cvridge linear cost age, cv(10)") == CvridgeCommand(
    outcome="cost",
    predictors=("age",),
    cv=10,
  )


def test_parse_phase_19_cvelasticnet_command() -> None:
  assert parse_command("cvelasticnet linear cost age bmi") == CvelasticnetCommand(
    outcome="cost",
    predictors=("age", "bmi"),
    cv=5,
  )
  assert parse_command("cvelasticnet linear cost age, l1_ratio(0.3)") == CvelasticnetCommand(
    outcome="cost",
    predictors=("age",),
    cv=5,
    l1_ratio=0.3,
  )
  assert parse_command(
    "cvelasticnet linear cost age, l1_ratio(0.1 0.5 0.9)"
  ) == CvelasticnetCommand(
    outcome="cost",
    predictors=("age",),
    cv=5,
    l1_ratio=(0.1, 0.5, 0.9),
  )

  from tabdat.parser import ParseError

  with pytest.raises(ParseError, match="option l1_ratio expects at least one value"):
    parse_command("cvelasticnet linear cost age, l1_ratio()")


def test_parse_phase_19_ridge_command() -> None:
  assert parse_command("ridge linear cost age bmi") == RidgeCommand(
    outcome="cost",
    predictors=("age", "bmi"),
  )
  assert parse_command("ridge linear cost age, alpha(0.25)") == RidgeCommand(
    outcome="cost",
    predictors=("age",),
    alpha=0.25,
  )
  assert parse_command("ridge linear cost age, noconstant") == RidgeCommand(
    outcome="cost",
    predictors=("age",),
    include_intercept=False,
  )


def test_parse_phase_19_elasticnet_command() -> None:
  assert parse_command("elasticnet linear cost age bmi") == ElasticnetCommand(
    outcome="cost",
    predictors=("age", "bmi"),
  )
  assert parse_command(
    "elasticnet linear cost age, alpha(0.25) l1_ratio(0.75)"
  ) == ElasticnetCommand(
    outcome="cost",
    predictors=("age",),
    alpha=0.25,
    l1_ratio=0.75,
  )
  assert parse_command("elasticnet linear cost age, noconstant") == ElasticnetCommand(
    outcome="cost",
    predictors=("age",),
    include_intercept=False,
  )


def test_parse_phase_19_bayes_command() -> None:
  assert parse_command("bayes linear cost age bmi") == BayesCommand(
    outcome="cost",
    predictors=("age", "bmi"),
  )
  assert parse_command("bayes linear cost age, n_iter(500)") == BayesCommand(
    outcome="cost",
    predictors=("age",),
    n_iter=500,
  )
  assert parse_command("bayes linear cost age, tol(1e-4)") == BayesCommand(
    outcome="cost",
    predictors=("age",),
    tol=0.0001,
  )
  assert parse_command("bayes linear cost age, n_iter(100) tol(1e-5) noconstant") == BayesCommand(
    outcome="cost",
    predictors=("age",),
    n_iter=100,
    tol=1e-5,
    include_intercept=False,
  )


def test_parse_phase_19_bayes_prefix_command() -> None:
  # Basic prefix without options
  assert parse_command("bayes: regress y x") == BayesPrefixCommand(
    command=RegressCommand(outcome="y", predictors=("x",)),
  )
  # Prefix with options
  cmd1 = "bayes, draws(500) burnin(200) chains(2) thin(2) seed(123): regress y x"
  assert parse_command(cmd1) == BayesPrefixCommand(
    command=RegressCommand(outcome="y", predictors=("x",)),
    draws=500,
    burnin=200,
    chains=2,
    thin=2,
    seed=123,
  )
  # rseed alias maps to the same seed field
  cmd_rseed = "bayes, rseed(42): regress y x"
  assert parse_command(cmd_rseed) == BayesPrefixCommand(
    command=RegressCommand(outcome="y", predictors=("x",)),
    seed=42,
  )
  # tune alias maps to burnin
  cmd_tune = "bayes, tune(100): regress y x"
  assert parse_command(cmd_tune) == BayesPrefixCommand(
    command=RegressCommand(outcome="y", predictors=("x",)),
    burnin=100,
  )
  # Prefix with custom prior options
  cmd2 = "bayes, prior(x, normal(0, 10)) prior(intercept, uniform(-5, 5)): logit y x"
  assert parse_command(cmd2) == BayesPrefixCommand(
    command=LogitCommand(outcome="y", predictors=("x",)),
    priors=(("x", "normal(0,10)"), ("intercept", "uniform(-5,5)")),
  )
  # noconstant in inner regress command
  cmd_noconst = "bayes: regress y x, noconstant"
  result = parse_command(cmd_noconst)
  assert isinstance(result, BayesPrefixCommand)
  assert isinstance(result.command, RegressCommand)
  assert result.command.include_intercept is False
  # Invalid prefix inner command
  with pytest.raises(ParseError, match="bayes prefix only supports regress and logit commands"):
    parse_command("bayes: codebook")


def test_parse_phase_13_predict_command() -> None:
  assert parse_command("predict cost_hat") == PredictCommand(
    target_variable="cost_hat",
    kind="xb",
  )
  assert parse_command("predict resid, residuals") == PredictCommand(
    target_variable="resid",
    kind="residuals",
  )
  assert parse_command("predict p_hat, pr") == PredictCommand(
    target_variable="p_hat",
    kind="pr",
  )
  assert parse_command("predict spatial_hat, spatial_lag") == PredictCommand(
    target_variable="spatial_hat",
    kind="spatial_lag",
  )
  assert parse_command("predict y_pp, posterior_predictive") == PredictCommand(
    target_variable="y_pp",
    kind="posterior_predictive",
  )


def test_parse_phase_15_logit_command() -> None:
  assert parse_command("logit outcome x1 x2") == LogitCommand(
    outcome="outcome",
    predictors=("x1", "x2"),
  )
  assert parse_command("logit outcome x1, robust") == LogitCommand(
    outcome="outcome",
    predictors=("x1",),
    robust=True,
  )
  assert parse_command("logit outcome x1, cluster(group_id)") == LogitCommand(
    outcome="outcome",
    predictors=("x1",),
    cluster_variable="group_id",
  )
  assert parse_command("logit outcome x1, noconstant") == LogitCommand(
    outcome="outcome",
    predictors=("x1",),
    include_intercept=False,
  )


def test_parse_phase_15_probit_command() -> None:
  assert parse_command("probit outcome x1 x2") == ProbitCommand(
    outcome="outcome",
    predictors=("x1", "x2"),
  )
  assert parse_command("probit outcome x1, robust") == ProbitCommand(
    outcome="outcome",
    predictors=("x1",),
    robust=True,
  )
  assert parse_command("probit outcome x1, cluster(group_id)") == ProbitCommand(
    outcome="outcome",
    predictors=("x1",),
    cluster_variable="group_id",
  )
  assert parse_command("probit outcome x1, noconstant") == ProbitCommand(
    outcome="outcome",
    predictors=("x1",),
    include_intercept=False,
  )


def test_parse_phase_15_tobit_command() -> None:
  assert parse_command("tobit outcome x1, ll(0)") == TobitCommand(
    outcome="outcome",
    predictors=("x1",),
    lower_limit=0.0,
  )
  assert parse_command("tobit outcome x1 x2, ll(-1) ul(10) robust") == TobitCommand(
    outcome="outcome",
    predictors=("x1", "x2"),
    lower_limit=-1.0,
    upper_limit=10.0,
    robust=True,
  )
  assert parse_command("tobit outcome x1, ll(0) cluster(group_id) noconstant") == TobitCommand(
    outcome="outcome",
    predictors=("x1",),
    lower_limit=0.0,
    cluster_variable="group_id",
    include_intercept=False,
  )


def test_parse_phase_15_heckman_command() -> None:
  assert parse_command("heckman outcome x1, selectdep(s) select(z1)") == HeckmanCommand(
    outcome="outcome",
    predictors=("x1",),
    selection_dependent="s",
    selection_predictors=("z1",),
  )
  assert parse_command("heckman outcome x1 x2, selectdep(s) select(z1 z2) robust") == (
    HeckmanCommand(
      outcome="outcome",
      predictors=("x1", "x2"),
      selection_dependent="s",
      selection_predictors=("z1", "z2"),
      robust=True,
    )
  )
  assert parse_command(
    "heckman outcome x1, selectdep(s) select(z1) cluster(group_id) noconstant"
  ) == HeckmanCommand(
    outcome="outcome",
    predictors=("x1",),
    selection_dependent="s",
    selection_predictors=("z1",),
    cluster_variable="group_id",
    include_intercept=False,
  )


def test_parse_phase_15_nl_command() -> None:
  assert parse_command("nl y = a + b * x, params(a b) start(1 0.5)") == NlCommand(
    outcome="y",
    expression=BinaryExpression(
      left=IdentifierExpression("a"),
      operator="+",
      right=BinaryExpression(
        left=IdentifierExpression("b"),
        operator="*",
        right=IdentifierExpression("x"),
      ),
    ),
    parameter_names=("a", "b"),
    start_values=(1.0, 0.5),
  )
  assert parse_command("nl y = exp(a + b * x), params(a b) start(0 1) robust noconstant") == (
    NlCommand(
      outcome="y",
      expression=FunctionCallExpression(
        name="exp",
        arguments=(
          BinaryExpression(
            left=IdentifierExpression("a"),
            operator="+",
            right=BinaryExpression(
              left=IdentifierExpression("b"),
              operator="*",
              right=IdentifierExpression("x"),
            ),
          ),
        ),
      ),
      parameter_names=("a", "b"),
      start_values=(0.0, 1.0),
      robust=True,
      include_intercept=False,
    )
  )


def test_parse_phase_16_poisson_command() -> None:
  assert parse_command("poisson outcome x1 x2") == PoissonCommand(
    outcome="outcome",
    predictors=("x1", "x2"),
  )
  assert parse_command("poisson outcome x1, robust") == PoissonCommand(
    outcome="outcome",
    predictors=("x1",),
    robust=True,
  )
  assert parse_command("poisson outcome x1, cluster(group_id)") == PoissonCommand(
    outcome="outcome",
    predictors=("x1",),
    cluster_variable="group_id",
  )
  assert parse_command("poisson outcome x1, noconstant") == PoissonCommand(
    outcome="outcome",
    predictors=("x1",),
    include_intercept=False,
  )


def test_parse_phase_16_nbreg_command() -> None:
  assert parse_command("nbreg outcome x1 x2") == NbregCommand(
    outcome="outcome",
    predictors=("x1", "x2"),
  )
  assert parse_command("nbreg outcome x1, robust") == NbregCommand(
    outcome="outcome",
    predictors=("x1",),
    robust=True,
  )
  assert parse_command("nbreg outcome x1, cluster(group_id)") == NbregCommand(
    outcome="outcome",
    predictors=("x1",),
    cluster_variable="group_id",
  )
  assert parse_command("nbreg outcome x1, noconstant") == NbregCommand(
    outcome="outcome",
    predictors=("x1",),
    include_intercept=False,
  )


def test_parse_phase_16_zip_command() -> None:
  assert parse_command("zip outcome x1 x2, inflate(z1 z2)") == ZipCommand(
    outcome="outcome",
    predictors=("x1", "x2"),
    inflate_predictors=("z1", "z2"),
  )
  assert parse_command("zip outcome x1, inflate(z1) robust") == ZipCommand(
    outcome="outcome",
    predictors=("x1",),
    inflate_predictors=("z1",),
    robust=True,
  )
  assert parse_command("zip outcome x1, inflate(z1) cluster(group_id)") == ZipCommand(
    outcome="outcome",
    predictors=("x1",),
    inflate_predictors=("z1",),
    cluster_variable="group_id",
  )
  assert parse_command("zip outcome x1, inflate(z1) noconstant") == ZipCommand(
    outcome="outcome",
    predictors=("x1",),
    inflate_predictors=("z1",),
    include_intercept=False,
  )


def test_parse_phase_16_zinb_command() -> None:
  assert parse_command("zinb outcome x1 x2, inflate(z1 z2)") == ZinbCommand(
    outcome="outcome",
    predictors=("x1", "x2"),
    inflate_predictors=("z1", "z2"),
  )
  assert parse_command("zinb outcome x1, inflate(z1) robust") == ZinbCommand(
    outcome="outcome",
    predictors=("x1",),
    inflate_predictors=("z1",),
    robust=True,
  )
  assert parse_command("zinb outcome x1, inflate(z1) cluster(group_id)") == ZinbCommand(
    outcome="outcome",
    predictors=("x1",),
    inflate_predictors=("z1",),
    cluster_variable="group_id",
  )
  assert parse_command("zinb outcome x1, inflate(z1) noconstant") == ZinbCommand(
    outcome="outcome",
    predictors=("x1",),
    inflate_predictors=("z1",),
    include_intercept=False,
  )


def test_parse_phase_16_streg_command() -> None:
  assert parse_command("streg time age income, failure(died) dist(weibull)") == StregCommand(
    time_variable="time",
    predictors=("age", "income"),
    failure_variable="died",
    distribution="weibull",
  )
  assert parse_command("streg time age, failure(died) dist(exponential) robust") == StregCommand(
    time_variable="time",
    predictors=("age",),
    failure_variable="died",
    distribution="exponential",
    robust=True,
  )
  assert parse_command(
    "streg time age, failure(died) dist(weibull) cluster(group_id) noconstant"
  ) == StregCommand(
    time_variable="time",
    predictors=("age",),
    failure_variable="died",
    distribution="weibull",
    cluster_variable="group_id",
    include_intercept=False,
  )


def test_parse_phase_13_estat_command() -> None:
  assert parse_command("estat residuals") == EstatCommand(subcommand="residuals")
  assert parse_command("estat ovtest") == EstatCommand(subcommand="ovtest")
  assert parse_command("estat vif") == EstatCommand(subcommand="vif")
  assert parse_command("estat firststage") == EstatCommand(subcommand="firststage")
  assert parse_command("estat overid") == EstatCommand(subcommand="overid")
  assert parse_command("estat hausman") == EstatCommand(subcommand="hausman")
  assert parse_command("estat endogenous") == EstatCommand(subcommand="endogenous")
  assert parse_command("estat margins") == EstatCommand(subcommand="margins")
  assert parse_command("estat gof") == EstatCommand(subcommand="gof")
  assert parse_command("estat did") == EstatCommand(subcommand="did")
  assert parse_command("estat drdid") == EstatCommand(subcommand="drdid")
  assert parse_command("estat bayes") == EstatCommand(subcommand="bayes")


def test_parse_phase_14_ivregress_command() -> None:
  assert parse_command("ivregress 2sls cost age bmi, endog(hours) iv(distance policy)") == (
    IvRegressCommand(
      outcome="cost",
      exogenous=("age", "bmi"),
      endogenous="hours",
      instruments=("distance", "policy"),
      estimator="2sls",
    )
  )
  assert parse_command("ivregress 2sls cost, endog(hours) iv(distance) robust") == IvRegressCommand(
    outcome="cost",
    exogenous=(),
    endogenous="hours",
    instruments=("distance",),
    robust=True,
    estimator="2sls",
  )
  assert parse_command(
    "ivregress 2sls cost age, endog(hours) iv(distance) cluster(group_id) noconstant"
  ) == IvRegressCommand(
    outcome="cost",
    exogenous=("age",),
    endogenous="hours",
    instruments=("distance",),
    cluster_variable="group_id",
    include_intercept=False,
    estimator="2sls",
  )
  assert parse_command("ivregress gmm cost age, endog(hours) iv(distance policy)") == (
    IvRegressCommand(
      outcome="cost",
      exogenous=("age",),
      endogenous="hours",
      instruments=("distance", "policy"),
      estimator="gmm",
    )
  )


def test_parse_phase_14_xtreg_command() -> None:
  assert parse_command("xtreg wage exper tenure, fe") == XtRegCommand(
    outcome="wage",
    predictors=("exper", "tenure"),
    estimator="fe",
  )
  assert parse_command("xtreg wage exper, re robust") == XtRegCommand(
    outcome="wage",
    predictors=("exper",),
    estimator="re",
    robust=True,
  )
  assert parse_command("xtreg wage exper, fe cluster(firm_id)") == XtRegCommand(
    outcome="wage",
    predictors=("exper",),
    estimator="fe",
    cluster_variable="firm_id",
  )


def test_parse_phase_14_xtdata_command() -> None:
  assert parse_command("xtdata wage exper, within") == XtDataCommand(
    variables=("wage", "exper"),
    transform="within",
  )
  assert parse_command("xtdata wage, between") == XtDataCommand(
    variables=("wage",),
    transform="between",
  )


def test_parse_phase_17_xtabond_command() -> None:
  assert parse_command("xtabond wage") == XtAbondCommand(
    outcome="wage",
    predictors=(),
  )
  assert parse_command("xtabond wage exposure, robust") == XtAbondCommand(
    outcome="wage",
    predictors=("exposure",),
    robust=True,
  )
  assert parse_command("xtabond wage exposure, lags(2) instlag(3)") == XtAbondCommand(
    outcome="wage",
    predictors=("exposure",),
    lag_depth=2,
    instrument_lag_start=3,
  )


def test_parse_phase_17_xtlogit_command() -> None:
  assert parse_command("xtlogit promoted training tenure, fe") == XtLogitCommand(
    outcome="promoted",
    predictors=("training", "tenure"),
  )
  assert parse_command("xtlogit promoted training, fe robust") == XtLogitCommand(
    outcome="promoted",
    predictors=("training",),
    robust=True,
  )


def test_parse_phase_17_lowess_command() -> None:
  assert parse_command("lowess wage exper, gen(wage_lowess)") == LowessCommand(
    outcome="wage",
    predictor="exper",
    target_variable="wage_lowess",
    bandwidth=2.0 / 3.0,
  )
  assert parse_command("lowess wage exper, gen(wage_lowess) bandwidth=0.5") == LowessCommand(
    outcome="wage",
    predictor="exper",
    target_variable="wage_lowess",
    bandwidth=0.5,
  )


def test_parse_phase_14_cfregress_command() -> None:
  assert parse_command("cfregress cost age bmi, endog(hours) iv(distance policy)") == (
    CfRegressCommand(
      outcome="cost",
      exogenous=("age", "bmi"),
      endogenous="hours",
      instruments=("distance", "policy"),
    )
  )
  assert parse_command("cfregress cost, endog(hours) iv(distance) robust") == CfRegressCommand(
    outcome="cost",
    exogenous=(),
    endogenous="hours",
    instruments=("distance",),
    robust=True,
  )
  assert parse_command(
    "cfregress cost age, endog(hours) iv(distance) cluster(group_id) noconstant"
  ) == CfRegressCommand(
    outcome="cost",
    exogenous=("age",),
    endogenous="hours",
    instruments=("distance",),
    cluster_variable="group_id",
    include_intercept=False,
  )


def test_parse_phase_20_drdid_command() -> None:
  assert parse_command("drdid wage exper tenure, treat(treated) post(post)") == DrDidCommand(
    outcome="wage",
    covariates=("exper", "tenure"),
    treatment_variable="treated",
    post_variable="post",
    method="aipw",
  )
  assert parse_command(
    "drdid wage, treat(treated) post(post) method(or) robust bootstrap(100) seed(42)"
  ) == DrDidCommand(
    outcome="wage",
    covariates=(),
    treatment_variable="treated",
    post_variable="post",
    method="or",
    robust=True,
    bootstrap=100,
    seed=42,
  )


def test_parse_phase_17_did_command() -> None:
  assert parse_command("did wage exper tenure, treat(treated) post(post)") == DidCommand(
    outcome="wage",
    controls=("exper", "tenure"),
    treatment_variable="treated",
    post_variable="post",
  )
  assert parse_command("did wage, treat(treated) post(post) robust") == DidCommand(
    outcome="wage",
    controls=(),
    treatment_variable="treated",
    post_variable="post",
    robust=True,
  )


def test_parse_phase_6_visualization_commands() -> None:
  assert parse_command("histogram age") == HistogramCommand(variable="age")
  assert parse_command("histogram age, bins=20 saving(figures/age.svg) noopen") == (
    HistogramCommand(
      variable="age",
      bins=20,
      saving=Path("figures/age.svg"),
      open_artifact=False,
    )
  )
  assert parse_command("scatter bmi age") == ScatterCommand(
    y_variable="bmi",
    x_variable="age",
  )
  assert parse_command("scatter bmi age, saving(artifacts/bmi-age.png)") == ScatterCommand(
    y_variable="bmi",
    x_variable="age",
    saving=Path("artifacts/bmi-age.png"),
  )
  assert parse_command("bar sex, missing noopen") == BarCommand(
    variable="sex",
    include_missing=True,
    open_artifact=False,
  )


def test_parse_expression_with_precedence_and_function_call() -> None:
  assert parse_expression("sqrt(age + 1) >= 5") == BinaryExpression(
    left=FunctionCallExpression(
      name="sqrt",
      arguments=(
        BinaryExpression(
          left=IdentifierExpression("age"),
          operator="+",
          right=NumberExpression(1),
        ),
      ),
    ),
    operator=">=",
    right=NumberExpression(5),
  )


def test_parse_exit_aliases() -> None:
  assert parse_command("exit") == ExitCommand()
  assert parse_command("quit") == ExitCommand()


@pytest.mark.parametrize(
  "text",
  [
    "",
    "use",
    "use one.parquet two.parquet",
    "use data.parquet,",
    "use data.parquet, eager",
    "use data.parquet, lazy=true",
    "use data.parquet, lazy lazy",
    "use data.parquet, engine=duckdb",
    "use data.parquet, lazy engine=spark",
    "join",
    "join lookup",
    "join lookup id",
    "join lookup on",
    "join lookup on id id",
    "join lookup on id, how=right",
    "join lookup on id, suffix()",
    "join lookup on id, suffix(_x) suffix(_y)",
    "join lookup on id, replace",
    "join active on id",
    "join bad-name on id",
    "append",
    "append followup extra",
    "append followup, replace",
    "append followup if age > 18",
    "append active",
    "append bad-name",
    "reshape",
    "reshape wider income, i(id) j(year)",
    "reshape long, i(id) j(year)",
    "reshape long income if age > 18, i(id) j(year)",
    "reshape long income = cost, i(id) j(year)",
    "reshape long income, i(id)",
    "reshape long income, j(year)",
    "reshape long income, i() j(year)",
    "reshape long income, i(id) j(year month)",
    "reshape long income income, i(id) j(year)",
    "reshape long income, i(id id) j(year)",
    "reshape long income, i(id) j(income)",
    "reshape long income, i(income) j(year)",
    "reshape long income, i(id) j(year), extra",
    "reshape long income, i(id) j(year) replace",
    "panel firm_id year extra",
    "panel firm_id if year > 2020",
    "panel firm_id year, replace",
    "panel firm_id = year",
    "panel firm_id firm_id",
    "panel clear now",
    "describe age",
    "describe if age > 18",
    "exit now",
    "unknown",
    "summarize age = 5",
    "summarize age if",
    "summarize age if age >=",
    "summarize age if if age > 18",
    "summarize age if age > 18 if bmi > 20",
    "summarize age,",
    "summarize age, limit=",
    "summarize age, limit 10",
    "codebook age if age > 18",
    "codebook age, detail",
    "count age",
    "count if age > 18",
    "head 1 2",
    "head -1",
    "head 1.5",
    "head five",
    "head, limit=10",
    "tail 1 2",
    "tail -1",
    "tail 1.5",
    "tail five",
    "tail if age > 18",
    "keep",
    "keep age if age > 18",
    "drop",
    "drop age = 1",
    "select",
    "select age if age > 18",
    "rename age",
    "rename age years now",
    "generate new",
    "generate new = age if age > 18",
    "replace cost",
    "replace cost = cost * 2, force",
    "tabulate",
    "tabulate age bmi sex",
    "tabulate age, row",
    "tabulate age bmi, exact",
    "collapse median age, by(sex)",
    "collapse mean age",
    "collapse mean age, by()",
    "by: summarize age",
    "by sex:",
    "by sex: by age: count",
    "sql",
    'sql """select * from active',
    "sql select * from active into",
    "sql select * from active into active",
    "sql select * from active into __tabdat_next",
    "sql select * from active into bad-name",
    "histogram",
    "histogram age bmi",
    "histogram age if age > 18",
    "histogram age, width=200",
    "histogram age, bins=0",
    "histogram age, bins",
    "histogram age, bins=ten",
    "histogram age, noopen=false",
    "scatter bmi",
    "scatter bmi age cost",
    "scatter bmi age, bins=20",
    "scatter bmi age, noopen=true",
    "bar",
    "bar sex age",
    "bar sex, bins=20",
    "bar sex, missing=true",
    "run",
    "run first.td second.td",
    "set",
    "set graph_format",
    "set unknown on",
    "regress",
    "regress cost",
    "regress cost age if age > 18",
    "regress cost age, robust cluster(sex)",
    "regress cost age, cluster",
    "regress cost age, cluster()",
    "regress cost age, cluster(sex firm)",
    "regress cost age, wls",
    "regress cost age, wls()",
    "regress cost age, wls(age bmi)",
    "regress cost age, gls",
    "regress cost age, gls()",
    "regress cost age, gls(age bmi)",
    "regress cost age, wls(age) gls(sigma)",
    "regress cost age, robust=true",
    "regress cost age, noconstant=true",
    "logit",
    "logit y",
    "logit y x if y == 1",
    "logit y x, robust cluster(group)",
    "logit y x, cluster()",
    "logit y x, cluster(group firm)",
    "logit y x, robust=true",
    "probit",
    "probit y",
    "probit y x if y == 1",
    "probit y x, robust cluster(group)",
    "probit y x, cluster()",
    "probit y x, cluster(group firm)",
    "probit y x, robust=true",
    "predict",
    "predict a b",
    "predict cost_hat if age > 18",
    "predict cost_hat, xb residuals",
    "predict cost_hat, xb spatial_lag",
    "predict cost_hat, xb posterior_predictive",
    "predict cost_hat, pr residuals",
    "predict cost_hat, pr spatial_lag",
    "predict cost_hat, pr posterior_predictive",
    "predict cost_hat, residuals spatial_lag",
    "predict cost_hat, residuals posterior_predictive",
    "predict cost_hat, spatial_lag posterior_predictive",
    "predict cost_hat, residuals=true",
    "tobit",
    "tobit y",
    "tobit y x",
    "tobit y x if y > 0",
    "tobit y x, ll()",
    "tobit y x, ll(low)",
    "tobit y x, ul(1)",
    "tobit y x, ll(0) robust cluster(group)",
    "tobit y x, ll(0) cluster()",
    "tobit y x, ll(0) cluster(group firm)",
    "tobit y x, ll(0) robust=true",
    "heckman",
    "heckman y",
    "heckman y x",
    "heckman y x if y > 0",
    "heckman y x, selectdep() select(z)",
    "heckman y x, selectdep(s t) select(z)",
    "heckman y x, selectdep(s)",
    "heckman y x, select(s)",
    "heckman y x, selectdep(s) select()",
    "heckman y x, selectdep(s) select(z) robust cluster(group)",
    "heckman y x, selectdep(s) select(z) cluster()",
    "heckman y x, selectdep(s) select(z) cluster(group firm)",
    "heckman y x, selectdep(s) select(z) robust=true",
    "nl",
    "nl y x",
    "nl y = x",
    "nl y = a + b*x, params(a b)",
    "nl y = a + b*x, start(1 2)",
    "nl y = a + b*x, params(a b) start(1)",
    "nl y = a + b*x, params(a b) start(1 two)",
    "nl y = a + b*x, params(a a) start(1 2)",
    "nl y = a + b*x if y > 0, params(a b) start(1 2)",
    "nl y = a + b*x, robust=true params(a b) start(1 2)",
    "poisson",
    "poisson y",
    "poisson y x if y > 0",
    "poisson y x, robust cluster(group)",
    "poisson y x, cluster()",
    "poisson y x, cluster(group firm)",
    "poisson y x, robust=true",
    "qreg",
    "qreg y",
    "qreg y x if y > 0",
    "qreg y x, cluster(group)",
    "qreg y x, quantile()",
    "qreg y x, quantile(0)",
    "qreg y x, quantile(1)",
    "qreg y x, quantile(1.2)",
    "qreg y x, robust=true",
    "lasso",
    "lasso linear",
    "lasso linear y",
    "lasso logistic y x",
    "lasso linear y x if y > 0",
    "lasso linear y x, alpha()",
    "lasso linear y x, alpha(-1)",
    "lasso linear y x, robust",
    "postlasso",
    "postlasso linear",
    "postlasso linear y",
    "postlasso logistic y x",
    "postlasso linear y x if y > 0",
    "postlasso linear y x, alpha()",
    "postlasso linear y x, alpha(-1)",
    "postlasso linear y x, cv(5)",
    "dml",
    "dml linear",
    "dml linear y",
    "dml logistic y x, treat(d)",
    "dml linear y x if y > 0, treat(d)",
    "dml linear y, treat(d)",
    "dml linear y x, treat()",
    "dml linear y x, alpha()",
    "dml linear y x, alpha(-1)",
    "dml linear y x, folds(1)",
    "dml linear y x, treat(d) robust=true",
    "ridge",
    "ridge linear",
    "ridge linear y",
    "ridge logistic y x",
    "ridge linear y x if y > 0",
    "ridge linear y x, alpha()",
    "ridge linear y x, alpha(-1)",
    "ridge linear y x, robust",
    "elasticnet",
    "elasticnet linear",
    "elasticnet linear y",
    "elasticnet logistic y x",
    "elasticnet linear y x if y > 0",
    "elasticnet linear y x, alpha()",
    "elasticnet linear y x, alpha(-1)",
    "elasticnet linear y x, l1_ratio()",
    "elasticnet linear y x, l1_ratio(-0.5)",
    "elasticnet linear y x, l1_ratio(1.5)",
    "elasticnet linear y x, robust",
    "bayes",
    "bayes linear",
    "bayes linear y",
    "bayes logistic y x",
    "bayes linear y x if y > 0",
    "bayes linear y x, n_iter()",
    "bayes linear y x, n_iter(-10)",
    "bayes linear y x, tol()",
    "bayes linear y x, tol(-0.5)",
    "bayes linear y x, alpha(1)",
    "bayes linear y x, robust",
    "nbreg",
    "nbreg y",
    "nbreg y x if y > 0",
    "nbreg y x, robust cluster(group)",
    "nbreg y x, cluster()",
    "nbreg y x, cluster(group firm)",
    "nbreg y x, robust=true",
    "zip",
    "zip y",
    "zip y x",
    "zip y x if y > 0, inflate(z)",
    "zip y x, inflate()",
    "zip y x, robust cluster(group) inflate(z)",
    "zip y x, cluster() inflate(z)",
    "zip y x, cluster(group firm) inflate(z)",
    "zip y x, robust=true inflate(z)",
    "zinb",
    "zinb y",
    "zinb y x",
    "zinb y x if y > 0, inflate(z)",
    "zinb y x, inflate()",
    "zinb y x, robust cluster(group) inflate(z)",
    "zinb y x, cluster() inflate(z)",
    "zinb y x, cluster(group firm) inflate(z)",
    "zinb y x, robust=true inflate(z)",
    "streg",
    "streg time",
    "streg time age",
    "streg time age if time > 0, failure(event) dist(weibull)",
    "streg time age, failure() dist(weibull)",
    "streg time age, failure(event event2) dist(weibull)",
    "streg time age, failure(event) dist()",
    "streg time age, failure(event) dist(loglogistic)",
    "streg time age, failure(event) dist(weibull) robust cluster(group)",
    "streg time age, failure(event) dist(weibull) cluster()",
    "streg time age, failure(event) dist(weibull) cluster(group firm)",
    "streg time age, failure(event) dist(weibull) robust=true",
    "estat",
    "estat vif extra",
    "estat, vif",
    "estat detail",
    "estat residuals, detail",
    "estat first",
    "estat endog",
    "estat margin",
    "estat bayes detail",
    "ivregress",
    "ivregress liml y x, endog(z) iv(w)",
    "ivregress 2sls y x",
    "ivregress 2sls y x, endog(z)",
    "ivregress 2sls y x, iv(w)",
    "ivregress 2sls y x, endog(z w) iv(q)",
    "ivregress 2sls y x, endog(z) iv()",
    "ivregress 2sls y x, endog(z) iv(w) robust cluster(g)",
    "ivregress 2sls y z, endog(z) iv(w)",
    "ivregress 2sls y x, endog(z) iv(w) robust=true",
    "xtreg",
    "xtreg y, fe",
    "xtreg y x",
    "xtreg y x, fe re",
    "xtreg y x, robust",
    "xtreg y x, cluster(firm)",
    "xtreg y x, fe cluster(firm) robust",
    "xtreg y x, fe cluster(firm year)",
    "xtreg y x, fe=true",
    "xtdata",
    "xtdata wage",
    "xtdata wage, within between",
    "xtdata wage, detail",
    "xtdata wage, within=true",
    "xtdata wage if year > 2020, within",
    "xtlogit",
    "xtlogit y x",
    "xtlogit y x, fe re",
    "xtlogit y x, robust",
    "xtlogit y x, fe cluster(firm)",
    "xtabond",
    "xtabond y if year > 2020",
    "xtabond y, robust=true",
    "xtabond y, cluster(firm_id)",
    "xtabond y, lags(0)",
    "xtabond y, instlag(1)",
    "xtabond y, lags(2) instlag(2)",
    "lowess",
    "lowess y",
    "lowess y x",
    "lowess y x, gen()",
    "lowess y x, gen(y_hat) bandwidth=0",
    "lowess y x, gen(y_hat) bandwidth=1",
    "lowess y x, robust",
    "cfregress",
    "cfregress y x",
    "cfregress y x, endog(z)",
    "cfregress y x, iv(w)",
    "cfregress y x, endog(z w) iv(q)",
    "cfregress y x, endog(z) iv()",
    "cfregress y x, endog(z) iv(w) robust cluster(g)",
    "cfregress y z, endog(z) iv(w)",
    "cfregress y x, endog(z) iv(w) robust=true",
    "did",
    "did y",
    "did y x",
    "did y x, treat(t) post(p) robust=true",
    "did y x, treat() post(p)",
    "did y x, treat(t p) post(p)",
    "did y x, treat(t) post()",
    "did y x, treat(t) post(p q)",
    "did y x, robust",
    "did y x, treat(t) post(p) cluster(g)",
    "drdid",
    "drdid y",
    "drdid y x",
    "drdid y x, treat(t) post(p) robust=true",
    "drdid y x, treat() post(p)",
    "drdid y x, treat(t p) post(p)",
    "drdid y x, treat(t) post()",
    "drdid y x, treat(t) post(p q)",
    "drdid y x, robust",
    "drdid y x, treat(t) post(p) method(invalid)",
    "drdid y x, treat(t) post(p) seed(123)",
    "save",
    "save out.parquet, force",
    "save out.parquet, replace=true",
    "export",
    'summarize age if sex == "F',
    "summarize age if age $ 18",
  ],
)
def test_parse_invalid_commands(text: str) -> None:
  with pytest.raises(ParseError):
    parse_command(text)
