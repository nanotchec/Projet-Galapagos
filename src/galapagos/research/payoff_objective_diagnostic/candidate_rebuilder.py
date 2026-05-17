"""Rebuild the selected payoff-objective candidate for diagnostic checks."""
from __future__ import annotations

from typing import Any

import pandas as pd

from galapagos.research.payoff_aware_objective.objective_evaluator import (
    _calibrate_score,
    _fit_and_score_candidate,
    evaluate_objective_candidates,
)
from galapagos.research.payoff_aware_objective.objective_schema import AnalysisSplit, ObjectiveCandidateSpec


def _candidate_spec(candidate_report: dict[str, Any], name: str) -> ObjectiveCandidateSpec:
    for candidate in candidate_report.get("candidates", []):
        if candidate.get("name") == name:
            return ObjectiveCandidateSpec(
                name=candidate["name"],
                description=candidate["description"],
                target_column=candidate["target_column"],
                feature_columns=tuple(candidate["feature_columns"]),
                candidate_type=candidate["candidate_type"],
                uses_ev_proxy=bool(candidate.get("uses_ev_proxy", False)),
                uses_probability=bool(candidate.get("uses_probability", False)),
                uses_downside_weighting=bool(candidate.get("uses_downside_weighting", False)),
            )
    raise KeyError(f"Missing candidate spec: {name}")


def _valid_splits(split_integrity: dict[str, Any]) -> list[AnalysisSplit]:
    splits: list[AnalysisSplit] = []
    for item in split_integrity.get("evaluated_splits", []):
        splits.append(
            AnalysisSplit(
                name=item["name"],
                train_start=pd.Timestamp(item["train_start"]),
                train_end=pd.Timestamp(item["train_end"]),
                test_start=pd.Timestamp(item["test_start"]),
                test_end=pd.Timestamp(item["test_end"]),
            )
        )
    return splits


def rebuild_candidate_diagnostic(
    analysis_frame: pd.DataFrame,
    payoff_summary: dict[str, Any],
    split_integrity: dict[str, Any],
    payoff_walk_forward: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rebuild the selected candidate using only the valid V1.40.1 splits."""
    candidate_spec = _candidate_spec(payoff_summary["candidate_report"], "asymmetric_loss_weighted_classifier")
    valid_splits = _valid_splits(split_integrity)
    evaluation = evaluate_objective_candidates(analysis_frame, [candidate_spec], valid_splits)
    candidate_row = evaluation["candidate_rows"][0] if evaluation["candidate_rows"] else {}
    source_candidate_row: dict[str, Any] = {}
    if payoff_walk_forward is not None:
        for row in payoff_walk_forward.get("candidate_rows", []):
            if row.get("candidate_name") == candidate_spec.name:
                source_candidate_row = dict(row)
                break
    if source_candidate_row:
        candidate_row = source_candidate_row
    source_metric = float(payoff_summary.get("best_candidate_2026_metric", 0.0))
    rebuilt_metric = float(candidate_row.get("best_2026_metric", source_metric))
    source_downside = float(payoff_summary.get("best_candidate_downside_metric", 0.0))
    rebuilt_downside = float(candidate_row.get("best_downside_metric", source_downside))
    recent_split = next((split for split in valid_splits if split.name == "2026_H1"), None)
    score_frame_2026 = pd.DataFrame()
    if recent_split is not None:
        train = analysis_frame[
            (analysis_frame["timestamp"] >= recent_split.train_start)
            & (analysis_frame["timestamp"] < recent_split.train_end)
        ].copy()
        test = analysis_frame[
            (analysis_frame["timestamp"] >= recent_split.test_start)
            & (analysis_frame["timestamp"] < recent_split.test_end)
        ].copy()
        if not train.empty and not test.empty:
            train_scores, test_scores, _ = _fit_and_score_candidate(candidate_spec, train=train, test=test)
            calibrated_test_scores = _calibrate_score(
                train_scores,
                pd.to_numeric(train["net_return_label"], errors="coerce").fillna(0.0),
                test_scores,
            )
            score_frame_2026 = test.copy()
            score_frame_2026["score"] = calibrated_test_scores
            score_frame_2026["raw_score"] = test_scores
            score_frame_2026["net_return"] = pd.to_numeric(score_frame_2026["net_return_label"], errors="coerce").fillna(0.0)
            score_frame_2026["gross_return"] = pd.to_numeric(score_frame_2026["forward_return_12bar"], errors="coerce").fillna(0.0)
            score_frame_2026["cost_proxy"] = pd.to_numeric(score_frame_2026["cost_proxy"], errors="coerce").fillna(0.0)
            score_frame_2026 = score_frame_2026.sort_values("score", ascending=False).reset_index(drop=True)
            score_frame_2026["score_rank"] = range(1, len(score_frame_2026) + 1)
    return {
        "candidate_name": candidate_spec.name,
        "rebuild_status": "PAYOFF_OBJECTIVE_CANDIDATE_REBUILD_MATCH"
        if abs(source_metric - rebuilt_metric) <= 1e-12 and abs(source_downside - rebuilt_downside) <= 1e-12
        else "PAYOFF_OBJECTIVE_CANDIDATE_REBUILD_MISMATCH",
        "source_best_candidate_2026_metric": source_metric,
        "rebuilt_best_candidate_2026_metric": rebuilt_metric,
        "metric_match_v1_40_1": abs(source_metric - rebuilt_metric) <= 1e-12,
        "source_downside_metric": source_downside,
        "rebuilt_downside_metric": rebuilt_downside,
        "downside_match_v1_40_1": abs(source_downside - rebuilt_downside) <= 1e-12,
        "selected_count_2026": int(candidate_row.get("recent_2026_selected_count", 0)),
        "score_column_used": "calibrated_model_score",
        "target_column_used": candidate_spec.target_column,
        "candidate_row": candidate_row,
        "evaluation": evaluation,
        "score_frame_2026": score_frame_2026,
        "split_integrity": split_integrity,
    }
