"""HTML reporting backend for OLS/WLS regression results."""

from __future__ import annotations

import html
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import scipy.stats as stats

from tabdat.errors import ExecutionError
from tabdat.models import RegressionResult


def generate_html_report(
  result: RegressionResult,
  fitted_model: object,
  path: Path,
) -> Path:
  """Generate a self-contained interactive HTML diagnostic report for a regression.

  Args:
    result: The RegressionResult dataclass containing stats.
    fitted_model: The statsmodels regression results object.
    path: Output path for the HTML file.

  Returns:
    The path to the generated HTML file.
  """
  # Extract residuals, fitted values and actual values
  residuals = getattr(fitted_model, "resid", None)
  fitted_values = getattr(fitted_model, "fittedvalues", None)

  if residuals is None or fitted_values is None:
    raise ExecutionError("estat report failed: missing residuals or fitted values in fitted model")

  # Squeeze/ravel to 1D arrays
  residuals = np.ravel(residuals).astype(float)
  fitted_values = np.ravel(fitted_values).astype(float)

  # actual = fitted + resid
  # In case model.endog is available, we can use it, but fitted + resid
  # is mathematically identical for OLS.
  actual_values = getattr(getattr(fitted_model, "model", None), "endog", None)
  if actual_values is not None:
    actual_values = np.ravel(actual_values).astype(float)
  else:
    actual_values = fitted_values + residuals

  # Filter out non-finite entries (NaN/inf) from the arrays
  valid_mask = np.isfinite(residuals) & np.isfinite(fitted_values) & np.isfinite(actual_values)
  residuals = residuals[valid_mask]
  fitted_values = fitted_values[valid_mask]
  actual_values = actual_values[valid_mask]

  n = len(residuals)
  if n < 2:
    raise ExecutionError(
      "estat report requires at least 2 complete observations to calculate statistics"
    )

  # Standardized residuals
  resid_mean = np.mean(residuals)
  resid_std = np.std(residuals, ddof=1)
  if not np.isfinite(resid_std) or resid_std == 0:
    resid_std = 1.0  # Avoid division by zero
  std_residuals = (residuals - resid_mean) / resid_std

  # Sort standardized residuals for Q-Q plot
  sorted_std_residuals = np.sort(std_residuals)
  # Standard plotting positions for Q-Q
  positions = (np.arange(1, n + 1) - 3 / 8) / (n + 0.25)
  theoretical_quantiles = stats.norm.ppf(positions)

  # Fits a line to 25th and 75th percentiles of Q-Q plot
  x25, x75 = np.percentile(theoretical_quantiles, [25, 75])
  y25, y75 = np.percentile(sorted_std_residuals, [25, 75])

  # Handle zero division
  if abs(x75 - x25) > 1e-8:
    slope = (y75 - y25) / (x75 - x25)
  else:
    slope = 1.0
  intercept = y25 - slope * x25

  line_x = np.array([np.min(theoretical_quantiles), np.max(theoretical_quantiles)])
  line_y = slope * line_x + intercept

  # Construct plotting DataFrames
  df_res_fit = pd.DataFrame(
    {
      "fitted": fitted_values,
      "residual": residuals,
      "index": np.arange(n),
    }
  )

  df_qq = pd.DataFrame(
    {
      "theoretical": theoretical_quantiles,
      "standardized": sorted_std_residuals,
      "index": np.arange(n),
    }
  )

  df_act_fit = pd.DataFrame(
    {
      "fitted": fitted_values,
      "actual": actual_values,
      "index": np.arange(n),
    }
  )

  # Performance Downsampling: Sample at most 5,000 observations to keep HTML
  # generation/rendering fast.
  MAX_PLOT_POINTS = 5000
  if n > MAX_PLOT_POINTS:
    # Use deterministic seeding to make the sample consistent across runs of the same model fit
    rng = np.random.default_rng(seed=42)
    sample_indices = rng.choice(n, size=MAX_PLOT_POINTS, replace=False)

    df_res_fit = df_res_fit.iloc[sample_indices].reset_index(drop=True)
    df_qq = df_qq.iloc[sample_indices].reset_index(drop=True)
    df_act_fit = df_act_fit.iloc[sample_indices].reset_index(drop=True)

  # 1. Residuals vs Fitted Plot
  chart_res_fit = (
    alt.Chart(df_res_fit)
    .mark_point(color="#3b82f6", opacity=0.7)
    .encode(
      x=alt.X("fitted:Q", title="Fitted Values"),
      y=alt.Y("residual:Q", title="Residuals"),
      tooltip=[
        alt.Tooltip("index:Q", title="Observation"),
        alt.Tooltip("fitted:Q", title="Fitted"),
        alt.Tooltip("residual:Q", title="Residual"),
      ],
    )
    .properties(title="Residuals vs Fitted", width="container", height=300)
  )

  # Reuse the sampled frame so Altair does not serialize a one-row reference-line
  # dataset ahead of the diagnostic observations in the embedded chart payload.
  line_y0 = (
    alt.Chart(df_res_fit).mark_rule(color="#ef4444", strokeDash=[4, 4]).encode(y=alt.datum(0.0))
  )
  plot_res_fit = (chart_res_fit + line_y0).interactive()

  # 2. Normal Q-Q Plot
  chart_qq = (
    alt.Chart(df_qq)
    .mark_point(color="#8b5cf6", opacity=0.7)
    .encode(
      x=alt.X("theoretical:Q", title="Theoretical Quantiles"),
      y=alt.Y("standardized:Q", title="Standardized Residuals"),
      tooltip=[
        alt.Tooltip("index:Q", title="Observation Index"),
        alt.Tooltip("theoretical:Q", title="Theoretical Quantile"),
        alt.Tooltip("standardized:Q", title="Standardized Residual"),
      ],
    )
    .properties(title="Normal Q-Q Plot", width="container", height=300)
  )

  df_qq_line = pd.DataFrame(
    {
      "x": line_x,
      "y": line_y,
    }
  )
  line_qq = (
    alt.Chart(df_qq_line)
    .mark_line(color="#ef4444", strokeDash=[4, 4])
    .encode(
      x="x:Q",
      y="y:Q",
    )
  )
  plot_qq = (chart_qq + line_qq).interactive()

  # 3. Actual vs Fitted Plot
  chart_act_fit = (
    alt.Chart(df_act_fit)
    .mark_point(color="#10b981", opacity=0.7)
    .encode(
      x=alt.X("fitted:Q", title="Fitted Values"),
      y=alt.Y("actual:Q", title="Actual Values"),
      tooltip=[
        alt.Tooltip("index:Q", title="Observation"),
        alt.Tooltip("fitted:Q", title="Fitted"),
        alt.Tooltip("actual:Q", title="Actual"),
      ],
    )
    .properties(title="Actual vs Fitted", width="container", height=300)
  )

  min_val = float(min(np.min(fitted_values), np.min(actual_values)))
  max_val = float(max(np.max(fitted_values), np.max(actual_values)))
  df_identity = pd.DataFrame({"x": [min_val, max_val], "y": [min_val, max_val]})
  line_identity = (
    alt.Chart(df_identity)
    .mark_line(color="#ef4444", strokeDash=[4, 4])
    .encode(
      x="x:Q",
      y="y:Q",
    )
  )
  plot_act_fit = (chart_act_fit + line_identity).interactive()

  # Convert charts to JSON specs (handling numpy types and escaping < for script tags)
  spec_res_fit = plot_res_fit.to_json().replace("<", "\\u003c")
  spec_qq = plot_qq.to_json().replace("<", "\\u003c")
  spec_act_fit = plot_act_fit.to_json().replace("<", "\\u003c")

  # Extract confidence intervals safely using positional index
  conf_int_lower = []
  conf_int_upper = []
  try:
    conf_ints = getattr(fitted_model, "conf_int", lambda: None)()
    if conf_ints is not None:
      conf_ints_arr = np.asarray(conf_ints)
      for idx in range(len(result.coefficients)):
        if idx < len(conf_ints_arr):
          conf_int_lower.append(float(conf_ints_arr[idx, 0]))
          conf_int_upper.append(float(conf_ints_arr[idx, 1]))
        else:
          conf_int_lower.append(None)
          conf_int_upper.append(None)
  except Exception:
    pass

  # Build coefficients table rows with escaping
  coef_rows = []
  for idx, coef in enumerate(result.coefficients):
    low = conf_int_lower[idx] if idx < len(conf_int_lower) else None
    high = conf_int_upper[idx] if idx < len(conf_int_upper) else None

    std_err_str = f"{coef.standard_error:.6f}" if coef.standard_error is not None else ""
    stat_str = f"{coef.statistic:.4f}" if coef.statistic is not None else ""
    p_val_str = f"{coef.p_value:.4f}" if coef.p_value is not None else ""
    ci_str = f"[{low:.6f}, {high:.6f}]" if (low is not None and high is not None) else ""

    escaped_name = html.escape(coef.name)

    coef_rows.append(
      f"<tr>\n"
      f"  <td style='font-weight: 500;'>{escaped_name}</td>\n"
      f"  <td class='number'>{coef.value:.6f}</td>\n"
      f"  <td class='number'>{std_err_str}</td>\n"
      f"  <td class='number'>{stat_str}</td>\n"
      f"  <td class='number'>{p_val_str}</td>\n"
      f"  <td class='number'>{ci_str}</td>\n"
      f"</tr>"
    )

  # Render HTML template with escaping for text fields
  html_content = _HTML_TEMPLATE.format(
    outcome=html.escape(result.outcome),
    predictors=", ".join(html.escape(pred) for pred in result.predictors),
    estimator=html.escape(result.estimator.upper()),
    covariance=html.escape(result.covariance),
    observations=result.observation_count,
    r_squared=f"{result.r_squared:.4f}" if result.r_squared is not None else "",
    adj_r_squared=f"{result.adjusted_r_squared:.4f}"
    if result.adjusted_r_squared is not None
    else "",
    root_mse=f"{result.root_mse:.4f}" if result.root_mse is not None else "",
    coef_rows="\n".join(coef_rows),
    spec_res_fit=spec_res_fit,
    spec_qq=spec_qq,
    spec_act_fit=spec_act_fit,
  )

  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(html_content, encoding="utf-8")
  return path


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TabDat Regression Diagnostic Report</title>
  <!-- Load Inter Font -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link
    href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
    rel="stylesheet"
  >
  <!-- Load Vega Embed (Using Vega-Lite v6 CDN imports to match Altair spec version) -->
  <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@6"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
  <style>
    :root {{
      --bg-color: #0f172a;
      --card-bg: #1e293b;
      --border-color: #334155;
      --text-color: #f8fafc;
      --text-muted: #94a3b8;
      --primary-color: #6366f1;
      --accent-color: #ef4444;
      --table-hover: #334155;
    }}

    body {{
      background-color: var(--bg-color);
      color: var(--text-color);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      margin: 0;
      padding: 2rem;
    }}

    .container {{
      max-width: 1200px;
      margin: 0 auto;
    }}

    .header {{
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 1.5rem;
      margin-bottom: 2rem;
    }}

    .header h1 {{
      margin: 0;
      font-size: 2.25rem;
      font-weight: 700;
      background: linear-gradient(to right, #818cf8, #c084fc);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}

    .header p {{
      color: var(--text-muted);
      margin: 0.5rem 0 0 0;
      font-size: 1rem;
    }}

    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }}

    .card {{
      background-color: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 1.5rem;
      box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    }}

    .stat-label {{
      font-size: 0.75rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.5rem;
    }}

    .stat-value {{
      font-size: 1.35rem;
      font-weight: 600;
    }}

    .table-card {{
      margin-bottom: 2rem;
      overflow-x: auto;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
    }}

    th {{
      text-align: left;
      padding: 0.75rem 1rem;
      font-size: 0.75rem;
      color: var(--text-muted);
      border-bottom: 2px solid var(--border-color);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    td {{
      padding: 0.75rem 1rem;
      border-bottom: 1px solid var(--border-color);
      font-size: 0.9rem;
    }}

    .number {{
      text-align: right;
      font-family: monospace;
    }}

    th.number {{
      text-align: right;
    }}

    tr:hover {{
      background-color: var(--table-hover);
    }}

    .plots-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
      gap: 1.5rem;
    }}

    .plot-container {{
      width: 100%;
      height: 300px;
    }}

    .plot-card h3 {{
      margin-top: 0;
      margin-bottom: 1rem;
      font-size: 1.1rem;
      color: var(--text-color);
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Regression Diagnostic Report</h1>
      <p>Interactive diagnostics for OLS model fit in TabDat-Explore</p>
    </div>

    <div class="stats-grid">
      <div class="card">
        <div class="stat-label">Model</div>
        <div class="stat-value">{outcome} on {predictors}</div>
      </div>
      <div class="card">
        <div class="stat-label">Estimator</div>
        <div class="stat-value">{estimator}</div>
      </div>
      <div class="card">
        <div class="stat-label">Covariance</div>
        <div class="stat-value">{covariance}</div>
      </div>
      <div class="card">
        <div class="stat-label">Observations</div>
        <div class="stat-value">{observations}</div>
      </div>
    </div>

    <div class="stats-grid">
      <div class="card">
        <div class="stat-label">R-squared</div>
        <div class="stat-value">{r_squared}</div>
      </div>
      <div class="card">
        <div class="stat-label">Adj. R-squared</div>
        <div class="stat-value">{adj_r_squared}</div>
      </div>
      <div class="card">
        <div class="stat-label">Root MSE</div>
        <div class="stat-value">{root_mse}</div>
      </div>
    </div>

    <div class="card table-card">
      <div class="stat-label">Parameter Estimates</div>
      <table>
        <thead>
          <tr>
            <th>Variable</th>
            <th class="number">Coef</th>
            <th class="number">Std Err</th>
            <th class="number">t</th>
            <th class="number">P&gt;|t|</th>
            <th class="number">[95% Conf. Interval]</th>
          </tr>
        </thead>
        <tbody>
          {coef_rows}
        </tbody>
      </table>
    </div>

    <div class="plots-grid">
      <div class="card plot-card">
        <h3>Residuals vs Fitted</h3>
        <div id="plot-res-fit" class="plot-container"></div>
      </div>
      <div class="card plot-card">
        <h3>Normal Q-Q</h3>
        <div id="plot-qq" class="plot-container"></div>
      </div>
      <div class="card plot-card">
        <h3>Actual vs Fitted</h3>
        <div id="plot-act-fit" class="plot-container"></div>
      </div>
    </div>
  </div>

  <script>
    const specResFit = {spec_res_fit};
    const specQQ = {spec_qq};
    const specActFit = {spec_act_fit};

    // VegaEmbed Theme config to fit dark mode dashboard style
    const embedOpts = {{
      actions: false,
      theme: 'dark'
    }};

    vegaEmbed('#plot-res-fit', specResFit, embedOpts).catch(console.error);
    vegaEmbed('#plot-qq', specQQ, embedOpts).catch(console.error);
    vegaEmbed('#plot-act-fit', specActFit, embedOpts).catch(console.error);
  </script>
</body>
</html>
"""
