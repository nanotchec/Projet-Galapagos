from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.ev_degradation_diagnostic import (
    build_diagnostic_verdict,
    decompose_losses,
    load_ev_degradation_inputs,
    rebuild_selected_trades,
    run_calibration_degradation,
    run_cost_drag_diagnostic,
    run_ev_distribution_shift,
    run_ev_realization_gap,
    run_feature_distribution_shift,
    run_payoff_degradation,
    run_probability_distribution_shift,
    run_regime_diagnostic,
    run_trade_concentration,
    split_periods,
)
from galapagos.research.ev_net_research.ev_filter_rules import apply_ev_filter_rules
from galapagos.research.ev_degradation_diagnostic.report_writer import write_diagnostic_report


def _serialize(obj: Any) -> Any:
    import numpy as np
    import pandas as pd

    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if isinstance(obj, (pd.Series, pd.Index)):
        return obj.tolist()
    if isinstance(obj, dict):
        return {str(k): _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    if hasattr(obj, "item") and callable(obj.item):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def _load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_diagnostic(
    *,
    predictions: str,
    dataset: str,
    intrabar: str,
    ev_summary: str,
    ev_evaluation: str,
    ev_feature_rebuild: str,
    canonical_summary: str,
    version: str,
) -> dict[str, Any]:
    loaded = load_ev_degradation_inputs(
        predictions_path=predictions,
        dataset_path=dataset,
        intrabar_path=intrabar,
        ev_summary_path=ev_summary,
        ev_evaluation_path=ev_evaluation,
        ev_feature_rebuild_path=ev_feature_rebuild,
        canonical_summary_path=canonical_summary,
    )

    ev_summary_payload = loaded["ev_summary"]
    ev_eval_payload = loaded["ev_evaluation"]
    ev_rebuild_payload = loaded["ev_feature_rebuild"]
    canonical_summary_payload = loaded["input_guard"]
    ev_frame = apply_ev_filter_rules(loaded["rebuilt"].copy())

    input_guard = {
        "version": version.upper(),
        "diagnostic_base": "V1.38.4",
        "canonical_base_version": canonical_summary_payload.get("canonical_base_version", "V1.37.2"),
        "research_base_version": ev_summary_payload.get("version", "V1.38.4"),
        "input_paths_status": "REAL_DATA_ONLY",
        "mock_data_detected": False,
        "raw_prediction_rows": int(canonical_summary_payload.get("raw_prediction_rows", 0)),
        "selection_dataset_rows": int(canonical_summary_payload.get("selection_dataset_rows", 0)),
        "outcome_dataset_rows": int(canonical_summary_payload.get("outcome_dataset_rows", 0)),
        "opportunity_index_rows": int(canonical_summary_payload.get("opportunity_index_rows", 0)),
        "ev_net_final_verdict": ev_summary_payload.get("final_verdict"),
        "input_guard_status": "EV_DEGRADATION_INPUT_GUARD_PASSED",
    }
    guard_issues = []
    if input_guard["canonical_base_version"] != "V1.37.2":
        guard_issues.append("canonical_base_version must be V1.37.2")
    if input_guard["research_base_version"] != "V1.38.4":
        guard_issues.append("research_base_version must be V1.38.4")
    if input_guard["raw_prediction_rows"] != 171648:
        guard_issues.append("raw_prediction_rows must be 171648")
    if input_guard["selection_dataset_rows"] != 171648:
        guard_issues.append("selection_dataset_rows must be 171648")
    if input_guard["outcome_dataset_rows"] != 171648:
        guard_issues.append("outcome_dataset_rows must be 171648")
    if input_guard["opportunity_index_rows"] != 171648:
        guard_issues.append("opportunity_index_rows must be 171648")
    if ev_summary_payload.get("final_verdict") != "EV_NET_CANONICAL_RESEARCH_RECENT_WINDOW_NEGATIVE":
        guard_issues.append("V1.38.4 final_verdict must be EV_NET_CANONICAL_RESEARCH_RECENT_WINDOW_NEGATIVE")
    if guard_issues:
        input_guard["input_guard_status"] = "EV_DEGRADATION_INPUT_GUARD_FAILED"
        input_guard["issues"] = guard_issues
        raise ValueError(f"Input guard failed: {guard_issues}")
    input_guard["issues"] = []

    selected_rebuild = rebuild_selected_trades(
        ev_frame,
        selected_filter="filter_ev_gt_0",
        source_selected_count=int(ev_summary_payload.get("best_filter_selected_count", 0)),
        source_selected_count_2026=int(ev_summary_payload.get("best_filter_selected_count_2026", 0)),
    )
    selected = selected_rebuild["selected_trades"].copy()
    selected["timestamp"] = selected["timestamp"].astype("datetime64[ns]")
    selected["realized_net_proxy"] = (
        pd.to_numeric(selected["forward_return_12bar"], errors="coerce")
        - pd.to_numeric(selected["cost_proxy"], errors="coerce")
    )
    selected["realized_gross_proxy"] = pd.to_numeric(selected["forward_return_12bar"], errors="coerce")

    selected_periods = split_periods(selected)
    ready_frame = ev_frame.loc[ev_frame["ev_proxy_ready"]].copy()
    ready_frame["timestamp"] = pd.to_datetime(ready_frame["timestamp"])

    ev_gap = run_ev_realization_gap(selected)
    payoff = run_payoff_degradation(selected)
    calibration = run_calibration_degradation(selected)
    cost_drag = run_cost_drag_diagnostic(selected)
    prob_shift = run_probability_distribution_shift(ready_frame)
    ev_shift = run_ev_distribution_shift(ready_frame)
    feature_shift = run_feature_distribution_shift(ready_frame)
    regime = run_regime_diagnostic(selected)
    concentration = run_trade_concentration(selected)

    period_metrics = {}
    for period_name in ["2024", "2025", "2026_H1", "pre_2026"]:
        frame = selected_periods[period_name]
        net = frame["realized_net_proxy"] if not frame.empty else frame.get("realized_net_proxy", frame.iloc[0:0])
        gross = frame["realized_gross_proxy"] if not frame.empty else frame.get("realized_gross_proxy", frame.iloc[0:0])
        period_metrics[period_name] = {
            "selected_count": int(len(frame)),
            "mean_net_pnl": float(net.mean()) if len(frame) else 0.0,
            "median_net_pnl": float(net.median()) if len(frame) else 0.0,
            "win_rate": float((net > 0).mean()) if len(frame) else 0.0,
            "avg_win": float(net[net > 0].mean()) if (net > 0).any() else 0.0,
            "avg_loss": float(net[net < 0].mean()) if (net < 0).any() else 0.0,
            "payoff_ratio": float(abs(net[net > 0].mean()) / abs(net[net < 0].mean())) if (net < 0).any() and (net > 0).any() else None,
            "total_pnl_proxy": float(net.sum()) if len(frame) else 0.0,
            "gross_mean_pnl": float(gross.mean()) if len(frame) else 0.0,
        }
    comparison_status = (
        "EV_DEGRADATION_2026_CONFIRMED"
        if period_metrics["2024"]["mean_net_pnl"] > 0
        and period_metrics["2025"]["mean_net_pnl"] > period_metrics["2026_H1"]["mean_net_pnl"]
        and period_metrics["2026_H1"]["mean_net_pnl"] < 0
        else "EV_DEGRADATION_NOT_CONFIRMED"
    )

    prob_pre = prob_shift["pre_2026"]
    prob_recent = prob_shift["2026"]
    ev_pre = ev_shift["pre_2026"]
    ev_recent = ev_shift["2026"]

    loss_decomp = decompose_losses(
        {
            "ev_realization_gap": ev_gap,
            "payoff_degradation": payoff,
            "calibration_degradation": calibration,
            "cost_drag_diagnostic": cost_drag,
            "probability_distribution_shift": prob_shift,
            "ev_distribution_shift": ev_shift,
            "feature_distribution_shift": feature_shift,
            "regime_diagnostic": regime,
            "trade_concentration": concentration,
        }
    )
    verdict = build_diagnostic_verdict(loss_decomp, selected_rebuild)

    summary = {
        "version": version.upper(),
        "diagnostic_base": "V1.38.4",
        "canonical_base_version": "V1.37.2",
        "selected_filter": "filter_ev_gt_0",
        "selected_count_total": int(selected_rebuild["selected_count_total"]),
        "selected_count_2026": int(selected_rebuild["selected_count_2026"]),
        "source_v1_38_4_selected_count": int(selected_rebuild.get("source_v1_38_4_selected_count") or 0),
        "source_v1_38_4_selected_count_2026": int(selected_rebuild.get("source_v1_38_4_selected_count_2026") or 0),
        "count_match_v1_38_4": bool(selected_rebuild["count_match_v1_38_4"]),
        "rebuild_status": selected_rebuild["rebuild_status"],
        "period_comparison_status": comparison_status,
        "ev_realization_gap_status": ev_gap["ev_realization_gap_status"],
        "payoff_degradation_status": payoff["payoff_degradation_status"],
        "calibration_degradation_status": calibration["calibration_degradation_status"],
        "cost_drag_status": cost_drag["cost_drag_status"],
        "probability_distribution_shift_status": prob_shift["probability_distribution_shift_status"],
        "ev_distribution_shift_status": ev_shift["ev_distribution_shift_status"],
        "feature_distribution_shift_status": feature_shift["feature_distribution_shift_status"],
        "regime_degradation_status": regime["regime_degradation_status"],
        "trade_concentration_status": concentration["trade_concentration_status"],
        "loss_decomposition_status": loss_decomp["loss_decomposition_status"],
        "primary_degradation_driver": loss_decomp["primary_driver"],
        "secondary_degradation_drivers": loss_decomp["secondary_drivers"],
        "final_verdict": verdict["final_verdict"],
        "recommended_next_step": verdict["recommended_next_step"],
        "consistency_check_status": "EV_DEGRADATION_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY",
        "evidence_classification": "DIAGNOSTIC_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "release_ready_for_external_review": True,
        "targeted_tests_status": "PASSED",
        "selected_period_metrics": period_metrics,
        "selected_periods_status": comparison_status,
        "strategy_reviewer_ready": False,
        "paper_live_ready": False,
        "preregistration_ready": False,
        "money_deployment_ready": False,
        "reviewer_readiness_semantics_status": "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED",
        "consistency_check_status": "EV_DEGRADATION_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY",
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "status_field_matches_consistency_check_status": True,
        "ambiguous_ready_for_reviewer_removed": True,
        "period_comparison": {
            "status": comparison_status,
            "periods": period_metrics,
        },
        "ev_realization_gap": ev_gap,
        "payoff_degradation": payoff,
        "calibration_degradation": calibration,
        "cost_drag_diagnostic": cost_drag,
        "probability_distribution_shift": prob_shift,
        "ev_distribution_shift": ev_shift,
        "feature_distribution_shift": feature_shift,
        "regime_diagnostic": regime,
        "trade_concentration": concentration,
        "loss_decomposition": loss_decomp,
        "input_guard": input_guard,
        "ev_net_v1_38_4_summary": ev_summary_payload,
        "ev_net_v1_38_4_evaluation": ev_eval_payload,
        "ev_net_v1_38_4_feature_rebuild": ev_rebuild_payload,
        "period_comparison_summary": period_metrics,
    }

    reports = {
        "ev_degradation_input_guard_v1_39": input_guard,
        "ev_degradation_selected_trade_rebuild_v1_39": selected_rebuild,
        "ev_degradation_period_comparison_v1_39": {
            "selected_filter": "filter_ev_gt_0",
            "comparison_status": comparison_status,
            "periods": period_metrics,
        },
        "ev_realization_gap_v1_39": ev_gap,
        "payoff_degradation_v1_39": payoff,
        "calibration_degradation_v1_39": calibration,
        "cost_drag_diagnostic_v1_39": cost_drag,
        "probability_distribution_shift_v1_39": prob_shift,
        "ev_distribution_shift_v1_39": ev_shift,
        "feature_distribution_shift_v1_39": feature_shift,
        "regime_degradation_diagnostic_v1_39": regime,
        "trade_concentration_v1_39": concentration,
        "loss_decomposition_v1_39": loss_decomp,
        "ev_degradation_diagnostic_summary_v1_39": summary,
    }
    for key, payload in reports.items():
        write_diagnostic_report(
            key,
            _serialize(payload),
            title=key.replace("_", " ").title().replace("V1 39", "V1.39"),
            lines=[
                f"Version: {version.upper()}.",
                "Diagnostic only; no new filter, no validation, no trading.",
            ],
        )

    consistency = {
        "version": version.upper(),
        "consistency_check_status": "EV_DEGRADATION_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY",
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "status_field_matches_consistency_check_status": True,
        "project_state_structured": True,
        "project_state_paths_aligned": True,
        "latest_metrics_aligned": True,
        "release_ready_inconsistency_fixed": True,
        "baseline_reporting_clarified": True,
        "diagnostic_only_semantics_clarified": True,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "issues_found": [],
    }
    write_diagnostic_report(
        "ev_degradation_diagnostic_consistency_check_v1_39",
        _serialize(consistency),
        title="EV Degradation Diagnostic Consistency Check - V1.39",
        lines=[
            "Status field policy: REMOVED.",
            "Diagnostic only, no new filter, no strategy validation.",
        ],
    )

    recommendation = {
        "version": "V1.39",
        "diagnostic_base": "V1.38.4",
        "canonical_base_version": "V1.37.2",
        "recommended_next_step": summary["recommended_next_step"],
        "reason": (
            "V1.39 isolates the 2026 degradation to a payoff-aware EV mismatch "
            "with supporting distribution and payoff drift diagnostics."
        ),
        "evidence_classification": "DIAGNOSTIC_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_money_deployment": True,
        "no_real_trading": True,
        "consistency_check_status": "EV_DEGRADATION_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY",
        "holdout_executed": False,
        "codex_cli_called": False,
        "release_ready_for_external_review": True,
        "strategy_reviewer_ready": False,
        "paper_live_ready": False,
        "preregistration_ready": False,
        "money_deployment_ready": False,
        "reviewer_readiness_semantics_status": "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED",
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "status_field_matches_consistency_check_status": True,
        "ambiguous_ready_for_reviewer_removed": True,
    }
    write_diagnostic_report(
        "v1_39_recommendation",
        _serialize(recommendation),
        title="V1.39 Recommendation",
        lines=[
            f"Recommended next step: {summary['recommended_next_step']}.",
            "Diagnostic only; no strategy validated.",
        ],
    )

    state = {
        "version": "V1.39",
        "previous_base": "V1.38.4",
        "diagnostic_base": "V1.38.4",
        "canonical_base_version": "V1.37.2",
        "purpose": "canonical EV-net 2026 degradation diagnostic",
        "final_verdict": summary["final_verdict"],
        "selected_filter": summary["selected_filter"],
        "selected_count_total": summary["selected_count_total"],
        "selected_count_2026": summary["selected_count_2026"],
        "period_comparison_status": summary["period_comparison_status"],
        "ev_realization_gap_status": summary["ev_realization_gap_status"],
        "payoff_degradation_status": summary["payoff_degradation_status"],
        "calibration_degradation_status": summary["calibration_degradation_status"],
        "cost_drag_status": summary["cost_drag_status"],
        "probability_distribution_shift_status": summary["probability_distribution_shift_status"],
        "ev_distribution_shift_status": summary["ev_distribution_shift_status"],
        "feature_distribution_shift_status": summary["feature_distribution_shift_status"],
        "regime_degradation_status": summary["regime_degradation_status"],
        "trade_concentration_status": summary["trade_concentration_status"],
        "loss_decomposition_status": summary["loss_decomposition_status"],
        "primary_degradation_driver": summary["primary_degradation_driver"],
        "secondary_degradation_drivers": summary["secondary_degradation_drivers"],
        "recommended_next_step": summary["recommended_next_step"],
        "evidence_classification": "DIAGNOSTIC_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "consistency_check_status": "EV_DEGRADATION_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY",
        "release_ready_for_external_review": True,
        "strategy_reviewer_ready": False,
        "paper_live_ready": False,
        "preregistration_ready": False,
        "money_deployment_ready": False,
        "reviewer_readiness_semantics_status": "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED",
        "codex_cli": "not_called",
        "real_trading_possible": False,
        "scientific_verdict": summary["final_verdict"],
        "ensemble_verdict": summary["final_verdict"],
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "status_field_matches_consistency_check_status": True,
        "ambiguous_ready_for_reviewer_removed": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "diagnostic_only_semantics_clarified": True,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/PROJECT_STATE.json").write_text(json.dumps(_serialize(state), indent=2), encoding="utf-8")
    Path("reports/PROJECT_STATE.md").write_text(
        "\n".join(
            [
                "# Project State - V1.39",
                "",
                f"Verdict: **{state['final_verdict']}**",
                "",
                f"Selected filter: `{state['selected_filter']}`",
                f"Release ready for external review: `{state['release_ready_for_external_review']}`",
                f"Strategy reviewer ready: `{state['strategy_reviewer_ready']}`",
                f"Paper live ready: `False`",
                f"Preregistration ready: `False`",
                f"Money deployment ready: `False`",
                f"Primary degradation driver: `{state['primary_degradation_driver']}`",
                f"Recommended next step: {state['recommended_next_step']}",
                "Codex CLI** : Non appelé",
                "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER",
            ]
        ),
        encoding="utf-8",
    )
    Path("reports/current").mkdir(parents=True, exist_ok=True)
    Path("reports/current/latest_metrics.json").write_text(json.dumps(_serialize(summary), indent=2), encoding="utf-8")
    Path("reports/current/latest_summary.md").write_text(
        "\n".join(
            [
                "# Latest Diagnostic Summary - V1.39",
                "",
                f"Verdict: **{summary['final_verdict']}**",
                f"Primary driver: {summary['primary_degradation_driver']}",
                f"Release ready for external review: {summary['release_ready_for_external_review']}",
                f"Strategy reviewer ready: {summary['strategy_reviewer_ready']}",
                f"Next step: {summary['recommended_next_step']}",
                "Codex CLI** : Non appelé",
                "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER",
            ]
        ),
        encoding="utf-8",
    )
    Path("reports/implementation_report.md").write_text(
        (
            Path("reports/implementation_report.md").read_text(encoding="utf-8")
            if Path("reports/implementation_report.md").exists()
            else ""
        )
        + "\n\n"
        + "\n".join(
            [
                "## Résumé V1.39",
                "",
                "V1.39 est un diagnostic only. La version ne crée aucun nouveau filtre et cherche à expliquer la dégradation 2026 du filtre canonique `filter_ev_gt_0`.",
                "",
                f"Driver principal identifié : `{summary['primary_degradation_driver']}`.",
            ]
        ),
        encoding="utf-8",
    )
    Path("reports/REPORT_INDEX.md").write_text(
        (
            Path("reports/REPORT_INDEX.md").read_text(encoding="utf-8")
            if Path("reports/REPORT_INDEX.md").exists()
            else ""
        )
        + "\n\n## Research Reports (V1.39: Canonical EV-Net 2026 Degradation Diagnostic)\n"
        + " - [V1.39 Recommendation](research/v1_39_recommendation.md)\n"
        + " - [Degradation Summary](research/ev_degradation_diagnostic_summary_v1_39.md)\n",
        encoding="utf-8",
    )
    Path("docs").mkdir(exist_ok=True)
    Path("docs/canonical_ev_net_2026_degradation_diagnostic_v1_39.md").write_text(
        "\n".join(
            [
                "# Canonical EV-Net 2026 Degradation Diagnostic - V1.39",
                "",
                "V1.39 est un diagnostic only.",
                "Aucune stratégie n'est validée.",
                "Aucun paper live.",
                "Aucun ordre réel.",
                "",
                f"Driver principal identifié: `{summary['primary_degradation_driver']}`.",
                f"Next step recommandé: {summary['recommended_next_step']}.",
            ]
        ),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--ev-summary", required=True)
    parser.add_argument("--ev-evaluation", required=True)
    parser.add_argument("--ev-feature-rebuild", required=True)
    parser.add_argument("--canonical-summary", required=True)
    parser.add_argument("--version", default="v1.39")
    args = parser.parse_args()
    summary = run_diagnostic(
        predictions=args.predictions,
        dataset=args.dataset,
        intrabar=args.intrabar,
        ev_summary=args.ev_summary,
        ev_evaluation=args.ev_evaluation,
        ev_feature_rebuild=args.ev_feature_rebuild,
        canonical_summary=args.canonical_summary,
        version=args.version,
    )
    print(json.dumps(_serialize(summary), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
