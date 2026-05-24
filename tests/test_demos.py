from pathlib import Path
import numpy as np
import pandas as pd
from tabdat.cli import main

def test_heckman_mroz_demo(tmp_path: Path, capsys) -> None:
  demo_path = Path("demos/heckman_mroz.td")
  assert demo_path.exists(), "Heckman demo script must exist"

  # Create a mock Stata dataset locally with the required columns
  np.random.seed(42)
  n = 100
  df = pd.DataFrame({
    "inlf": np.random.randint(0, 2, n),
    "hours": np.random.randint(0, 2000, n),
    "kidslt6": np.random.randint(0, 3, n),
    "kidsge6": np.random.randint(0, 4, n),
    "age": np.random.randint(30, 60, n),
    "educ": np.random.randint(8, 18, n),
    "wage": np.random.uniform(0.5, 30.0, n),
    "repwage": np.random.uniform(0.5, 30.0, n),
    "hushrs": np.random.randint(1000, 3000, n),
    "husage": np.random.randint(30, 65, n),
    "huseduc": np.random.randint(8, 18, n),
    "huswage": np.random.uniform(5, 40, n),
    "faminc": np.random.uniform(10, 100, n),
    "mtr": np.random.uniform(0.1, 0.5, n),
    "motheduc": np.random.randint(6, 18, n),
    "fatheduc": np.random.randint(6, 18, n),
    "unem": np.random.uniform(2, 10, n),
    "city": np.random.randint(0, 2, n),
    "exper": np.random.randint(1, 30, n),
    "nwifeinc": np.random.uniform(5, 80, n),
    "lwage": np.random.uniform(0.5, 3.5, n),
  })
  df["expersq"] = df["exper"] ** 2
  # Enforce selection rules: non-participants have wage = 0 and NaN log wage
  df.loc[df["inlf"] == 0, "wage"] = 0.0
  df.loc[df["inlf"] == 0, "lwage"] = np.nan

  local_dta = tmp_path / "mroz.dta"
  df.to_stata(local_dta, write_index=False)

  # Read original script and replace remote URL with local path
  script_content = demo_path.read_text(encoding="utf-8")
  modified_content = script_content.replace(
    "https://www.stata.com/data/jwooldridge/eacsap/mroz.dta",
    str(local_dta)
  )

  # Write modified script to a temp file
  temp_script = tmp_path / "heckman_mroz_local.td"
  temp_script.write_text(modified_content, encoding="utf-8")

  # Run script via CLI main
  exit_code = main(["-f", str(temp_script)])
  assert exit_code == 0, "Heckman demo script must run successfully"

  captured = capsys.readouterr()
  assert f"Loaded: {local_dta}" in captured.out
  assert "Model: heckman" in captured.out
  assert "mills_lambda" in captured.out
  assert "educ" in captured.out
  assert "exper" in captured.out
  assert "Predicted wage_hat:" in captured.out
  assert "Predicted selection_resid:" in captured.out
  assert "wage_hat" in captured.out
  assert "selection_resid" in captured.out


def test_ivregress_card_demo(tmp_path: Path, capsys) -> None:
  demo_path = Path("demos/ivregress_card.td")
  assert demo_path.exists(), "IV regress demo script must exist"

  # Create a mock Card Stata dataset locally with required columns
  np.random.seed(42)
  n = 120
  df = pd.DataFrame({
    "lwage": np.random.uniform(4.5, 7.5, n),
    "educ": np.random.randint(8, 18, n),
    "exper": np.random.randint(1, 20, n),
    "black": np.random.randint(0, 2, n),
    "south": np.random.randint(0, 2, n),
    "smsa": np.random.randint(0, 2, n),
    "nearc4": np.random.randint(0, 2, n),
  })
  df["expersq"] = df["exper"] ** 2
  local_dta = tmp_path / "card.dta"
  df.to_stata(local_dta, write_index=False)

  # Read original script and replace remote URL with local path
  script_content = demo_path.read_text(encoding="utf-8")
  modified_content = script_content.replace(
    "https://www.stata.com/data/jwooldridge/eacsap/card.dta",
    str(local_dta)
  )

  # Write modified script to a temp file
  temp_script = tmp_path / "ivregress_card_local.td"
  temp_script.write_text(modified_content, encoding="utf-8")

  # Run script via CLI main
  exit_code = main(["-f", str(temp_script)])
  assert exit_code == 0, "IV regress demo script must run successfully"

  captured = capsys.readouterr()
  assert f"Loaded: {local_dta}" in captured.out
  assert "Model: regress lwage" in captured.out
  assert "Model: ivregress 2sls" in captured.out
  assert "estat firststage" in captured.out
  assert "partial_f" in captured.out
  assert "estat endogenous" in captured.out
  assert "wu_hausman" in captured.out


def test_panel_union_demo(tmp_path: Path, capsys) -> None:
  demo_path = Path("demos/panel_union.td")
  assert demo_path.exists(), "Panel union demo script must exist"

  # Create a mock Union Stata dataset locally with required columns
  np.random.seed(42)
  entities = 80
  years = 3
  rows = []
  for i in range(1, entities + 1):
    for y in range(70, 70 + years):
      # Ensure there is time variation in South, Grade, and Union within entity
      south = np.random.randint(0, 2)
      union = np.random.randint(0, 2)
      age = 20 + (y - 70)
      grade = 10 + (y - 70) + np.random.randint(0, 2)
      rows.append({
        "idcode": i,
        "year": y,
        "union": union,
        "age": age,
        "grade": grade,
        "south": south
      })
  df = pd.DataFrame(rows)
  local_dta = tmp_path / "union.dta"
  df.to_stata(local_dta, write_index=False)

  # Read original script and replace remote URL with local path
  script_content = demo_path.read_text(encoding="utf-8")
  modified_content = script_content.replace(
    "https://www.stata-press.com/data/r14/union.dta",
    str(local_dta)
  )

  # Write modified script to a temp file
  temp_script = tmp_path / "panel_union_local.td"
  temp_script.write_text(modified_content, encoding="utf-8")

  # Run script via CLI main
  exit_code = main(["-f", str(temp_script)])
  assert exit_code == 0, "Panel union demo script must run successfully"

  captured = capsys.readouterr()
  assert f"Loaded: {local_dta}" in captured.out
  assert "Panel set: id=idcode" in captured.out
  assert "Model: xtreg fe union" in captured.out
  assert "Model: xtreg re union" in captured.out
  assert "estat hausman" in captured.out
  assert "chi2" in captured.out
