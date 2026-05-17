"""Simple ML models with sklearn optional fallback."""
from __future__ import annotations

from typing import Any

import numpy as np

try:
    from sklearn.dummy import DummyClassifier
    from sklearn.ensemble import (
        HistGradientBoostingClassifier,
        RandomForestClassifier,
    )
    from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class FallbackDummyModel:
    """Trivial model when sklearn is not installed."""

    def __init__(self) -> None:
        self.majority_class: Any = 0

    def fit(self, x: np.ndarray, y: np.ndarray) -> FallbackDummyModel:
        unique, counts = np.unique(y[~np.isnan(y)], return_counts=True)
        self.majority_class = unique[np.argmax(counts)] if len(unique) else 0
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        return np.full(len(x), self.majority_class)

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        n = len(x)
        return np.column_stack([np.full(n, 0.5), np.full(n, 0.5)])


MODEL_REGISTRY: dict[str, dict] = {}

if SKLEARN_AVAILABLE:
    MODEL_REGISTRY = {
        "logistic_regression": {
            "class": LogisticRegression,
            "params": {"max_iter": 1000, "solver": "lbfgs", "random_state": 42},
            "type": "classification",
            "supports_proba": True,
        },
        "random_forest": {
            "class": RandomForestClassifier,
            "params": {"n_estimators": 100, "max_depth": 6, "random_state": 42, "n_jobs": -1},
            "type": "classification",
            "supports_proba": True,
        },
        "hist_gradient_boosting": {
            "class": HistGradientBoostingClassifier,
            "params": {"max_iter": 200, "max_depth": 4, "random_state": 42},
            "type": "classification",
            "supports_proba": True,
        },
        "dummy_stratified": {
            "class": DummyClassifier,
            "params": {"strategy": "stratified", "random_state": 42},
            "type": "classification",
            "supports_proba": True,
        },
        "dummy_most_frequent": {
            "class": DummyClassifier,
            "params": {"strategy": "most_frequent"},
            "type": "classification",
            "supports_proba": True,
        },
        "ridge_regression": {
            "class": Ridge,
            "params": {"alpha": 1.0},
            "type": "regression",
            "supports_proba": False,
        },
        "linear_regression": {
            "class": LinearRegression,
            "params": {},
            "type": "regression",
            "supports_proba": False,
        },
    }
else:
    MODEL_REGISTRY = {
        "fallback_dummy": {
            "class": FallbackDummyModel,
            "params": {},
            "type": "classification",
            "supports_proba": True,
        },
    }


def create_model(name: str) -> Any:
    """Instantiate a model by registry name."""
    if name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model: {name}. Known: {sorted(MODEL_REGISTRY)}")
    entry = MODEL_REGISTRY[name]
    return entry["class"](**entry["params"])


def available_models(model_type: str = "classification") -> list[str]:
    """List model names of a given type."""
    return [name for name, entry in MODEL_REGISTRY.items() if entry["type"] == model_type]
