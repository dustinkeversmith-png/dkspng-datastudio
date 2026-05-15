from pathlib import Path

from app.analysis import R_RUNNER


def test_r_runner_path_is_expected():
    assert str(R_RUNNER).endswith("services/r-analysis/analysis_runner.R")


def test_r_runner_file_exists():
    assert Path(R_RUNNER).exists()
