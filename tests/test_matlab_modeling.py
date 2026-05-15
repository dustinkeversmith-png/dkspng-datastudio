from pathlib import Path

from app.matlab_modeling import MATLAB_RUNNER


def test_matlab_runner_path_is_expected():
    assert str(MATLAB_RUNNER).endswith("services/matlab-modeling/matlab_model_runner.py")


def test_matlab_runner_file_exists():
    assert Path(MATLAB_RUNNER).exists()
