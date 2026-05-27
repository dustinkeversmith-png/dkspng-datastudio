"""Regression model exports."""

from backend.modules.analysis.models.regression.linear_regression_model import LinearRegressionModel, RegressionResult
from backend.modules.analysis.models.regression.logistic_regression_model import LogisticRegressionModel

__all__ = ["LinearRegressionModel", "LogisticRegressionModel", "RegressionResult"]
