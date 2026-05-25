"""Models package — registers all model types on import."""

from app.models.model_result import ModelResult, PredictionResult, ModelEvaluation  # noqa
from app.models.base_model import BaseModel, get_model, list_models  # noqa

# Trigger registration side-effects
import app.models.regression.linear_regression_model  # noqa
import app.models.regression.logistic_regression_model  # noqa
import app.models.classification.svm_model  # noqa
import app.models.classification.naive_bayes_model  # noqa
import app.models.classification.decision_tree_model  # noqa
import app.models.decomposition.pca_model  # noqa
import app.models.time_series.arima_model  # noqa
import app.models.signal.fourier_model  # noqa

__all__ = [
    "BaseModel",
    "ModelResult",
    "PredictionResult",
    "ModelEvaluation",
    "get_model",
    "list_models",
]
