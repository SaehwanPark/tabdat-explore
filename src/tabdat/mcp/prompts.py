"""Prompt templates and handlers for TabDat MCP server."""

from __future__ import annotations

from typing import Any

from tabdat.mcp.types import (
  MCPGetPromptResult,
  MCPPrompt,
  MCPPromptArgument,
  MCPPromptMessage,
  MCPTextContent,
)

TABDAT_PROMPTS: list[MCPPrompt] = [
  MCPPrompt(
    name="eda_workflow",
    description=(
      "Guided workflow for exploratory data analysis on a tabular dataset using TabDat."
    ),
    arguments=[
      MCPPromptArgument(
        name="file_path",
        description="Path to the tabular file (Parquet, CSV, Feather, etc.).",
        required=True,
      ),
      MCPPromptArgument(
        name="focus_variables",
        description="Specific variables or columns to focus on during exploration.",
        required=False,
      ),
    ],
  ),
  MCPPrompt(
    name="econometric_analysis",
    description="Guided workflow for econometrics and regression modeling with robust diagnostics.",
    arguments=[
      MCPPromptArgument(
        name="file_path",
        description="Path to the dataset.",
        required=True,
      ),
      MCPPromptArgument(
        name="dependent_var",
        description="Dependent response variable.",
        required=True,
      ),
      MCPPromptArgument(
        name="independent_vars",
        description="Space-separated independent explanatory variables.",
        required=True,
      ),
      MCPPromptArgument(
        name="estimator",
        description=(
          "Estimator family (e.g. 'ols', 'robust', 'cluster', 'logit', 'probit', '2sls', 'fe')."
        ),
        required=False,
      ),
    ],
  ),
  MCPPrompt(
    name="data_cleaning",
    description="Guided workflow for variable creation, filtering, recoding, and export.",
    arguments=[
      MCPPromptArgument(
        name="file_path",
        description="Path to the dataset to transform.",
        required=True,
      ),
      MCPPromptArgument(
        name="task_description",
        description="Description of the cleaning or transformation tasks to perform.",
        required=True,
      ),
    ],
  ),
]


def handle_get_prompt(name: str, arguments: dict[str, Any] | None = None) -> MCPGetPromptResult:
  """Retrieve a populated prompt template by name.

  Args:
    name: The prompt name.
    arguments: Optional arguments dictionary.

  Returns:
    MCPGetPromptResult containing description and messages.
  """
  args = arguments or {}

  if name == "eda_workflow":
    file_path = args.get("file_path", "<path_to_data>")
    focus = args.get("focus_variables", "")
    focus_str = f" with special attention to: {focus}" if focus else ""
    prompt_text = (
      f"Please perform an exploratory data analysis on `{file_path}`{focus_str}.\n\n"
      "Recommended TabDat steps:\n"
      f"1. Load and inspect structure: `use {file_path}` followed by `describe` and `count`.\n"
      "2. Summarize numerical distributions: `summarize` (or `summarize <vars>`).\n"
      "3. Inspect unique values and missingness: `codebook` and `tabulate <categorical_var>`.\n"
      "4. Visualize key distributions: `histogram <var>` or `scatter <y> <x>`.\n"
      "5. Provide a clear synthesis of findings and data quality notes."
    )
    return MCPGetPromptResult(
      description=f"EDA Workflow for {file_path}",
      messages=[
        MCPPromptMessage(
          role="user",
          content=MCPTextContent(text=prompt_text),
        )
      ],
    )

  if name == "econometric_analysis":
    file_path = args.get("file_path", "<path_to_data>")
    depvar = args.get("dependent_var", "<y>")
    indepvars = args.get("independent_vars", "<x1> <x2>")
    estimator = args.get("estimator", "ols").lower()

    if estimator in ("robust", "hc1", "hc2", "hc3"):
      reg_cmd = f"regress {depvar} {indepvars}, robust"
    elif "cluster" in estimator:
      reg_cmd = f"regress {depvar} {indepvars}, cluster(<cluster_var>)"
    elif estimator == "logit":
      reg_cmd = f"logit {depvar} {indepvars}"
    elif estimator == "probit":
      reg_cmd = f"probit {depvar} {indepvars}"
    else:
      reg_cmd = f"regress {depvar} {indepvars}"

    diag_text = (
      "Post-estimation diagnostics: `estat vif` for multicollinearity, "
      "`estat hettest` for heteroskedasticity, `predict y_hat, xb` for fitted values."
    )
    prompt_text = (
      f"Please run an econometric analysis on `{file_path}` "
      f"modeling `{depvar}` against `{indepvars}`.\n\n"
      "Recommended TabDat workflow:\n"
      f"1. `use {file_path}`\n"
      f"2. `summarize {depvar} {indepvars}`\n"
      f"3. `{reg_cmd}`\n"
      f"4. {diag_text}\n"
      "5. Interpret point estimates, statistical significance, and effect magnitudes."
    )
    return MCPGetPromptResult(
      description=f"Econometric Analysis on {depvar}",
      messages=[
        MCPPromptMessage(
          role="user",
          content=MCPTextContent(text=prompt_text),
        )
      ],
    )

  if name == "data_cleaning":
    file_path = args.get("file_path", "<path_to_data>")
    task = args.get("task_description", "<cleaning_tasks>")
    prompt_text = (
      f"Please perform the following data cleaning task on `{file_path}`:\n{task}\n\n"
      "Use TabDat commands (`keep`, `drop`, `generate`, `replace`, `recode`, `rename`, `export`)."
    )
    return MCPGetPromptResult(
      description=f"Data Cleaning Workflow on {file_path}",
      messages=[
        MCPPromptMessage(
          role="user",
          content=MCPTextContent(text=prompt_text),
        )
      ],
    )

  raise ValueError(f"Unknown prompt template: {name}")
