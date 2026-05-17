"""Walk-forward evaluation for payoff-aware objective candidates."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression, Ridge

from .baseline_comparator import compare_against_baselines
from .objective_schema import AnalysisSplit, ObjectiveCandidateSpec
from .sample_weighting import build_asymmetric_sample_weights, build_downside_sample_weights


def evaluate_objective_candidates(
    frame: pd.DataFrame,
    candidates: list[ObjectiveCandidateSpec],
    splits: list[AnalysisSplit],
    *,
    iterations: int = 200,
    seed: int = 40,
) -> dict[str, Any]:
    """Evaluate payoff-aware objective candidates in a causal walk-forward protocol."""
    split_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    baseline_rows: list[dict[str, Any]] = []
    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame.sort_values("timestamp").reset_index(drop=True)

    for candidate_index, spec in enumerate(candidates):
        per_split: list[dict[str, Any]] = []
        for split_index, split in enumerate(splits):
            train = _slice_frame(frame, split.train_start, split.train_end)
            test = _slice_frame(frame, split.test_start, split.test_end)
            metrics = _evaluate_candidate_split(
                spec,
                train=train,
                test=test,
                iterations=iterations,
                seed=seed + candidate_index * 97 + split_index,
            )
            metrics.update(
                {
                    "candidate_name": spec.name,
                    "candidate_type": spec.candidate_type,
                    "description": spec.description,
                    "uses_ev_proxy": spec.uses_ev_proxy,
                    "uses_probability": spec.uses_probability,
                    "uses_downside_weighting": spec.uses_downside_weighting,
                    "target_column": spec.target_column,
                    "feature_columns": list(spec.feature_columns),
                    "split_name": split.name,
                    "train_start": split.train_start.isoformat(),
                    "train_end": split.train_end.isoformat(),
                    "test_start": split.test_start.isoformat(),
                    "test_end": split.test_end.isoformat(),
                }
            )
            split_rows.append(metrics)
            per_split.append(metrics)
        candidate_rows.append(_aggregate_candidate_rows(spec, per_split))
        baseline_rows.extend(compare_against_baselines(per_split))

    temporal = _temporal_summary(split_rows)
    regime = _regime_summary(frame, candidate_rows)
    overfit = {
        "candidates_tested_count": len(candidates),
        "targets_tested_count": len({spec.target_column for spec in candidates}),
        "metric_count": len(split_rows) * 6,
        "multiple_testing_risk": _multiple_testing_risk(len(candidates), len(split_rows)),
        "evidence_classification": "EXPLORATORY_ONLY",
        "preregistration_allowed": False,
        "paper_live_allowed": False,
        "no_strategy_validated": True,
    }
    return {
        "split_rows": split_rows,
        "candidate_rows": candidate_rows,
        "baseline_rows": baseline_rows,
        "temporal_summary": temporal,
        "regime_summary": regime,
        "overfit_guard": overfit,
        "evaluation_status": "PAYOFF_OBJECTIVE_WALK_FORWARD_EVAL_COMPLETE" if split_rows else "PAYOFF_OBJECTIVE_WALK_FORWARD_EVAL_FAILED",
    }


def evaluate_score_baseline(
    frame: pd.DataFrame,
    *,
    score_column: str,
    splits: list[AnalysisSplit],
    name: str,
    iterations: int = 200,
    seed: int = 40,
) -> dict[str, Any]:
    """Evaluate a non-trainable baseline score using the same walk-forward protocol."""
    rows: list[dict[str, Any]] = []
    for split_index, split in enumerate(splits):
        train = _slice_frame(frame, split.train_start, split.train_end)
        test = _slice_frame(frame, split.test_start, split.test_end)
        if train.empty or test.empty:
            rows.append(
                {
                    "candidate_name": name,
                    "split_name": split.name,
                    "selected_count": 0,
                    "selection_ratio": 0.0,
                    "spearman_corr": 0.0,
                    "mean_realized_return_top_decile": 0.0,
                    "median_realized_return_top_decile": 0.0,
                    "downside_loss_rate_top_decile": 0.0,
                    "payoff_ratio_top_decile": 0.0,
                    "ev_realization_gap": 0.0,
                    "best_score_mean": 0.0,
                    "random_monthly_count_preserving_mean": 0.0,
                    "random_monthly_count_preserving_p95": 0.0,
                    "beats_random_baseline": False,
                    "beats_random_p95": False,
                    "enough_sample_size": False,
                    "sample_warning": "SAMPLE_TOO_SMALL",
                    "raw_score_mean": 0.0,
                    "raw_score_std": 0.0,
                }
            )
            continue
        if score_column not in train.columns or score_column not in test.columns:
            continue
        raw_train = pd.to_numeric(train[score_column], errors="coerce").fillna(0.0).to_numpy()
        raw_test = pd.to_numeric(test[score_column], errors="coerce").fillna(0.0).to_numpy()
        calibration_target = pd.to_numeric(train["net_return_label"], errors="coerce").fillna(0.0)
        calibrated_test_score = _calibrate_score(raw_train, calibration_target, raw_test)
        test_target = pd.to_numeric(test["net_return_label"], errors="coerce").fillna(0.0)
        top_k = max(1, int(round(len(test) * 0.1)))
        selected = test.assign(calibrated_score=calibrated_test_score).nlargest(top_k, "calibrated_score")
        baseline = _monthly_random_baseline(
            test.assign(net_return_label=test_target),
            selected_count=len(selected),
            iterations=iterations,
            seed=seed + split_index,
        )
        selected_returns = test_target.loc[selected.index]
        selected_scores = pd.Series(calibrated_test_score, index=test.index).loc[selected.index]
        test_len = len(test)
        rows.append(
            {
                "candidate_name": name,
                "split_name": split.name,
                "selected_count": int(len(selected)),
                "selection_ratio": float(len(selected) / test_len) if test_len else 0.0,
                "spearman_corr": _safe_spearman(calibrated_test_score, test_target),
                "mean_realized_return_top_decile": float(selected_returns.mean()) if len(selected_returns) else 0.0,
                "median_realized_return_top_decile": float(selected_returns.median()) if len(selected_returns) else 0.0,
                "downside_loss_rate_top_decile": float((selected_returns < 0).mean()) if len(selected_returns) else 0.0,
                "payoff_ratio_top_decile": _payoff_ratio(selected_returns),
                    "ev_realization_gap": float(selected_scores.mean() - selected_returns.mean()) if len(selected_returns) else 0.0,
                    "best_score_mean": float(selected_scores.mean()) if len(selected_returns) else 0.0,
                "random_monthly_count_preserving_mean": float(baseline["random_mean"]),
                "random_monthly_count_preserving_p95": float(baseline["random_p95"]),
                "beats_random_baseline": bool(selected_returns.mean() > baseline["random_mean"]) if len(selected_returns) else False,
                "beats_random_p95": bool(selected_returns.mean() > baseline["random_p95"]) if len(selected_returns) else False,
                "enough_sample_size": len(selected) >= 30,
                "sample_warning": "SAMPLE_TOO_SMALL" if len(selected) < 30 else None,
                "raw_score_mean": float(pd.Series(raw_test).mean()) if len(raw_test) else 0.0,
                "raw_score_std": float(pd.Series(raw_test).std()) if len(raw_test) else 0.0,
            }
        )
    return {
        "name": name,
        "score_column": score_column,
        "rows": rows,
        "summary": _aggregate_candidate_rows(
            ObjectiveCandidateSpec(
                name=name,
                description=f"Baseline score: {score_column}",
                target_column="net_return_label",
                feature_columns=(score_column,),
                candidate_type="baseline",
            ),
            rows,
        ),
        "status": "PAYOFF_OBJECTIVE_WALK_FORWARD_EVAL_COMPLETE" if rows else "PAYOFF_OBJECTIVE_WALK_FORWARD_EVAL_FAILED",
    }


def _slice_frame(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    mask = (frame["timestamp"] >= start) & (frame["timestamp"] < end)
    return frame.loc[mask].copy()


def _evaluate_candidate_split(
    spec: ObjectiveCandidateSpec,
    *,
    train: pd.DataFrame,
    test: pd.DataFrame,
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    if train.empty or test.empty:
        return {
            "selected_count": 0,
            "selection_ratio": 0.0,
            "spearman_corr": 0.0,
            "mean_realized_return_top_decile": 0.0,
            "median_realized_return_top_decile": 0.0,
            "downside_loss_rate_top_decile": 0.0,
            "payoff_ratio_top_decile": 0.0,
            "ev_realization_gap": 0.0,
            "best_score_mean": 0.0,
            "random_monthly_count_preserving_mean": 0.0,
            "random_monthly_count_preserving_p95": 0.0,
            "beats_random_baseline": False,
            "beats_random_p95": False,
            "enough_sample_size": False,
            "sample_warning": "SAMPLE_TOO_SMALL",
            "raw_score_mean": 0.0,
            "raw_score_std": 0.0,
        }
    train_scores, test_scores, score_info = _fit_and_score_candidate(spec, train=train, test=test)
    calibration_target = pd.to_numeric(train["net_return_label"], errors="coerce").fillna(0.0)
    test_target = pd.to_numeric(test["net_return_label"], errors="coerce").fillna(0.0)
    calibrated_test_score = _calibrate_score(train_scores, calibration_target, test_scores)
    calibrated_train_score = _calibrate_score(train_scores, calibration_target, train_scores)
    top_k = max(1, int(round(len(test) * 0.1)))
    selected = test.assign(calibrated_score=calibrated_test_score).nlargest(top_k, "calibrated_score")
    selected_mask = test.index.isin(selected.index)
    selected_returns = test_target.loc[selected.index]
    selected_scores = pd.Series(calibrated_test_score, index=test.index).loc[selected.index]
    baseline = _monthly_random_baseline(
        test.assign(net_return_label=test_target),
        selected_count=len(selected),
        iterations=iterations,
        seed=seed,
    )
    spearman = _safe_spearman(calibrated_test_score, test_target)
    top_returns = selected_returns
    return {
        "selected_count": int(len(selected)),
        "selection_ratio": float(len(selected) / len(test)),
        "spearman_corr": float(spearman),
        "mean_realized_return_top_decile": float(top_returns.mean()) if len(top_returns) else 0.0,
        "median_realized_return_top_decile": float(top_returns.median()) if len(top_returns) else 0.0,
        "downside_loss_rate_top_decile": float((top_returns < 0).mean()) if len(top_returns) else 0.0,
        "payoff_ratio_top_decile": _payoff_ratio(top_returns),
        "ev_realization_gap": float(selected_scores.mean() - selected_returns.mean()) if len(selected) else 0.0,
        "best_score_mean": float(selected_scores.mean()) if len(selected) else 0.0,
        "random_monthly_count_preserving_mean": float(baseline["random_mean"]),
        "random_monthly_count_preserving_p95": float(baseline["random_p95"]),
        "beats_random_baseline": bool(top_returns.mean() > baseline["random_mean"]) if len(top_returns) else False,
        "beats_random_p95": bool(top_returns.mean() > baseline["random_p95"]) if len(top_returns) else False,
        "enough_sample_size": len(selected) >= 30,
        "sample_warning": "SAMPLE_TOO_SMALL" if len(selected) < 30 else None,
        "raw_score_mean": float(pd.Series(test_scores).mean()) if len(test_scores) else 0.0,
        "raw_score_std": float(pd.Series(test_scores).std()) if len(test_scores) else 0.0,
        "calibrated_train_score_mean": float(pd.Series(calibrated_train_score).mean()) if len(calibrated_train_score) else 0.0,
        "score_fit_status": score_info["score_fit_status"],
    }


def _fit_and_score_candidate(
    spec: ObjectiveCandidateSpec,
    *,
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    if spec.name == "probability_only_baseline":
        raw_train = pd.to_numeric(
            train.get("predicted_probability_calibrated", train.get("predicted_probability")),
            errors="coerce",
        ).fillna(0.5)
        raw_test = pd.to_numeric(
            test.get("predicted_probability_calibrated", test.get("predicted_probability")),
            errors="coerce",
        ).fillna(0.5)
        return raw_train.to_numpy(), raw_test.to_numpy(), {"score_fit_status": "BASELINE_PROBABILITY_ONLY"}

    feature_columns = [column for column in spec.feature_columns if column in train.columns and column in test.columns]
    if not feature_columns:
        raw_train = np.zeros(len(train), dtype=float)
        raw_test = np.zeros(len(test), dtype=float)
        return raw_train, raw_test, {"score_fit_status": "NO_FEATURES_AVAILABLE"}
    train_matrix, test_matrix = _build_design_matrices(train, test, feature_columns)
    target = pd.to_numeric(train[spec.target_column], errors="coerce").fillna(0.0)
    if spec.candidate_type == "classifier":
        weights = build_asymmetric_sample_weights(train["net_return_label"]) if spec.uses_downside_weighting else None
        model = LogisticRegression(max_iter=1000, solver="lbfgs")
        model.fit(train_matrix, (train[spec.target_column].astype(float) > 0).astype(int), sample_weight=weights)
        raw_train = model.predict_proba(train_matrix)[:, 1]
        raw_test = model.predict_proba(test_matrix)[:, 1]
        return raw_train, raw_test, {"score_fit_status": "LOGISTIC_CLASSIFIER"}
    if spec.candidate_type == "downside_regression":
        weights = build_downside_sample_weights(train["downside_risk_label"]) if spec.uses_downside_weighting else None
        model = Ridge(alpha=1.0)
        model.fit(train_matrix, target, sample_weight=weights)
        raw_train = -model.predict(train_matrix)
        raw_test = -model.predict(test_matrix)
        return raw_train, raw_test, {"score_fit_status": "RIDGE_DOWNSIDE_REGRESSION"}
    if spec.candidate_type == "ev_gap_residual":
        model = Ridge(alpha=1.0)
        model.fit(train_matrix, target)
        residual_train = model.predict(train_matrix)
        residual_test = model.predict(test_matrix)
        base_train = pd.to_numeric(train["ev_calibrated_proxy"], errors="coerce").fillna(0.0).to_numpy()
        base_test = pd.to_numeric(test["ev_calibrated_proxy"], errors="coerce").fillna(0.0).to_numpy()
        return base_train + residual_train, base_test + residual_test, {"score_fit_status": "RIDGE_EV_RESIDUAL"}
    if spec.candidate_type == "two_head":
        prob_model = LogisticRegression(max_iter=1000, solver="lbfgs")
        prob_model.fit(train_matrix, (train["signed_payoff_label"].astype(float) > 0).astype(int))
        reg_model = Ridge(alpha=1.0)
        reg_model.fit(train_matrix, pd.to_numeric(train["net_return_label"], errors="coerce").fillna(0.0))
        prob_train = prob_model.predict_proba(train_matrix)[:, 1]
        prob_test = prob_model.predict_proba(test_matrix)[:, 1]
        reg_train = reg_model.predict(train_matrix)
        reg_test = reg_model.predict(test_matrix)
        reg_train_z = _zscore(reg_train)
        reg_test_z = _zscore_with_train(reg_train, reg_test)
        raw_train = 0.6 * prob_train + 0.4 * reg_train_z
        raw_test = 0.6 * prob_test + 0.4 * reg_test_z
        return raw_train, raw_test, {"score_fit_status": "TWO_HEAD_COMBINED"}
    model = Ridge(alpha=1.0)
    model.fit(train_matrix, target)
    raw_train = model.predict(train_matrix)
    raw_test = model.predict(test_matrix)
    return raw_train, raw_test, {"score_fit_status": "RIDGE_REGRESSION"}


def _build_design_matrices(train: pd.DataFrame, test: pd.DataFrame, feature_columns: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    train_df = train[feature_columns].copy()
    test_df = test[feature_columns].copy()
    categorical_columns = [column for column in feature_columns if train_df[column].dtype == "object" or str(train_df[column].dtype).startswith("category")]
    numeric_columns = [column for column in feature_columns if column not in categorical_columns]
    for column in numeric_columns:
        train_df[column] = pd.to_numeric(train_df[column], errors="coerce")
        test_df[column] = pd.to_numeric(test_df[column], errors="coerce")
        median = train_df[column].median()
        if pd.isna(median):
            median = 0.0
        train_df[column] = train_df[column].fillna(median)
        test_df[column] = test_df[column].fillna(median)
    train_matrix = pd.get_dummies(train_df, columns=categorical_columns, dummy_na=True)
    test_matrix = pd.get_dummies(test_df, columns=categorical_columns, dummy_na=True)
    test_matrix = test_matrix.reindex(columns=train_matrix.columns, fill_value=0.0)
    return train_matrix.astype(float), test_matrix.astype(float)


def _calibrate_score(train_score: np.ndarray, train_target: pd.Series, test_score: np.ndarray) -> np.ndarray:
    if len(train_score) == 0 or len(test_score) == 0:
        return np.asarray(test_score, dtype=float)
    x = np.asarray(train_score, dtype=float)
    y = pd.to_numeric(train_target, errors="coerce").fillna(0.0).to_numpy(dtype=float)
    if np.allclose(np.nanstd(x), 0.0):
        return np.full_like(np.asarray(test_score, dtype=float), float(np.nanmean(y)))
    try:
        slope, intercept = np.polyfit(x, y, 1)
    except Exception:
        slope, intercept = 1.0, float(np.nanmean(y))
    calibrated = slope * np.asarray(test_score, dtype=float) + intercept
    return calibrated


def _zscore(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if len(array) == 0:
        return array
    std = float(np.nanstd(array))
    mean = float(np.nanmean(array))
    if not np.isfinite(std) or std == 0.0:
        return np.zeros_like(array, dtype=float)
    return (array - mean) / std


def _zscore_with_train(train_values: np.ndarray, test_values: np.ndarray) -> np.ndarray:
    train = np.asarray(train_values, dtype=float)
    test = np.asarray(test_values, dtype=float)
    if len(train) == 0:
        return test
    std = float(np.nanstd(train))
    mean = float(np.nanmean(train))
    if not np.isfinite(std) or std == 0.0:
        return np.zeros_like(test, dtype=float)
    return (test - mean) / std


def _safe_spearman(left: np.ndarray, right: pd.Series) -> float:
    left_arr = np.asarray(left, dtype=float)
    right_arr = pd.to_numeric(right, errors="coerce").fillna(0.0).to_numpy(dtype=float)
    if len(left_arr) < 2 or len(right_arr) < 2:
        return 0.0
    try:
        corr = spearmanr(left_arr, right_arr).correlation
    except Exception:
        corr = np.nan
    return float(0.0 if corr is None or np.isnan(corr) else corr)


def _payoff_ratio(values: pd.Series) -> float:
    series = pd.to_numeric(values, errors="coerce").dropna()
    wins = series[series > 0]
    losses = series[series < 0]
    if wins.empty and losses.empty:
        return 0.0
    if losses.empty:
        return float("inf")
    if wins.empty:
        return 0.0
    return float(abs(wins.mean()) / abs(losses.mean()))


def _monthly_random_baseline(
    frame: pd.DataFrame,
    *,
    selected_count: int,
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    if frame.empty or selected_count <= 0:
        return {"random_mean": 0.0, "random_p95": 0.0, "samples": []}
    rng = np.random.default_rng(seed)
    sample_returns = pd.to_numeric(frame["net_return_label"], errors="coerce").fillna(0.0)
    month_keys = pd.to_datetime(frame["timestamp"], utc=True).dt.to_period("M")
    counts = frame.groupby(month_keys).size().to_dict()
    monthly_indices = {
        key: frame.index[month_keys == key].to_numpy()
        for key in counts
    }
    samples: list[float] = []
    for _ in range(iterations):
        chosen: list[int] = []
        for key, count in counts.items():
            pool = monthly_indices.get(key, np.array([], dtype=int))
            if len(pool) == 0:
                continue
            if len(pool) >= count:
                chosen.extend(rng.choice(pool, size=count, replace=False).tolist())
            else:
                chosen.extend(pool.tolist())
        if not chosen:
            continue
        samples.append(float(sample_returns.loc[chosen].mean()))
    if not samples:
        return {"random_mean": 0.0, "random_p95": 0.0, "samples": []}
    samples_arr = np.asarray(samples, dtype=float)
    return {
        "random_mean": float(np.mean(samples_arr)),
        "random_p95": float(np.percentile(samples_arr, 95)),
        "samples": samples,
    }


def _aggregate_candidate_rows(spec: ObjectiveCandidateSpec, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "candidate_name": spec.name,
            "candidate_type": spec.candidate_type,
            "split_count": 0,
            "mean_spearman_corr": 0.0,
            "mean_realized_return_top_decile": 0.0,
            "mean_downside_loss_rate_top_decile": 0.0,
            "mean_payoff_ratio_top_decile": 0.0,
            "best_2026_metric": 0.0,
            "best_downside_metric": 0.0,
        }
    recent = [row for row in rows if row["split_name"] == "2026_H1"]
    return {
        "candidate_name": spec.name,
        "candidate_type": spec.candidate_type,
        "description": spec.description,
        "uses_ev_proxy": spec.uses_ev_proxy,
        "uses_probability": spec.uses_probability,
        "uses_downside_weighting": spec.uses_downside_weighting,
        "target_column": spec.target_column,
        "feature_columns": list(spec.feature_columns),
        "split_count": len(rows),
        "mean_spearman_corr": float(np.mean([row["spearman_corr"] for row in rows])),
        "mean_realized_return_top_decile": float(np.mean([row["mean_realized_return_top_decile"] for row in rows])),
        "mean_downside_loss_rate_top_decile": float(np.mean([row["downside_loss_rate_top_decile"] for row in rows])),
        "mean_payoff_ratio_top_decile": float(np.mean([row["payoff_ratio_top_decile"] for row in rows if np.isfinite(row["payoff_ratio_top_decile"])])) if any(np.isfinite(row["payoff_ratio_top_decile"]) for row in rows) else 0.0,
        "best_2026_metric": float(recent[0]["mean_realized_return_top_decile"]) if recent else 0.0,
        "best_downside_metric": float(recent[0]["downside_loss_rate_top_decile"]) if recent else 0.0,
        "recent_2026_selected_count": int(recent[0]["selected_count"]) if recent else 0,
        "recent_2026_random_p95": float(recent[0]["random_monthly_count_preserving_p95"]) if recent else 0.0,
        "recent_2026_beats_random_p95": bool(recent[0]["beats_random_p95"]) if recent else False,
        "recent_window_status": _recent_window_status(recent),
        "selected_count_total": int(sum(row["selected_count"] for row in rows)),
    }


def _recent_window_status(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "RECENT_WINDOW_INCONCLUSIVE"
    row = rows[0]
    if row["selected_count"] < 30:
        return "RECENT_WINDOW_SAMPLE_TOO_SMALL"
    if row["mean_realized_return_top_decile"] > 0 and row["beats_random_p95"]:
        return "RECENT_WINDOW_PROMISING"
    if row["mean_realized_return_top_decile"] <= 0:
        return "RECENT_WINDOW_WEAK"
    return "RECENT_WINDOW_INCONCLUSIVE"


def _temporal_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"temporal_status": "PAYOFF_OBJECTIVE_TEMPORAL_ROBUSTNESS_FAILED", "rows": []}
    split_groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        split_groups.setdefault(row["split_name"], []).append(row)
    split_records = []
    for split_name, split_rows in split_groups.items():
        recent = split_rows[0]
        split_records.append(
            {
                "split_name": split_name,
                "mean_spearman_corr": float(np.mean([row["spearman_corr"] for row in split_rows])),
                "mean_realized_return_top_decile": float(np.mean([row["mean_realized_return_top_decile"] for row in split_rows])),
                "selected_count_total": int(sum(row["selected_count"] for row in split_rows)),
                "recent_2026_selected_count": int(recent["selected_count"]) if split_name == "2026_H1" else None,
                "recent_2026_mean_realized_return_top_decile": float(recent["mean_realized_return_top_decile"]) if split_name == "2026_H1" else None,
                "recent_2026_beats_random_p95": bool(recent["beats_random_p95"]) if split_name == "2026_H1" else None,
            }
        )
    return {
        "temporal_status": "PAYOFF_OBJECTIVE_TEMPORAL_ROBUSTNESS_COMPLETE",
        "split_records": split_records,
        "recent_window_status": "PAYOFF_OBJECTIVE_RECENT_WINDOW_WEAK"
        if any(record["split_name"] == "2026_H1" and (record["recent_2026_mean_realized_return_top_decile"] or 0.0) <= 0 for record in split_records)
        else "PAYOFF_OBJECTIVE_TEMPORAL_ROBUSTNESS_COMPLETE",
    }


def _regime_summary(frame: pd.DataFrame, candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    regime_column = None
    for candidate in ["macro_regime", "derivatives_risk_regime"]:
        if candidate in frame.columns:
            regime_column = candidate
            break
    if regime_column is None:
        return {"regime_breakdown_status": "PAYOFF_OBJECTIVE_REGIME_DATA_LIMITED", "regime_column": None, "rows": []}
    subset = frame[frame["analysis_ready"]].copy()
    if subset.empty:
        return {"regime_breakdown_status": "PAYOFF_OBJECTIVE_REGIME_DATA_LIMITED", "regime_column": regime_column, "rows": []}
    records = []
    for regime_value, regime_frame in subset.groupby(regime_column):
        records.append(
            {
                "regime": str(regime_value),
                "count": int(len(regime_frame)),
                "mean_net_return": float(pd.to_numeric(regime_frame["net_return_label"], errors="coerce").fillna(0.0).mean()),
                "mean_ev_proxy": float(pd.to_numeric(regime_frame.get("ev_calibrated_proxy"), errors="coerce").fillna(0.0).mean()) if "ev_calibrated_proxy" in regime_frame.columns else 0.0,
            }
        )
    return {
        "regime_breakdown_status": "PAYOFF_OBJECTIVE_REGIME_BREAKDOWN_COMPLETE",
        "regime_column": regime_column,
        "rows": records,
    }


def _multiple_testing_risk(candidates_count: int, split_count: int) -> str:
    if candidates_count <= 4 and split_count <= 3:
        return "LOW"
    if candidates_count <= 8 and split_count <= 5:
        return "MODERATE"
    return "HIGH"
