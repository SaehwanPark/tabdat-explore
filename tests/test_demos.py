from pathlib import Path
from tabdat.cli import main

def test_heckman_mroz_demo(capsys) -> None:
  demo_path = Path("demos/heckman_mroz.td")
  assert demo_path.exists(), "Heckman demo script must exist"

  exit_code = main(["-f", str(demo_path)])
  assert exit_code == 0, "Heckman demo script must run successfully"

  captured = capsys.readouterr()
  assert "Loaded: https://www.stata.com/data/jwooldridge/eacsap/mroz.dta" in captured.out
  assert "Model: heckman" in captured.out
  assert "mills_lambda" in captured.out
  assert "educ" in captured.out
  assert "exper" in captured.out
  assert "Predicted wage_hat:" in captured.out
  assert "Predicted selection_resid:" in captured.out
  assert "wage_hat" in captured.out
  assert "selection_resid" in captured.out


def test_ivregress_card_demo(capsys) -> None:
  demo_path = Path("demos/ivregress_card.td")
  assert demo_path.exists(), "IV regress demo script must exist"

  exit_code = main(["-f", str(demo_path)])
  assert exit_code == 0, "IV regress demo script must run successfully"

  captured = capsys.readouterr()
  assert "Loaded: https://www.stata.com/data/jwooldridge/eacsap/card.dta" in captured.out
  assert "Model: regress lwage" in captured.out
  assert "Model: ivregress 2sls" in captured.out
  assert "estat firststage" in captured.out
  assert "partial_f" in captured.out
  assert "estat endogenous" in captured.out
  assert "wu_hausman" in captured.out


def test_panel_union_demo(capsys) -> None:
  demo_path = Path("demos/panel_union.td")
  assert demo_path.exists(), "Panel union demo script must exist"

  exit_code = main(["-f", str(demo_path)])
  assert exit_code == 0, "Panel union demo script must run successfully"

  captured = capsys.readouterr()
  assert "Loaded: https://www.stata-press.com/data/r14/union.dta" in captured.out
  assert "Panel set: id=idcode" in captured.out
  assert "Model: xtreg fe union" in captured.out
  assert "Model: xtreg re union" in captured.out
  assert "estat hausman" in captured.out
  assert "chi2" in captured.out
