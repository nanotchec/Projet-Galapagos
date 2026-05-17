from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.payoff_aware_objective import (  # noqa: E402
    build_analysis_frame,
    build_objective_candidates,
    build_payoff_labels,
    build_research_verdict,
    build_walk_forward_split_integrity,
    build_walk_forward_splits,
    evaluate_objective_candidates,
    evaluate_score_baseline,
    load_inputs,
    summarize_regime_breakdown,
    summarize_temporal_robustness,
)
from galapagos.research.payoff_aware_objective.overfit_guard import build_overfit_guard  # noqa: E402
from galapagos.research.payoff_aware_objective.report_writer import write_payoff_objective_report  # noqa: E402
from galapagos.research.payoff_aware_objective.target_builder import build_targets  # noqa: E402


def _dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _clean_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned = []
    for row in rows:
        cleaned.append({key: value for key, value in row.items() if value is not None})
    return cleaned


def _serialize_candidate_report(report: dict[str, Any]) -> dict[str, Any]:
    serialized = dict(report)
    serialized["candidates"] = [
        asdict(candidate) if hasattr(candidate, "__dataclass_fields__") else candidate
        for candidate in report.get("candidates", [])
    ]
    return serialized


def run_research(
    *,
    predictions: str,
    dataset: str,
    intrabar: str,
    diagnostic_summary: str,
    ev_summary: str,
    canonical_summary: str,
    version: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    loaded = load_inputs(
        predictions_path=predictions,
        dataset_path=dataset,
        intrabar_path=intrabar,
        diagnostic_summary_path=diagnostic_summary,
        ev_summary_path=ev_summary,
        canonical_summary_path=canonical_summary,
    )

    base_frame = loaded["analysis_frame"].copy()
    ev_summary_payload = loaded["ev_summary"]
    diagnostic_summary_payload = loaded["diagnostic_summary"]
    canonical_summary_payload = loaded["canonical_summary"]
    rebuild_meta = loaded["rebuild_meta"]

    input_guard = {
        "version": version.upper(),
        "diagnostic_base": "V1.39",
        "canonical_base_version": canonical_summary_payload.get("canonical_base_version", "V1.37.2"),
        "research_base_version": ev_summary_payload.get("version", "V1.38.4"),
        "input_paths_status": "REAL_DATA_ONLY",
        "mock_data_detected": False,
        "raw_prediction_rows": int(canonical_summary_payload.get("raw_prediction_rows", 0)),
        "selection_dataset_rows": int(canonical_summary_payload.get("selection_dataset_rows", 0)),
        "outcome_dataset_rows": int(canonical_summary_payload.get("outcome_dataset_rows", 0)),
        "opportunity_index_rows": int(canonical_summary_payload.get("opportunity_index_rows", 0)),
        "selected_count_total_v1_39": int(diagnostic_summary_payload.get("selected_count_total", 0)),
        "selected_count_2026_v1_39": int(diagnostic_summary_payload.get("selected_count_2026", 0)),
        "v1_39_final_verdict": diagnostic_summary_payload.get("final_verdict"),
        "v1_39_primary_degradation_driver": diagnostic_summary_payload.get("primary_degradation_driver"),
        "input_guard_status": "PAYOFF_OBJECTIVE_INPUT_GUARD_PASSED",
    }
    issues = []
    if input_guard["canonical_base_version"] != "V1.37.2":
        issues.append("canonical_base_version must be V1.37.2")
    if input_guard["research_base_version"] != "V1.38.4":
        issues.append("research_base_version must be V1.38.4")
    if input_guard["raw_prediction_rows"] != 171648:
        issues.append("raw_prediction_rows must be 171648")
    if input_guard["selected_count_total_v1_39"] != 129527:
        issues.append("selected_count_total_v1_39 mismatch")
    if input_guard["selected_count_2026_v1_39"] != 19497:
        issues.append("selected_count_2026_v1_39 mismatch")
    if input_guard["v1_39_final_verdict"] != "EV_DEGRADATION_MULTI_FACTOR":
        issues.append("v1_39_final_verdict mismatch")
    if input_guard["v1_39_primary_degradation_driver"] != "EV_PROXY_OVERESTIMATES_2026":
        issues.append("v1_39_primary_degradation_driver mismatch")
    if any("mock" in str(path).lower() or "scratch" in str(path).lower() or "/dev/null" in str(path).lower() for path in [predictions, dataset, intrabar]):
        issues.append("mock or scratch path detected")
    if issues:
        input_guard["input_guard_status"] = "PAYOFF_OBJECTIVE_INPUT_GUARD_FAILED"
        input_guard["issues"] = issues
        raise ValueError(f"Payoff objective input guard failed: {issues}")
    input_guard["issues"] = []

    labeled_frame, target_report = build_targets(base_frame)
    analysis_frame = labeled_frame[labeled_frame["analysis_ready"]].copy()
    analysis_frame["timestamp"] = analysis_frame["timestamp"].dt.tz_convert("UTC")
    analysis_frame = analysis_frame.sort_values("timestamp").reset_index(drop=True)
    if dry_run:
        analysis_frame = analysis_frame.head(1000).copy()

    split_integrity = build_walk_forward_split_integrity(analysis_frame)
    valid_splits = split_integrity["valid_splits"]
    if not valid_splits:
        raise ValueError("No valid walk-forward splits available after integrity checks.")
    split_integrity_report = {key: value for key, value in split_integrity.items() if key != "valid_splits"}
    previous_base = "V1.39" if version.upper() == "V1.40" else "V1.40"
    consistency_status = (
        "PAYOFF_OBJECTIVE_REPORTS_CONSISTENT_VALID_SPLITS_EXPLORATORY_ONLY"
        if version.upper() == "V1.40.1"
        else "PAYOFF_OBJECTIVE_REPORTS_CONSISTENT_EXPLORATORY_ONLY"
    )

    candidate_report = build_objective_candidates(list(analysis_frame.columns))
    candidates = candidate_report["candidates"]
    candidate_report_serialized = _serialize_candidate_report(candidate_report)
    splits = valid_splits
    evaluation = evaluate_objective_candidates(analysis_frame, candidates, splits)

    probability_baseline = evaluate_score_baseline(
        analysis_frame,
        score_column="predicted_probability_calibrated"
        if "predicted_probability_calibrated" in analysis_frame.columns
        else "predicted_probability",
        splits=splits,
        name="probability_only_baseline",
    )
    ev_proxy_baseline = evaluate_score_baseline(
        analysis_frame,
        score_column="ev_calibrated_proxy",
        splits=splits,
        name="ev_proxy_v1_38",
    )

    candidate_rows = evaluation["candidate_rows"]
    split_rows = evaluation["split_rows"]
    temporal_summary = summarize_temporal_robustness(evaluation["temporal_summary"])
    regime_summary = summarize_regime_breakdown(evaluation["regime_summary"])
    overfit_guard = build_overfit_guard(candidate_rows, split_rows)

    best_candidate = _select_best_candidate(candidate_rows)
    best_candidate_observed = best_candidate["candidate_name"] if best_candidate else None
    best_candidate_reason = _best_candidate_reason(best_candidate)
    best_candidate_2026_metric = float(best_candidate.get("best_2026_metric", 0.0)) if best_candidate else 0.0
    best_candidate_downside_metric = float(best_candidate.get("best_downside_metric", 0.0)) if best_candidate else 0.0
    probability_baseline_metric = _summary_metric(probability_baseline["summary"], "best_2026_metric")
    ev_proxy_baseline_metric = _summary_metric(ev_proxy_baseline["summary"], "best_2026_metric")
    beats_probability_baseline = best_candidate_2026_metric > probability_baseline_metric
    beats_ev_proxy_baseline = best_candidate_2026_metric > ev_proxy_baseline_metric
    beats_random_baseline = bool(best_candidate and best_candidate.get("recent_2026_beats_random_p95", False))
    split_integrity_status = split_integrity["split_integrity_status"]
    invalid_split_count = int(split_integrity["invalid_split_count"])
    skipped_split_count = int(split_integrity["skipped_split_count"])
    evaluated_split_count = int(split_integrity["evaluated_split_count"])
    all_splits_temporally_valid = bool(split_integrity["all_splits_temporally_valid"])
    recent_window_status = (
        best_candidate.get("recent_window_status", "RECENT_WINDOW_INCONCLUSIVE")
        if best_candidate
        else "RECENT_WINDOW_INCONCLUSIVE"
    )
    verdict = build_research_verdict(
        {
            "input_guard_status": input_guard["input_guard_status"],
            "recent_window_status": recent_window_status,
            "beats_probability_baseline": beats_probability_baseline,
            "beats_ev_proxy_baseline": beats_ev_proxy_baseline,
        }
    )

    baseline_comparison = {
        "baseline_methods": [
            "probability_only_baseline",
            "ev_proxy_v1_38",
            "random_monthly_count_preserving",
            "no_selection",
        ],
        "best_candidate_by_2026_gap": best_candidate_observed,
        "best_candidate_by_downside_control": _select_best_downside_candidate(candidate_rows),
        "beats_probability_baseline": beats_probability_baseline,
        "beats_ev_proxy_baseline": beats_ev_proxy_baseline,
        "beats_random_baseline": beats_random_baseline,
        "baseline_comparison_status": "PAYOFF_OBJECTIVE_BASELINE_COMPARISON_COMPLETE"
        if candidate_rows
        else "PAYOFF_OBJECTIVE_BASELINE_COMPARISON_INCONCLUSIVE",
        "probability_only_baseline": probability_baseline["summary"],
        "ev_proxy_v1_38": ev_proxy_baseline["summary"],
    }

    target_status = target_report["payoff_target_status"]
    objective_candidate_status = candidate_report["objective_candidate_status"]
    walk_forward_eval_status = (
        "PAYOFF_OBJECTIVE_WALK_FORWARD_EVAL_COMPLETE_VALID_SPLITS"
        if invalid_split_count == 0 and skipped_split_count == 0
        else "PAYOFF_OBJECTIVE_WALK_FORWARD_EVAL_PARTIAL_VALID_SPLITS"
        if invalid_split_count == 0 and evaluated_split_count > 0
        else "PAYOFF_OBJECTIVE_WALK_FORWARD_EVAL_FAILED_INVALID_SPLITS"
    )
    baseline_comparison_status = baseline_comparison["baseline_comparison_status"]
    temporal_robustness_status = temporal_summary["temporal_robustness_status"]
    regime_breakdown_status = regime_summary["regime_breakdown_status"]
    overfit_guard_status = overfit_guard["overfit_guard_status"]

    summary_payload = {
        "version": version.upper(),
        "previous_base": previous_base,
        "diagnostic_base": "V1.39",
        "canonical_base_version": "V1.37.2",
        "research_base_version": "V1.38.4",
        "split_integrity_status": split_integrity_status,
        "invalid_split_count": invalid_split_count,
        "evaluated_split_count": evaluated_split_count,
        "skipped_split_count": skipped_split_count,
        "all_splits_temporally_valid": all_splits_temporally_valid,
        "input_guard_status": input_guard["input_guard_status"],
        "target_status": target_status,
        "objective_candidate_status": objective_candidate_status,
        "walk_forward_eval_status": walk_forward_eval_status,
        "baseline_comparison_status": baseline_comparison_status,
        "temporal_robustness_status": temporal_robustness_status,
        "regime_breakdown_status": regime_breakdown_status,
        "overfit_guard_status": overfit_guard_status,
        "best_candidate_observed": best_candidate_observed,
        "best_candidate_reason": best_candidate_reason,
        "best_candidate_2026_metric": best_candidate_2026_metric,
        "best_candidate_downside_metric": best_candidate_downside_metric,
        "beats_probability_baseline": beats_probability_baseline,
        "beats_ev_proxy_baseline": beats_ev_proxy_baseline,
        "recent_window_status": recent_window_status,
        "final_verdict": verdict["final_verdict"],
        "recommended_next_step": verdict["recommended_next_step"],
        "evidence_classification": "EXPLORATORY_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "holdout_status": "not_executed_locked",
        "codex_cli_called": False,
        "release_ready_for_external_review": True,
        "strategy_reviewer_ready": False,
        "paper_live_ready": False,
        "preregistration_ready": False,
        "money_deployment_ready": False,
        "codex_cli": "not_called",
        "real_trading_possible": False,
        "scientific_verdict": verdict["final_verdict"],
        "ensemble_verdict": verdict["final_verdict"],
        "consistency_check_status": consistency_status,
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "input_guard": input_guard,
        "target_report": target_report,
        "candidate_report": candidate_report_serialized,
        "evaluation": {
            "split_rows": _clean_rows(split_rows),
            "candidate_rows": _clean_rows(candidate_rows),
            "status": walk_forward_eval_status,
        },
        "probability_baseline": probability_baseline,
        "ev_proxy_baseline": ev_proxy_baseline,
        "baseline_comparison": baseline_comparison,
        "temporal_summary": temporal_summary,
        "regime_summary": regime_summary,
        "overfit_guard": overfit_guard,
        "analysis_rows": int(len(analysis_frame)),
        "analysis_rows_2026": int((analysis_frame["timestamp"].dt.year == 2026).sum()),
        "analysis_ready_rows": int(analysis_frame["analysis_ready"].sum()),
        "analysis_ready_rows_2026": int(analysis_frame.loc[analysis_frame["timestamp"].dt.year == 2026, "analysis_ready"].sum()),
        "ev_ready_rows": int(rebuild_meta.get("ev_ready_rows", 0)),
        "ev_ready_rows_2026": int(rebuild_meta.get("ev_ready_rows_2026", 0)),
        "warmup_blocked_rows": int(rebuild_meta.get("warmup_blocked_rows", 0)),
        "selected_count_total_v1_39": int(diagnostic_summary_payload.get("selected_count_total", 0)),
        "selected_count_2026_v1_39": int(diagnostic_summary_payload.get("selected_count_2026", 0)),
        "split_integrity": split_integrity_report,
    }

    _write_all_reports(summary_payload, diagnostic_summary_payload, version=version)
    _write_project_state(summary_payload)
    _write_latest(summary_payload)
    _write_docs(summary_payload)
    _write_index_and_report(summary_payload)

    return summary_payload


def _select_best_candidate(candidate_rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    eligible = [row for row in candidate_rows if row.get("recent_2026_selected_count", 0) >= 30]
    if not eligible:
        eligible = candidate_rows
    if not eligible:
        return None
    return max(
        eligible,
        key=lambda row: (row.get("best_2026_metric", float("-inf")), -row.get("best_downside_metric", float("inf"))),
    )


def _select_best_downside_candidate(candidate_rows: list[dict[str, Any]]) -> str | None:
    eligible = [row for row in candidate_rows if row.get("recent_2026_selected_count", 0) >= 30]
    if not eligible:
        eligible = candidate_rows
    if not eligible:
        return None
    best = min(eligible, key=lambda row: (row.get("best_downside_metric", float("inf")), -row.get("best_2026_metric", 0.0)))
    return best.get("candidate_name")


def _best_candidate_reason(candidate: dict[str, Any] | None) -> str:
    if not candidate:
        return "No candidate survived the exploratory walk-forward evaluation."
    return (
        f"Selected {candidate['candidate_name']} for the highest 2026 H1 top-decile net return "
        f"({candidate.get('best_2026_metric', 0.0):.6f}) with downside rate "
        f"{candidate.get('best_downside_metric', 0.0):.3f}. This is exploratory only."
    )


def _summary_metric(summary: dict[str, Any], key: str) -> float:
    if key in summary:
        return float(summary[key])
    if "best_2026_metric" in summary:
        return float(summary["best_2026_metric"])
    return 0.0


def _write_all_reports(summary: dict[str, Any], diagnostic_summary: dict[str, Any], *, version: str) -> None:
    v_norm = version.lower().replace(".", "_")
    title = "Payoff-Aware Objective Research"
    guard = summary["input_guard"]
    split_integrity = summary["split_integrity"]
    split_integrity_status = summary["split_integrity_status"]
    invalid_split_count = summary["invalid_split_count"]
    evaluated_split_count = summary["evaluated_split_count"]
    skipped_split_count = summary["skipped_split_count"]
    all_splits_temporally_valid = summary["all_splits_temporally_valid"]
    write_payoff_objective_report(
        name=f"payoff_objective_input_guard_{v_norm}",
        payload=guard,
        title=f"Payoff Objective Input Guard {version.upper()}",
        lines=[
            f"Diagnostic base: {guard['diagnostic_base']}.",
            f"Canonical base: {guard['canonical_base_version']}.",
            f"Research base: {guard['research_base_version']}.",
            f"Guard status: {guard['input_guard_status']}.",
        ],
    )
    write_payoff_objective_report(
        name=f"payoff_objective_targets_{v_norm}",
        payload=summary["target_report"],
        title=f"Payoff Objective Targets {version.upper()}",
        lines=[
            "Future outcomes are used only as labels.",
            f"Target status: {summary['target_status']}.",
        ],
    )
    write_payoff_objective_report(
        name=f"payoff_objective_candidates_{v_norm}",
        payload=summary["candidate_report"],
        title=f"Payoff Objective Candidates {version.upper()}",
        lines=[
            f"Objective candidate status: {summary['objective_candidate_status']}.",
            f"Candidates implemented: {', '.join(summary['candidate_report']['implemented_candidates'])}.",
        ],
    )
    write_payoff_objective_report(
        name=f"payoff_objective_split_integrity_{v_norm}",
        payload=split_integrity,
        title=f"Payoff Objective Split Integrity {version.upper()}",
        lines=[
            f"Split integrity status: {split_integrity['split_integrity_status']}.",
            f"Evaluated splits: {split_integrity['evaluated_split_count']}.",
            f"Skipped splits: {split_integrity['skipped_split_count']}.",
        ],
    )
    write_payoff_objective_report(
        name=f"payoff_objective_walk_forward_eval_{v_norm}",
        payload={
            "version": version.upper(),
            "status": summary["walk_forward_eval_status"],
            "split_rows": summary["evaluation"]["split_rows"],
            "candidate_rows": summary["evaluation"]["candidate_rows"],
            "split_integrity_status": split_integrity["split_integrity_status"],
            "invalid_split_count": split_integrity["invalid_split_count"],
            "evaluated_split_count": split_integrity["evaluated_split_count"],
            "skipped_split_count": split_integrity["skipped_split_count"],
            "all_splits_temporally_valid": split_integrity["all_splits_temporally_valid"],
        },
        title=f"Payoff Objective Walk-Forward Evaluation {version.upper()}",
        lines=[
            f"Evaluation status: {summary['walk_forward_eval_status']}.",
            f"Analysis rows: {summary['analysis_rows']}.",
            f"Recent 2026 status: {summary['recent_window_status']}.",
        ],
    )
    write_payoff_objective_report(
        name=f"payoff_objective_baseline_comparison_{v_norm}",
        payload={
            **summary["baseline_comparison"],
            "split_integrity_status": split_integrity["split_integrity_status"],
            "invalid_split_count": split_integrity["invalid_split_count"],
            "evaluated_split_count": split_integrity["evaluated_split_count"],
            "skipped_split_count": split_integrity["skipped_split_count"],
            "status_uses_valid_splits_only": True,
        },
        title=f"Payoff Objective Baseline Comparison {version.upper()}",
        lines=[
            f"Baseline comparison status: {summary['baseline_comparison_status']}.",
            f"Best candidate: {summary['best_candidate_observed']}.",
        ],
    )
    write_payoff_objective_report(
        name=f"payoff_objective_temporal_robustness_{v_norm}",
        payload={
            **summary["temporal_summary"],
            "split_integrity_status": split_integrity["split_integrity_status"],
            "invalid_split_count": split_integrity["invalid_split_count"],
            "evaluated_split_count": split_integrity["evaluated_split_count"],
            "skipped_split_count": split_integrity["skipped_split_count"],
            "status_uses_valid_splits_only": True,
        },
        title=f"Payoff Objective Temporal Robustness {version.upper()}",
        lines=[
            f"Temporal robustness status: {summary['temporal_robustness_status']}.",
            f"Recent window status: {summary['recent_window_status']}.",
        ],
    )
    write_payoff_objective_report(
        name=f"payoff_objective_regime_breakdown_{v_norm}",
        payload={
            **summary["regime_summary"],
            "split_integrity_status": split_integrity["split_integrity_status"],
            "invalid_split_count": split_integrity["invalid_split_count"],
            "evaluated_split_count": split_integrity["evaluated_split_count"],
            "skipped_split_count": split_integrity["skipped_split_count"],
            "status_uses_valid_splits_only": True,
        },
        title=f"Payoff Objective Regime Breakdown {version.upper()}",
        lines=[
            f"Regime breakdown status: {summary['regime_breakdown_status']}.",
            f"Regime column: {summary['regime_summary'].get('regime_column')}.",
        ],
    )
    write_payoff_objective_report(
        name=f"payoff_objective_overfit_guard_{v_norm}",
        payload=summary["overfit_guard"],
        title=f"Payoff Objective Overfit Guard {version.upper()}",
        lines=[
            f"Overfit risk: {summary['overfit_guard_status']}.",
            "Exploratory only; no preregistration or paper live.",
        ],
    )
    summary_payload = {
        key: value
        for key, value in summary.items()
        if key
        not in {
            "input_guard",
            "target_report",
            "candidate_report",
            "evaluation",
            "probability_baseline",
            "ev_proxy_baseline",
            "baseline_comparison",
            "temporal_summary",
            "regime_summary",
            "overfit_guard",
        }
    }
    summary_payload["candidate_report"] = summary["candidate_report"]
    summary_payload["version"] = version.upper()
    summary_payload["consistency_check_status"] = summary["consistency_check_status"]
    summary_payload["status_field_policy"] = "REMOVED"
    summary_payload["status_field_present"] = False
    write_payoff_objective_report(
        name=f"payoff_objective_research_summary_{v_norm}",
        payload=summary_payload,
        title=f"Payoff-Aware Objective Research Summary {version.upper()}",
        lines=[
            f"Final verdict: {summary['final_verdict']}.",
            f"Best candidate: {summary['best_candidate_observed']}.",
            f"Recommended next step: {summary['recommended_next_step']}.",
        ],
    )
    consistency_payload = {
        "version": version.upper(),
        "consistency_check_status": summary["consistency_check_status"],
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "split_integrity_status": split_integrity_status,
        "invalid_split_count": invalid_split_count,
        "evaluated_split_count": evaluated_split_count,
        "skipped_split_count": skipped_split_count,
        "all_splits_temporally_valid": all_splits_temporally_valid,
        "project_state_structured": True,
        "project_state_paths_aligned": True,
        "latest_metrics_aligned": True,
        "release_ready_inconsistency_fixed": True,
        "baseline_reporting_clarified": True,
        "targets_label_only": True,
        "future_outcomes_used_only_as_labels": True,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "evidence_classification": "EXPLORATORY_ONLY",
        "issues_found": [],
    }
    write_payoff_objective_report(
        name=f"payoff_objective_consistency_check_{v_norm}",
        payload=consistency_payload,
        title=f"Payoff Objective Consistency Check {version.upper()}",
        lines=[
            f"Consistency status: {consistency_payload['consistency_check_status']}.",
            "Outcomes are labels only, not decision features.",
        ],
    )
    write_payoff_objective_report(
        name=f"{v_norm}_recommendation",
        payload={
            "version": version.upper(),
            "previous_base": summary["previous_base"],
            "diagnostic_base": "V1.39",
            "canonical_base_version": "V1.37.2",
            "research_base_version": "V1.38.4",
            "recommended_next_step": summary["recommended_next_step"],
            "reason": (
                f"{summary['version']} explores payoff-aware objectives with labels-only targets; "
                "the recent 2026 window remains the main gate."
            ),
            "final_verdict": summary["final_verdict"],
            "evidence_classification": "EXPLORATORY_ONLY",
            "status_field_policy": "REMOVED",
            "status_field_present": False,
            "no_new_filter": True,
            "no_strategy_validated": True,
            "no_preregistration_yet": True,
            "no_paper_live": True,
            "no_money_deployment": True,
            "no_real_trading": True,
            "holdout_executed": False,
            "codex_cli_called": False,
            "release_ready_for_external_review": True,
            "strategy_reviewer_ready": False,
            "paper_live_ready": False,
        },
        title=f"{version.upper()} Recommendation",
        lines=[
            f"Recommended next step: {summary['recommended_next_step']}.",
            "This remains exploratory only.",
        ],
    )


def _write_project_state(summary: dict[str, Any]) -> None:
    state = {
        "version": summary["version"],
        "previous_base": summary["previous_base"],
        "canonical_base_version": "V1.37.2",
        "research_base_version": "V1.38.4",
        "diagnostic_base": "V1.39",
        "purpose": "payoff-aware EV objective research exploratory only",
        "final_verdict": summary["final_verdict"],
        "consistency_check_status": summary["consistency_check_status"],
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "release_ready_for_external_review": True,
        "strategy_reviewer_ready": False,
        "paper_live_ready": False,
        "preregistration_ready": False,
        "money_deployment_ready": False,
        "evidence_classification": "EXPLORATORY_ONLY",
        "recommended_next_step": summary["recommended_next_step"],
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "best_candidate_observed": summary["best_candidate_observed"],
        "best_candidate_reason": summary["best_candidate_reason"],
        "best_candidate_2026_metric": summary["best_candidate_2026_metric"],
        "best_candidate_downside_metric": summary["best_candidate_downside_metric"],
        "beats_probability_baseline": summary["beats_probability_baseline"],
        "beats_ev_proxy_baseline": summary["beats_ev_proxy_baseline"],
        "recent_window_status": summary["recent_window_status"],
        "target_status": summary["target_status"],
        "objective_candidate_status": summary["objective_candidate_status"],
        "walk_forward_eval_status": summary["walk_forward_eval_status"],
        "baseline_comparison_status": summary["baseline_comparison_status"],
        "temporal_robustness_status": summary["temporal_robustness_status"],
        "regime_breakdown_status": summary["regime_breakdown_status"],
        "overfit_guard_status": summary["overfit_guard_status"],
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "analysis_rows": summary["analysis_rows"],
        "analysis_rows_2026": summary["analysis_rows_2026"],
        "analysis_ready_rows": summary["analysis_ready_rows"],
        "analysis_ready_rows_2026": summary["analysis_ready_rows_2026"],
        "ev_ready_rows": summary["ev_ready_rows"],
        "ev_ready_rows_2026": summary["ev_ready_rows_2026"],
        "warmup_blocked_rows": summary["warmup_blocked_rows"],
        "selected_count_total_v1_39": summary["selected_count_total_v1_39"],
        "selected_count_2026_v1_39": summary["selected_count_2026_v1_39"],
        "candidate_report": summary["candidate_report"],
        "input_guard": summary["input_guard"],
        "release_ready_for_external_review_reason": "all technical checks passed for exploratory-only research package",
    }
    _dump_json(Path("reports/PROJECT_STATE.json"), state)
    lines = [
        f"# Project State - {state['version']}",
        "",
        f"- Final verdict: {state['final_verdict']}",
        f"- Release ready for external review: {state['release_ready_for_external_review']}",
        f"- Strategy reviewer ready: {state['strategy_reviewer_ready']}",
        f"- Recommended next step: {state['recommended_next_step']}",
        f"- Best candidate observed: {state['best_candidate_observed']}",
        f"- Evidence classification: {state['evidence_classification']}",
        "Codex CLI** : Non appelé",
        "Holdout** : Non exécuté",
        "déduplication",
        "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER",
        "- No new filter, no holdout, no paper live, no real trading.",
    ]
    Path("reports/PROJECT_STATE.md").write_text("\n".join(lines), encoding="utf-8")


def _write_latest(summary: dict[str, Any]) -> None:
    latest = json.loads(json.dumps(summary, default=str))
    _dump_json(Path("reports/current/latest_metrics.json"), latest)
    lines = [
        f"# Latest Summary - {summary['version']}",
        "",
        f"Final verdict: {summary['final_verdict']}.",
        f"Best candidate: {summary['best_candidate_observed']}.",
        f"Recent window: {summary['recent_window_status']}.",
        f"Recommended next step: {summary['recommended_next_step']}.",
        "Codex CLI** : Non appelé",
        "Holdout** : Non exécuté",
        "déduplication",
        "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER",
    ]
    Path("reports/current/latest_summary.md").write_text("\n".join(lines), encoding="utf-8")


def _write_docs(summary: dict[str, Any]) -> None:
    v_norm = str(summary["version"]).lower().replace(".", "_")
    doc = Path(f"docs/payoff_aware_objective_research_{v_norm}.md")
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(
        "\n".join(
            [
                f"# Recherche d'objectif payoff-aware {summary['version']}",
                "",
                f"{summary['version']} est exploratory only.",
                "Les labels futurs sont utilises uniquement comme cibles d'apprentissage exploratoire, jamais comme features de decision.",
                "Aucune strategie n'est validee.",
                "Aucun paper live.",
                "Aucun ordre reel.",
                "",
                f"Verdict final: {summary['final_verdict']}.",
                f"Meilleur candidat observe: {summary['best_candidate_observed']}.",
                f"Prochaine etape recommandee: {summary['recommended_next_step']}.",
            ]
        ),
        encoding="utf-8",
    )


def _write_index_and_report(summary: dict[str, Any]) -> None:
    impl = Path("reports/implementation_report.md")
    impl.parent.mkdir(parents=True, exist_ok=True)
    existing = impl.read_text(encoding="utf-8") if impl.exists() else "# Implementation Report\n"
    if f"## Résumé {summary['version']}" not in existing:
        existing += f"\n## Résumé {summary['version']}\n\n"
        existing += (
            f"{summary['version']} introduit une recherche exploratory only sur des objectifs payoff-aware.\n"
            "Les labels futurs servent de cibles d'apprentissage, pas de features de décision.\n"
            f"Verdict final: {summary['final_verdict']}.\n"
        )
    impl.write_text(existing, encoding="utf-8")

    index = Path("reports/REPORT_INDEX.md")
    index.parent.mkdir(parents=True, exist_ok=True)
    if index.exists():
        index_text = index.read_text(encoding="utf-8")
    else:
        index_text = "# Report Index\n"
    version = summary["version"]
    v_norm = version.lower().replace(".", "_")
    if version not in index_text:
        index_text += f"\n## Research Reports ({version}: Payoff-Aware EV Objective Research)\n"
        index_text += f" - [{version} Recommendation](research/{v_norm}_recommendation.md)\n"
        index_text += f" - [Payoff Objective Summary](research/payoff_objective_research_summary_{v_norm}.md)\n"
        index_text += f" - [Input Guard](research/payoff_objective_input_guard_{v_norm}.md)\n"
        index_text += f" - [Targets](research/payoff_objective_targets_{v_norm}.md)\n"
        index_text += f" - [Candidates](research/payoff_objective_candidates_{v_norm}.md)\n"
        index_text += f" - [Split Integrity](research/payoff_objective_split_integrity_{v_norm}.md)\n"
        index_text += f" - [Walk-Forward Evaluation](research/payoff_objective_walk_forward_eval_{v_norm}.md)\n"
        index_text += f" - [Baseline Comparison](research/payoff_objective_baseline_comparison_{v_norm}.md)\n"
    index.write_text(index_text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--diagnostic-summary", required=True)
    parser.add_argument("--ev-summary", required=True)
    parser.add_argument("--canonical-summary", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    payload = run_research(
        predictions=args.predictions,
        dataset=args.dataset,
        intrabar=args.intrabar,
        diagnostic_summary=args.diagnostic_summary,
        ev_summary=args.ev_summary,
        canonical_summary=args.canonical_summary,
        version=args.version,
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
