from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from galapagos.ml.schemas import RANDOM_SEED, TARGET_CLASSES


@dataclass(frozen=True)
class OfflineModelResult:
    model_name: str
    predicted_class: pd.Series
    probabilities: pd.DataFrame


def fit_predict_model(
    model_name: str,
    train_features: pd.DataFrame,
    train_target: pd.Series,
    predict_features: pd.DataFrame,
) -> OfflineModelResult:
    if model_name == "majority_class_baseline":
        return _majority_class(train_target, predict_features.index)
    if model_name == "random_seeded_baseline":
        return _random_seeded(train_target, predict_features.index)
    if model_name == "logistic_regression":
        estimator = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(max_iter=500, random_state=RANDOM_SEED)),
            ]
        )
        estimator.fit(train_features, train_target)
        return _sklearn_result(model_name, estimator, predict_features)
    if model_name == "decision_tree_depth_2":
        estimator = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("model", DecisionTreeClassifier(max_depth=2, random_state=RANDOM_SEED)),
            ]
        )
        estimator.fit(train_features, train_target)
        return _sklearn_result(model_name, estimator, predict_features)
    raise ValueError(f"unsupported V2.8 model: {model_name}")


def _majority_class(train_target: pd.Series, index: pd.Index) -> OfflineModelResult:
    majority = str(train_target.value_counts().sort_values(ascending=False).index[0])
    probabilities = pd.DataFrame(0.0, index=index, columns=TARGET_CLASSES)
    probabilities.loc[:, majority] = 1.0
    predicted = pd.Series(majority, index=index, name="research_predicted_class")
    return OfflineModelResult("majority_class_baseline", predicted, probabilities)


def _random_seeded(train_target: pd.Series, index: pd.Index) -> OfflineModelResult:
    distribution = train_target.value_counts(normalize=True).reindex(TARGET_CLASSES, fill_value=0.0)
    rng = np.random.default_rng(RANDOM_SEED)
    draws = rng.choice(TARGET_CLASSES, size=len(index), p=distribution.to_numpy(dtype=float))
    probabilities = pd.DataFrame(
        np.tile(distribution.to_numpy(dtype=float), (len(index), 1)),
        index=index,
        columns=TARGET_CLASSES,
    )
    predicted = pd.Series(draws, index=index, name="research_predicted_class")
    return OfflineModelResult("random_seeded_baseline", predicted, probabilities)


def _sklearn_result(model_name: str, estimator: Pipeline, predict_features: pd.DataFrame) -> OfflineModelResult:
    predicted = pd.Series(estimator.predict(predict_features), index=predict_features.index, name="research_predicted_class")
    raw_probabilities = estimator.predict_proba(predict_features)
    classes = [str(value) for value in estimator.classes_]
    probabilities = pd.DataFrame(0.0, index=predict_features.index, columns=TARGET_CLASSES)
    for column_index, class_name in enumerate(classes):
        probabilities.loc[:, class_name] = raw_probabilities[:, column_index]
    return OfflineModelResult(model_name, predicted.astype(str), probabilities)
