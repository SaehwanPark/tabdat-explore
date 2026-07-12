"""Integrated public-dataset E2E harness for TabDat-Explore."""

from __future__ import annotations

import argparse
import json
import os
import pty
import re
import select
import shutil
import signal
import subprocess
import time
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = REPO_ROOT / "artifacts" / "e2e"
DATA_DIR = ARTIFACT_ROOT / "data"
REPORT_ROOT = REPO_ROOT / "integrated_testing" / "reports" / "latest"
TTY_HOME = ARTIFACT_ROOT / "home"


@dataclass(frozen=True)
class CommandSpec:
  argv: tuple[str, ...]
  stdout_contains: tuple[str, ...] = ()
  stdout_regex: tuple[str, ...] = ()
  expected_files: tuple[Path, ...] = ()
  expected_stderr: str = ""


@dataclass
class ScenarioResult:
  scenario_id: str
  passed: bool
  checks: list[str] = field(default_factory=list)
  failures: list[str] = field(default_factory=list)
  stdout_path: str | None = None
  stderr_path: str | None = None
  exit_code: int | None = None
  duration_seconds: float | None = None
  metrics: dict[str, bool | float | int | str] = field(default_factory=dict)


def main(argv: Sequence[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("scenarios", nargs="*", help="scenario IDs to run")
  parser.add_argument("--no-clean", action="store_true", help="keep existing generated artifacts")
  args = parser.parse_args(argv)

  selected = tuple(args.scenarios) or tuple(SCENARIOS)
  unknown = sorted(set(selected) - set(SCENARIOS))
  if unknown:
    parser.error(f"unknown scenarios: {', '.join(unknown)}")

  prepare_workspace(clean=not args.no_clean)
  ensure_datasets(selected)

  results = [SCENARIOS[scenario_id]() for scenario_id in selected]
  write_reports(results)
  return 0 if all(result.passed for result in results) else 1


def prepare_workspace(*, clean: bool) -> None:
  if clean:
    shutil.rmtree(ARTIFACT_ROOT, ignore_errors=True)
    shutil.rmtree(REPORT_ROOT, ignore_errors=True)
  DATA_DIR.mkdir(parents=True, exist_ok=True)
  REPORT_ROOT.mkdir(parents=True, exist_ok=True)
  TTY_HOME.mkdir(parents=True, exist_ok=True)


def ensure_datasets(selected: Sequence[str]) -> None:
  required = set()
  for scenario_id in selected:
    required.update(SCENARIO_DATASETS[scenario_id])

  if "titanic" in required:
    ensure_csv_parquet(
      "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/titanic.csv",
      DATA_DIR / "titanic.csv",
      DATA_DIR / "titanic.parquet",
    )
  if "penguins" in required:
    ensure_csv_parquet(
      "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/penguins.csv",
      DATA_DIR / "penguins.csv",
      DATA_DIR / "penguins.parquet",
    )
  if "nyc_taxi_jan_2023" in required:
    ensure_download(
      "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet",
      DATA_DIR / "yellow_tripdata_2023-01.parquet",
    )


def ensure_csv_parquet(url: str, csv_path: Path, parquet_path: Path) -> None:
  ensure_download(url, csv_path)
  if parquet_path.exists():
    return
  parquet_path.parent.mkdir(parents=True, exist_ok=True)
  con = duckdb.connect()
  try:
    con.execute(
      "create or replace table _e2e_source as select * from read_csv_auto(?)", [str(csv_path)]
    )
    con.execute("copy _e2e_source to ? (format parquet)", [str(parquet_path)])
  finally:
    con.close()


def ensure_download(url: str, destination: Path) -> None:
  if destination.exists() and destination.stat().st_size > 0:
    return
  destination.parent.mkdir(parents=True, exist_ok=True)
  tmp_path = destination.with_suffix(destination.suffix + ".tmp")
  with urllib.request.urlopen(url, timeout=120) as response:
    tmp_path.write_bytes(response.read())
  tmp_path.replace(destination)


def s1_titanic_batch_core() -> ScenarioResult:
  command = CommandSpec(
    argv=(
      "uv",
      "run",
      "tabdat",
      "-c",
      "use artifacts/e2e/data/titanic.parquet",
      "-c",
      "describe",
      "-c",
      "summarize age fare sibsp parch",
      "-c",
      "codebook sex class deck embarked survived",
      "-c",
      "count",
      "-c",
      "head 5",
      "-c",
      "tail 5",
      "-c",
      "keep if age >= 18",
      "-c",
      "drop deck alone",
      "-c",
      "rename sex gender",
      "-c",
      "generate family_size = sibsp + parch + 1",
      "-c",
      "replace fare = 0 if fare < 1",
      "-c",
      "select survived pclass class gender age fare family_size",
      "-c",
      "tabulate gender survived, row col missing",
      "-c",
      "by pclass: summarize age fare",
      "-c",
      "collapse mean age fare, by(survived)",
      "-c",
      "head 5",
    ),
    stdout_contains=(
      "Loaded: artifacts/e2e/data/titanic.parquet",
      "Rows:",
      "Variable  Type",
      "Variable  Count  Mean",
      "Nonmissing",
      "Distinct",
      "Examples",
      "Kept matching rows:",
      "Dropped selected columns:",
      "Renamed sex to gender:",
      "Generated family_size:",
      "Replaced fare:",
      "Selected columns:",
      "gender",
      "survived",
      "Row %",
      "Col %",
      "pclass",
      "Collapsed dataset:",
    ),
    stdout_regex=(
      r"Rows: [0-9]+",
      r"Collapsed dataset: [0-9]+ rows, 3 columns",
    ),
  )
  return run_command_scenario("s1_titanic_batch_core", command)


def s2_interactive_shell_contract() -> ScenarioResult:
  result = ScenarioResult("s2_interactive_shell_contract", passed=True)
  history_path = TTY_HOME / ".tabdat_history"
  history_path.unlink(missing_ok=True)
  env = os.environ.copy()
  env["HOME"] = str(TTY_HOME)
  output = ""

  child = spawn_pty(("uv", "run", "tabdat"), env=env)
  try:
    output += expect_output(child, "tabdat>", timeout=20)
    output += send_and_expect(child, "use artifacts/e2e/data/titanic.parquet\n", "Loaded:")
    output += send_and_expect(child, "summarize a\t", "age")
    output += send_and_expect(child, "\x03", "tabdat>")
    output += send_and_expect(child, "tabulate sex, \t", "missing")
    output += send_and_expect(child, "\x03", "tabdat>")
    output += send_and_expect(child, "by s\t", "sex")
    output += send_and_expect(child, "\x03", "tabdat>")
    output += send_and_expect(child, "by sex: sum\t", "summarize")
    output += send_and_expect(child, "\x03", "tabdat>")
    output += send_and_expect(child, "sql group\t", "group by")
    output += send_and_expect(child, "\x03", "tabdat>")
    output += send_and_expect(child, "histogram a\t", "age")
    output += send_and_expect(child, "\x03", "tabdat>")
    output += send_and_expect(child, "count\n", "Rows:")
    output += send_and_expect(child, "exit\n", "", timeout=10)
  except HarnessFailure as exc:
    result.passed = False
    result.failures.append(str(exc))
  finally:
    exit_code = close_pty(child)
    result.exit_code = exit_code

  stdout_path = write_log("s2_interactive_shell_contract", "stdout", output)
  stderr_path = write_log("s2_interactive_shell_contract", "stderr", "")
  result.stdout_path = str(stdout_path.relative_to(REPO_ROOT))
  result.stderr_path = str(stderr_path.relative_to(REPO_ROOT))
  check(result, exit_code == 0, f"exit code {exit_code}")
  check(result, history_path.exists(), f"history exists at {history_path}")
  if history_path.exists():
    history_text = history_path.read_text(encoding="utf-8")
    check(result, "use artifacts/e2e/data/titanic.parquet" in history_text, "history has use")
    check(result, "count" in history_text, "history has count")
  check(result, re.search(r"Rows: [0-9]+", output) is not None, "count printed row count")
  return result


def s3_taxi_lazy_scale() -> ScenarioResult:
  scenario_dir = ARTIFACT_ROOT / "s3"
  scenario_dir.mkdir(parents=True, exist_ok=True)
  command = CommandSpec(
    argv=(
      "uv",
      "run",
      "tabdat",
      "-c",
      "use artifacts/e2e/data/yellow_tripdata_2023-01.parquet, lazy engine=duckdb",
      "-c",
      "describe",
      "-c",
      "count",
      "-c",
      "select passenger_count trip_distance fare_amount tip_amount total_amount payment_type",
      "-c",
      "keep if trip_distance >= 10",
      "-c",
      "drop if fare_amount == 0",
      "-c",
      "generate tip_share = tip_amount / total_amount",
      "-c",
      "summarize trip_distance fare_amount tip_amount total_amount tip_share",
      "-c",
      (
        "sql select payment_type, avg(total_amount) as mean_total, "
        "avg(tip_share) as mean_tip_share from active group by payment_type order by payment_type"
      ),
      "-c",
      "histogram total_amount, bins=30 saving(artifacts/e2e/s3/total_amount_hist.svg) noopen",
      "-c",
      "bar payment_type, missing saving(artifacts/e2e/s3/payment_type_bar.svg) noopen",
      "-c",
      "save artifacts/e2e/s3/filtered_trips.parquet, replace",
      "-c",
      (
        "sql select payment_type, count(*) as n from active group by payment_type "
        "order by payment_type into payment_summary"
      ),
      "-c",
      "head 10",
    ),
    stdout_contains=(
      "Loaded: artifacts/e2e/data/yellow_tripdata_2023-01.parquet (unknown rows,",
      "lazy=duckdb",
      "Rows:",
      "Selected columns:",
      "Kept matching rows:",
      "Dropped matching rows:",
      "Generated tip_share:",
      "payment_type",
      "mean_total",
      "mean_tip_share",
      "Saved plot: artifacts/e2e/s3/total_amount_hist.svg",
      "Saved plot: artifacts/e2e/s3/payment_type_bar.svg",
      "Saved: artifacts/e2e/s3/filtered_trips.parquet",
      "Created payment_summary:",
    ),
    stdout_regex=(
      r"Rows: [0-9]+",
      r"Saved: artifacts/e2e/s3/filtered_trips.parquet \([0-9]+ rows, 7 columns\)",
    ),
    expected_files=(
      Path("artifacts/e2e/s3/total_amount_hist.svg"),
      Path("artifacts/e2e/s3/payment_type_bar.svg"),
      Path("artifacts/e2e/s3/filtered_trips.parquet"),
    ),
  )
  result = run_command_scenario("s3_taxi_lazy_scale", command)
  followup = CommandSpec(
    argv=(
      "uv",
      "run",
      "tabdat",
      "-c",
      "use artifacts/e2e/data/yellow_tripdata_2023-01.parquet, lazy engine=polars",
      "-c",
      "count",
      "-c",
      "head 2",
    ),
    stdout_contains=(
      "Loaded: artifacts/e2e/data/yellow_tripdata_2023-01.parquet (unknown rows,",
      "lazy=polars",
      "Rows:",
    ),
  )
  merge_result(result, run_command_scenario("s3_taxi_lazy_scale_followup", followup))
  return result


def s4_penguins_script_repro() -> ScenarioResult:
  scenario_dir = ARTIFACT_ROOT / "s4"
  scenario_dir.mkdir(parents=True, exist_ok=True)
  write_text(
    scenario_dir / "config.tabdat.toml",
    'graph_format = "png"\nartifact_dir = "artifacts/e2e/s4/artifacts"\ngraph_open = false\n',
  )
  write_text(
    scenario_dir / "prep.td",
    "\n".join(
      (
        "summarize bill_length_mm flipper_length_mm body_mass_g",
        "generate body_mass_kg = body_mass_g / 1000",
        "scatter body_mass_g flipper_length_mm, "
        "saving(artifacts/e2e/s4/artifacts/plots/penguins_scatter.png) noopen",
        "",
      )
    ),
  )
  write_text(
    scenario_dir / "analysis.td",
    "\n".join(
      (
        "use artifacts/e2e/data/penguins.parquet",
        "run prep.td",
        "tabulate species sex, row col missing",
        'sql """',
        "select",
        "  species,",
        "  avg(body_mass_kg) as mean_body_mass_kg,",
        "  avg(flipper_length_mm) as mean_flipper_length_mm",
        "from active",
        "group by species",
        "order by species",
        '""" into penguin_summary',
        "head 10",
        "export artifacts/e2e/s4/penguin_summary.parquet, replace",
        "",
      )
    ),
  )
  command = CommandSpec(
    argv=(
      "uv",
      "run",
      "tabdat",
      "--config",
      "artifacts/e2e/s4/config.tabdat.toml",
      "-f",
      "artifacts/e2e/s4/analysis.td",
    ),
    stdout_contains=(
      "Script: artifacts/e2e/s4/analysis.td",
      "TabDat:",
      "Python:",
      "Config: graph_format=png, artifact_dir=artifacts/e2e/s4/artifacts, graph_open=off",
      ". use artifacts/e2e/data/penguins.parquet",
      "Script: artifacts/e2e/s4/prep.td",
      ". summarize bill_length_mm flipper_length_mm body_mass_g",
      "Generated body_mass_kg:",
      "Saved plot: artifacts/e2e/s4/artifacts/plots/penguins_scatter.png",
      "species",
      "Row %",
      "Col %",
      "Created penguin_summary:",
      "Exported: artifacts/e2e/s4/penguin_summary.parquet",
    ),
    stdout_regex=(
      r"Exported: artifacts/e2e/s4/penguin_summary.parquet \([0-9]+ rows, 3 columns\)",
    ),
    expected_files=(
      Path("artifacts/e2e/s4/config.tabdat.toml"),
      Path("artifacts/e2e/s4/prep.td"),
      Path("artifacts/e2e/s4/analysis.td"),
      Path("artifacts/e2e/s4/artifacts/plots/penguins_scatter.png"),
      Path("artifacts/e2e/s4/penguin_summary.parquet"),
    ),
  )
  return run_command_scenario("s4_penguins_script_repro", command)


def s5_titanic_phase13_dogfood() -> ScenarioResult:
  command = CommandSpec(
    argv=(
      "uv",
      "run",
      "tabdat",
      "-c",
      "use artifacts/e2e/data/titanic.parquet",
      "-c",
      "regress fare age",
      "-c",
      "predict fare_hat",
      "-c",
      "predict fare_resid, residuals",
      "-c",
      "estat residuals",
      "-c",
      "estat ovtest",
      "-c",
      "estat vif",
      "-c",
      "head 5",
    ),
    stdout_contains=(
      "Loaded: artifacts/e2e/data/titanic.parquet",
      "Model: regress fare on age",
      "Estimator: ols",
      "Covariance: nonrobust",
      "Predicted fare_hat:",
      "Predicted fare_resid:",
      "Metric",
      "studentized_std_dev",
      "p_value",
      "Variable  VIF",
      "age",
      "fare_hat",
      "fare_resid",
    ),
    stdout_regex=(
      r"Observations: [0-9]+",
      r"Predicted fare_resid: [0-9]+ rows, [0-9]+ columns",
    ),
  )
  return run_command_scenario("s5_titanic_phase13_dogfood", command)


def s6_canonical_parquet_workflow() -> ScenarioResult:
  output_path = Path("artifacts/e2e/s6/canonical_summary.parquet")
  command = CommandSpec(
    argv=(
      "uv",
      "run",
      "tabdat",
      "-f",
      "demos/canonical_parquet_eda.td",
    ),
    stdout_contains=(
      "Script: demos/canonical_parquet_eda.td",
      "lazy=duckdb",
      "Rows:",
      "Nonmissing",
      "Missing",
      "Kept matching rows:",
      "Generated family_size:",
      "Count  Mean",
      "by class: summarize fare",
      "Collapsed dataset:",
      "Exported: artifacts/e2e/s6/canonical_summary.parquet",
    ),
    stdout_regex=(
      r"Collapsed dataset: 3 rows, 4 columns",
      r"Exported: artifacts/e2e/s6/canonical_summary\.parquet \(3 rows, 4 columns\)",
    ),
    expected_files=(output_path,),
  )

  result = ScenarioResult("s6_canonical_parquet_workflow", passed=True)
  first = run_command_scenario("s6_canonical_parquet_workflow_first", command)
  merge_result(result, first)
  first_snapshot = read_parquet_snapshot_or_failure(
    result,
    REPO_ROOT / output_path,
    "first replay output",
  )

  replay = run_command_scenario("s6_canonical_parquet_workflow_replay", command)
  merge_result(result, replay)
  replay_snapshot = read_parquet_snapshot_or_failure(
    result,
    REPO_ROOT / output_path,
    "second replay output",
  )

  check(result, first.stdout_path is not None, "first replay stdout was captured")
  check(result, replay.stdout_path is not None, "second replay stdout was captured")
  if first.stdout_path is not None and replay.stdout_path is not None:
    first_stdout = (REPO_ROOT / first.stdout_path).read_text(encoding="utf-8")
    replay_stdout = (REPO_ROOT / replay.stdout_path).read_text(encoding="utf-8")
    check(result, first_stdout == replay_stdout, "script replay stdout is identical")
    result.metrics["replay_stdout_match"] = first_stdout == replay_stdout
  check(
    result,
    first_snapshot != ((), ())
    and replay_snapshot != ((), ())
    and first_snapshot == replay_snapshot,
    "script replay output table is identical",
  )
  check(
    result,
    replay_snapshot[0] == ("class", "mean_age", "mean_fare", "mean_family_size"),
    "output schema is class-level means",
  )
  check(result, len(replay_snapshot[1]) == 3, "output has three class rows")
  check_file(result, output_path)

  first_seconds = first.duration_seconds or 0.0
  replay_seconds = replay.duration_seconds or 0.0
  result.duration_seconds = first_seconds + replay_seconds
  result.metrics.update(
    {
      "first_run_seconds": first_seconds,
      "replay_seconds": replay_seconds,
      "total_seconds": result.duration_seconds,
      "output_rows": len(replay_snapshot[1]),
      "output_columns": len(replay_snapshot[0]),
    }
  )
  return result


def run_command_scenario(scenario_id: str, command: CommandSpec) -> ScenarioResult:
  started_at = time.perf_counter()
  completed = subprocess.run(
    command.argv,
    cwd=REPO_ROOT,
    text=True,
    capture_output=True,
    check=False,
  )
  stdout_path = write_log(scenario_id, "stdout", completed.stdout)
  stderr_path = write_log(scenario_id, "stderr", completed.stderr)
  result = ScenarioResult(
    scenario_id=scenario_id,
    passed=True,
    stdout_path=str(stdout_path.relative_to(REPO_ROOT)),
    stderr_path=str(stderr_path.relative_to(REPO_ROOT)),
    exit_code=completed.returncode,
    duration_seconds=time.perf_counter() - started_at,
  )
  check(result, completed.returncode == 0, f"exit code {completed.returncode}")
  check(result, completed.stderr == command.expected_stderr, "stderr matches expectation")
  for expected in command.stdout_contains:
    check(result, expected in completed.stdout, f"stdout contains {expected!r}")
  for pattern in command.stdout_regex:
    check(result, re.search(pattern, completed.stdout) is not None, f"stdout matches {pattern!r}")
  for path in command.expected_files:
    check_file(result, path)
  return result


def write_log(scenario_id: str, stream: str, content: str) -> Path:
  path = REPORT_ROOT / f"{scenario_id}.{stream}.log"
  path.write_text(content, encoding="utf-8")
  return path


def check(result: ScenarioResult, condition: bool, message: str) -> None:
  if condition:
    result.checks.append(message)
    return
  result.passed = False
  result.failures.append(message)


def check_file(result: ScenarioResult, path: Path) -> None:
  absolute = REPO_ROOT / path
  check(result, absolute.exists(), f"file exists {path}")
  if not absolute.exists():
    return
  if absolute.suffix == ".svg":
    text = absolute.read_text(encoding="utf-8", errors="replace").lstrip()
    check(result, text.startswith("<svg"), f"svg starts with <svg {path}")
  elif absolute.suffix == ".png":
    check(result, absolute.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), f"png signature {path}")
  elif absolute.suffix == ".parquet":
    con = duckdb.connect()
    try:
      con.execute("select count(*) from read_parquet(?)", [str(absolute)]).fetchone()
      check(result, True, f"parquet readable {path}")
    except duckdb.Error as exc:
      check(result, False, f"parquet readable {path}: {exc}")
    finally:
      con.close()


def read_parquet_snapshot(path: Path) -> tuple[tuple[str, ...], tuple[tuple[object, ...], ...]]:
  con = duckdb.connect()
  try:
    cursor = con.execute("select * from read_parquet(?) order by all", [str(path)])
    columns = tuple(column[0] for column in cursor.description or ())
    return columns, tuple(cursor.fetchall())
  finally:
    con.close()


def read_parquet_snapshot_or_failure(
  result: ScenarioResult,
  path: Path,
  label: str,
) -> tuple[tuple[str, ...], tuple[tuple[object, ...], ...]]:
  if not path.exists():
    check(result, False, f"{label} exists at {path.relative_to(REPO_ROOT)}")
    return (), ()
  try:
    return read_parquet_snapshot(path)
  except duckdb.Error as exc:
    check(result, False, f"{label} is readable: {exc}")
    return (), ()


def merge_result(target: ScenarioResult, source: ScenarioResult) -> None:
  target.checks.extend(f"{source.scenario_id}: {check_message}" for check_message in source.checks)
  target.failures.extend(
    f"{source.scenario_id}: {failure_message}" for failure_message in source.failures
  )
  target.passed = target.passed and source.passed
  if target.stdout_path is None:
    target.stdout_path = source.stdout_path
  if target.stderr_path is None:
    target.stderr_path = source.stderr_path
  if target.exit_code is None:
    target.exit_code = source.exit_code
  if source.duration_seconds is not None:
    target.metrics[f"{source.scenario_id}.seconds"] = source.duration_seconds


class HarnessFailure(Exception):
  """Raised when the interactive harness observes unexpected behavior."""


@dataclass
class PtyChild:
  pid: int
  fd: int
  closed: bool = False


def spawn_pty(argv: tuple[str, ...], *, env: dict[str, str]) -> PtyChild:
  pid, fd = pty.fork()
  if pid == 0:
    os.chdir(REPO_ROOT)
    os.execvpe(argv[0], argv, env)
  os.set_blocking(fd, False)
  return PtyChild(pid=pid, fd=fd)


def send_and_expect(child: PtyChild, text: str, expected: str, *, timeout: float = 20) -> str:
  os.write(child.fd, text.encode())
  if not expected:
    return read_available(child, timeout=timeout)
  return expect_output(child, expected, timeout=timeout)


def expect_output(child: PtyChild, expected: str, *, timeout: float) -> str:
  deadline = time.monotonic() + timeout
  output = ""
  while time.monotonic() < deadline:
    output += read_available(child, timeout=0.2)
    if expected in output:
      return output
  raise HarnessFailure(f"timed out waiting for {expected!r}; observed tail: {output[-500:]!r}")


def read_available(child: PtyChild, *, timeout: float) -> str:
  chunks: list[bytes] = []
  deadline = time.monotonic() + timeout
  while time.monotonic() < deadline:
    readable, _, _ = select.select(
      [child.fd], [], [], min(0.1, max(0, deadline - time.monotonic()))
    )
    if not readable:
      continue
    try:
      chunk = os.read(child.fd, 4096)
    except BlockingIOError:
      continue
    except OSError:
      break
    if not chunk:
      break
    chunks.append(chunk)
  return b"".join(chunks).decode(errors="replace")


def close_pty(child: PtyChild) -> int:
  if child.closed:
    return 0
  child.closed = True
  try:
    os.close(child.fd)
  except OSError:
    pass
  deadline = time.monotonic() + 5
  while time.monotonic() < deadline:
    try:
      pid, status = os.waitpid(child.pid, os.WNOHANG)
    except ChildProcessError:
      return 0
    if pid:
      if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
      if os.WIFSIGNALED(status):
        return 128 + os.WTERMSIG(status)
      return status
    time.sleep(0.1)
  os.kill(child.pid, signal.SIGTERM)
  _, status = os.waitpid(child.pid, 0)
  if os.WIFEXITED(status):
    return os.WEXITSTATUS(status)
  if os.WIFSIGNALED(status):
    return 128 + os.WTERMSIG(status)
  return status


def write_text(path: Path, content: str) -> None:
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(content, encoding="utf-8")


def write_reports(results: Sequence[ScenarioResult]) -> None:
  serializable = [
    {
      "scenario_id": result.scenario_id,
      "passed": result.passed,
      "exit_code": result.exit_code,
      "stdout_path": result.stdout_path,
      "stderr_path": result.stderr_path,
      "duration_seconds": result.duration_seconds,
      "metrics": result.metrics,
      "checks": result.checks,
      "failures": result.failures,
    }
    for result in results
  ]
  (REPORT_ROOT / "results.json").write_text(
    json.dumps(serializable, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
  )
  summary_lines = ["# Integrated E2E Summary", ""]
  for result in results:
    status = "PASS" if result.passed else "FAIL"
    summary_lines.append(f"- {status}: `{result.scenario_id}`")
    if result.duration_seconds is not None:
      summary_lines.append(f"  - duration: {result.duration_seconds:.3f}s")
    for metric, value in sorted(result.metrics.items()):
      if metric.endswith(".seconds"):
        continue
      summary_lines.append(f"  - {metric}: {value}")
    for failure in result.failures:
      summary_lines.append(f"  - {failure}")
  summary_lines.append("")
  summary_lines.append(f"Overall: {'PASS' if all(result.passed for result in results) else 'FAIL'}")
  (REPORT_ROOT / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
  print("\n".join(summary_lines))


SCENARIO_DATASETS = {
  "s1_titanic_batch_core": ("titanic",),
  "s2_interactive_shell_contract": ("titanic",),
  "s3_taxi_lazy_scale": ("nyc_taxi_jan_2023",),
  "s4_penguins_script_repro": ("penguins",),
  "s5_titanic_phase13_dogfood": ("titanic",),
  "s6_canonical_parquet_workflow": ("titanic",),
}

SCENARIOS = {
  "s1_titanic_batch_core": s1_titanic_batch_core,
  "s2_interactive_shell_contract": s2_interactive_shell_contract,
  "s3_taxi_lazy_scale": s3_taxi_lazy_scale,
  "s4_penguins_script_repro": s4_penguins_script_repro,
  "s5_titanic_phase13_dogfood": s5_titanic_phase13_dogfood,
  "s6_canonical_parquet_workflow": s6_canonical_parquet_workflow,
}


if __name__ == "__main__":
  raise SystemExit(main())
