"""Models package: import once to register every analysis model."""

from backend.modules.analysis.models.model_result import ModelEvaluation, ModelResult, PredictionResult  # noqa
from backend.modules.analysis.models.base_model import BaseModel, get_model, list_models  # noqa
from backend.modules.analysis.models.clustering.clustering_model import ClusterModel, ClusterResult  # noqa
from backend.modules.analysis.models.regression.linear_regression_model import RegressionResult  # noqa
from backend.modules.analysis.models.sampling.sampling_model import SamplingModel, SamplingResult  # noqa
from backend.modules.analysis.models.clustering.spatial_temporal_model import (  # noqa
    KNNResult,
    NeighborModel,
    NeighborResult,
    SpatialTemporalKey,
    haversine_km,
    haversine_mi,
    infer_stkey,
)

# Trigger registration side effects for concrete model families.
import backend.modules.analysis.models.regression.linear_regression_model  # noqa
import backend.modules.analysis.models.regression.logistic_regression_model  # noqa
import backend.modules.analysis.models.classification.svm_model  # noqa
import backend.modules.analysis.models.classification.naive_bayes_model  # noqa
import backend.modules.analysis.models.classification.decision_tree_model  # noqa
import backend.modules.analysis.models.decomposition.pca_model  # noqa
import backend.modules.analysis.models.time_series.arima_model  # noqa
import backend.modules.analysis.models.signal.fourier_model  # noqa

__all__ = [
    "BaseModel",
    "ModelResult",
    "PredictionResult",
    "ModelEvaluation",
    "ClusterModel",
    "ClusterResult",
    "RegressionResult",
    "KNNResult",
    "NeighborModel",
    "NeighborResult",
    "SamplingModel",
    "SamplingResult",
    "SpatialTemporalKey",
    "haversine_km",
    "haversine_mi",
    "infer_stkey",
    "get_model",
    "list_models",
]
