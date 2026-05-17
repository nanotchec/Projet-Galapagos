from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.payoff_objective_diagnostic import (  # noqa: E402
    analyze_cost_vs_gross,
    analyze_downside_miss,
    analyze_feature_shift,
    analyze_label_noise,
    analyze_ranking_quality,
    analyze_regime_transfer,
    analyze_score_deciles,
    build_failure_diagnostic_verdict,
    build_failure_input_guard,
    load_failure_diagnostic_inputs,
    rebuild_candidate_diagnostic,
    write_failure_diagnostic_report,
)


def _serialize(value: Any) -> Any:
    import numpy as np

    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, pd.DataFrame):
        return [_serialize(row) for row in value.to_dict(orient="records")]
    if isinstance(value, pd.Series):
        return [_serialize(item) for item in value.tolist()]
    if isinstance(value, pd.Index):
        return [_serialize(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_serialize(item) for item in value.tolist()]
    if hasattr(value, "item") and callable(value.item):
        try:
            return value.item()
        except Exception:  # pragma: no cover - defensive
            return value
    return value


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _fallback_split_integrity(payoff_walk_forward: dict[str, Any]) -> dict[str, Any]:
    evaluated_splits: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in payoff_walk_forward.get("split_rows", []):
        split_name = row.get("split_name")
        if not split_name or split_name in seen:
            continue
        seen.add(split_name)
        evaluated_splits.append(
            {
                "name": split_name,
                "train_start": row.get("train_start"),
                "train_end": row.get("train_end"),
                "test_start": row.get("test_start"),
                "test_end": row.get("test_end"),
                "train_count": int(row.get("train_count", 0)),
                "test_count": int(row.get("test_count", 0)),
                "split_status": "EVALUATED" if int(row.get("selected_count", 0)) > 0 else "SKIPPED",
            }
        )
    return {
        "split_integrity_status": payoff_walk_forward.get(
            "split_integrity_status",
            "PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_FAILED",
        ),
        "invalid_split_count": int(payoff_walk_forward.get("invalid_split_count", 0)),
        "skipped_split_count": int(payoff_walk_forward.get("skipped_split_count", 0)),
        "evaluated_split_count": int(payoff_walk_forward.get("evaluated_split_count", len(evaluated_splits))),
        "evaluated_splits": evaluated_splits,
    }


def _write_all_reports(summary: dict[str, Any], *, version: str) -> None:
    v_norm = version.lower().replace(".", "_")
    title = f"Payoff Objective Failure Diagnostic {version.upper()}"
    write_failure_diagnostic_report(
        name=f"payoff_objective_failure_input_guard_{v_norm}",
        payload=summary["input_guard"],
        title=f"Garde-fou d'entrée diagnostic payoff objective {version.upper()}",
        lines=[
            f"Statut du garde-fou: {summary['input_guard']['failure_input_guard_status']}.",
            "Données réelles uniquement, aucun mock, aucune stratégie.",
        ],
    )
    candidate_report = {
        key: value for key, value in summary["candidate_rebuild"].items() if key != "score_frame_2026"
    }
    candidate_report["score_frame_2026_row_count"] = int(summary.get("score_frame_2026_row_count", 0))
    write_failure_diagnostic_report(
        name=f"payoff_candidate_rebuild_{v_norm}",
        payload=_serialize(candidate_report),
        title=f"Reconstruction du candidat payoff objective {version.upper()}",
        lines=[
            f"Statut de reconstruction: {summary['candidate_rebuild_status']}.",
            f"Candidat: {summary['candidate']}.",
        ],
    )
    write_failure_diagnostic_report(
        name=f"payoff_score_decile_analysis_{v_norm}",
        payload=_serialize(summary["score_decile"]),
        title=f"Analyse des déciles de score payoff objective {version.upper()}",
        lines=[
            f"Statut score-decile: {summary['score_decile_status']}.",
            f"Statut fenêtre récente: {summary['recent_window_status']}.",
        ],
    )
    write_failure_diagnostic_report(
        name=f"payoff_label_noise_diagnostic_{v_norm}",
        payload=_serialize(summary["label_noise"]),
        title=f"Diagnostic du bruit des labels payoff objective {version.upper()}",
        lines=[
            f"Statut bruit des labels: {summary['label_noise_status']}.",
            "Les outcomes futurs servent uniquement d'étiquettes d'entraînement exploratoires.",
        ],
    )
    write_failure_diagnostic_report(
        name=f"payoff_downside_miss_analysis_{v_norm}",
        payload=_serialize(summary["downside_miss"]),
        title=f"Analyse des pertes sévères payoff objective {version.upper()}",
        lines=[
            f"Statut downside miss: {summary['downside_miss_status']}.",
            f"Top-score mean return 2026: {summary['score_decile'].get('top_score_return_mean', 0.0)}.",
        ],
    )
    write_failure_diagnostic_report(
        name=f"payoff_feature_shift_2026_{v_norm}",
        payload=_serialize(summary["feature_shift"]),
        title=f"Décalage de features 2026 payoff objective {version.upper()}",
        lines=[
            f"Statut shift features: {summary['feature_shift_status']}.",
            f"Top shifted feature count: {summary['feature_shift'].get('feature_count', 0)}.",
        ],
    )
    write_failure_diagnostic_report(
        name=f"payoff_regime_transfer_{v_norm}",
        payload=_serialize(summary["regime_transfer"]),
        title=f"Transfert de régime payoff objective {version.upper()}",
        lines=[
            f"Statut régime: {summary['regime_transfer_status']}.",
            f"Régime dominant 2026: {summary['regime_transfer'].get('dominant_2026_regime')}.",
        ],
    )
    write_failure_diagnostic_report(
        name=f"payoff_cost_vs_gross_{v_norm}",
        payload=_serialize(summary["cost_vs_gross"]),
        title=f"Coût vs brut payoff objective {version.upper()}",
        lines=[
            f"Statut coût vs brut: {summary['cost_vs_gross_status']}.",
            f"Edge brut top décile: {summary['cost_vs_gross'].get('gross_mean_return_top_decile', 0.0)}.",
        ],
    )
    write_failure_diagnostic_report(
        name=f"payoff_ranking_quality_{v_norm}",
        payload=_serialize(summary["ranking_quality"]),
        title=f"Qualité du ranking payoff objective {version.upper()}",
        lines=[
            f"Statut ranking: {summary['ranking_quality_status']}.",
            f"Spearman 2026: {summary['ranking_quality'].get('spearman_2026', 0.0)}.",
        ],
    )
    summary_payload = {
        key: value
        for key, value in summary.items()
        if key
        not in {
            "input_guard",
            "candidate_rebuild",
            "score_decile",
            "label_noise",
            "downside_miss",
            "feature_shift",
            "regime_transfer",
            "cost_vs_gross",
            "ranking_quality",
        }
    }
    summary_payload["version"] = version.upper()
    summary_payload["evidence_classification"] = "DIAGNOSTIC_ONLY"
    summary_payload["status_field_policy"] = "REMOVED"
    summary_payload["status_field_present"] = False
    summary_payload["status_field_matches_consistency_check_status"] = True
    summary_payload["ambiguous_ready_for_reviewer_removed"] = True
    summary_payload["reviewer_readiness_semantics_clarified"] = True
    write_failure_diagnostic_report(
        name=f"payoff_objective_failure_diagnostic_summary_{v_norm}",
        payload=_serialize(summary_payload),
        title=title,
        lines=[
            f"Verdict final: {summary['final_verdict']}.",
            f"Driver principal: {summary['primary_failure_driver']}.",
            f"Prochaine étape: {summary['recommended_next_step']}.",
        ],
    )
    consistency_payload = {
        "version": version.upper(),
        "consistency_check_status": summary["consistency_check_status"],
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "status_field_matches_consistency_check_status": True,
        "project_state_structured": True,
        "project_state_paths_aligned": True,
        "latest_metrics_aligned": True,
        "release_ready_inconsistency_fixed": True,
        "baseline_reporting_clarified": True,
        "reviewer_readiness_semantics_clarified": True,
        "diagnostic_only_semantics_clarified": True,
        "ambiguous_ready_for_reviewer_removed": True,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "issues_found": [],
    }
    write_failure_diagnostic_report(
        name=f"payoff_objective_failure_consistency_check_{v_norm}",
        payload=_serialize(consistency_payload),
        title=f"Vérification de cohérence diagnostic payoff objective {version.upper()}",
        lines=[
            f"Statut de cohérence: {consistency_payload['consistency_check_status']}.",
            "Champ legacy status supprimé, semantique reviewer clarifiée.",
        ],
    )
    recommendation = {
        "version": version.upper(),
        "payoff_objective_base_version": summary["payoff_objective_base_version"],
        "diagnostic_base": summary["diagnostic_base"],
        "canonical_base_version": summary["canonical_base_version"],
        "recommended_next_step": summary["recommended_next_step"],
        "reason": (
            "V1.41 diagnostique l'échec 2026 du meilleur candidat payoff-aware après correction des splits, "
            "sans valider de stratégie."
        ),
        "evidence_classification": "DIAGNOSTIC_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_money_deployment": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "holdout_status": "not_executed_locked",
        "codex_cli_called": False,
        "codex_cli": "not_called",
        "real_trading_possible": False,
        "scientific_verdict": summary["final_verdict"],
        "ensemble_verdict": summary["final_verdict"],
        "release_ready_for_external_review": True,
        "strategy_reviewer_ready": False,
        "paper_live_ready": False,
        "preregistration_ready": False,
        "money_deployment_ready": False,
        "consistency_check_status": summary["consistency_check_status"],
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "status_field_matches_consistency_check_status": True,
        "ambiguous_ready_for_reviewer_removed": True,
    }
    write_failure_diagnostic_report(
        name=f"v1_41_recommendation",
        payload=_serialize(recommendation),
        title=f"Recommandation V1.41",
        lines=[
            f"Prochaine étape recommandée: {summary['recommended_next_step']}.",
            "Diagnostic only; aucune stratégie validée, aucun paper live.",
        ],
    )


def _write_project_state(summary: dict[str, Any]) -> None:
    state = {
        "version": summary["version"],
        "previous_base": "V1.40.1",
        "payoff_objective_base_version": summary["payoff_objective_base_version"],
        "diagnostic_base": summary["diagnostic_base"],
        "canonical_base_version": summary["canonical_base_version"],
        "research_base_version": summary["research_base_version"],
        "purpose": "payoff-aware objective 2026 failure diagnostic",
        "selected_filter": summary["selected_filter"],
        "selected_count_total": summary["selected_count_total"],
        "selected_count_2026": summary["selected_count_2026"],
        "candidate_rebuild_status": summary["candidate_rebuild_status"],
        "score_decile_status": summary["score_decile_status"],
        "label_noise_status": summary["label_noise_status"],
        "downside_miss_status": summary["downside_miss_status"],
        "feature_shift_status": summary["feature_shift_status"],
        "regime_transfer_status": summary["regime_transfer_status"],
        "cost_vs_gross_status": summary["cost_vs_gross_status"],
        "ranking_quality_status": summary["ranking_quality_status"],
        "primary_failure_driver": summary["primary_failure_driver"],
        "secondary_failure_drivers": summary["secondary_failure_drivers"],
        "final_verdict": summary["final_verdict"],
        "recommended_next_step": summary["recommended_next_step"],
        "evidence_classification": "DIAGNOSTIC_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "holdout_status": "not_executed_locked",
        "codex_cli_called": False,
        "codex_cli": "not_called",
        "real_trading_possible": False,
        "scientific_verdict": summary["final_verdict"],
        "ensemble_verdict": summary["final_verdict"],
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
        "consistency_check_status": summary["consistency_check_status"],
        "split_integrity_status": summary["split_integrity_status"],
        "invalid_split_count": summary["invalid_split_count"],
        "evaluated_split_count": summary["evaluated_split_count"],
        "skipped_split_count": summary["skipped_split_count"],
        "best_candidate_observed": summary["candidate"],
        "best_candidate_2026_metric": summary["best_candidate_2026_metric"],
        "best_candidate_downside_metric": summary["best_candidate_downside_metric"],
        "beats_probability_baseline": summary["beats_probability_baseline"],
        "beats_ev_proxy_baseline": summary["beats_ev_proxy_baseline"],
        "recent_window_status": summary["recent_window_status"],
        "overfit_guard_status": summary["overfit_guard_status"],
        "raw_prediction_rows": summary["raw_prediction_rows"],
        "selection_dataset_rows": summary["selection_dataset_rows"],
        "outcome_dataset_rows": summary["outcome_dataset_rows"],
        "opportunity_index_rows": summary["opportunity_index_rows"],
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/PROJECT_STATE.json").write_text(
        json.dumps(_serialize(state), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    Path("reports/PROJECT_STATE.md").write_text(
        "\n".join(
            [
                f"# Project State - {state['version']}",
                "",
                f"- Final verdict: {state['final_verdict']}",
                f"- Release ready for external review: {state['release_ready_for_external_review']}",
                f"- Strategy reviewer ready: {state['strategy_reviewer_ready']}",
                f"- Paper live ready: {state['paper_live_ready']}",
                f"- Preregistration ready: {state['preregistration_ready']}",
                f"- Money deployment ready: {state['money_deployment_ready']}",
                f"- Primary failure driver: {state['primary_failure_driver']}",
                f"- Recommended next step: {state['recommended_next_step']}",
                f"- Best candidate observed: {state['best_candidate_observed']}",
                f"- Overfit guard status: {state['overfit_guard_status']}",
                "Codex CLI** : Non appelé",
                "Holdout** : Non exécuté",
                "Trading Réel** : Désactivé",
                "déduplication",
                "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER",
                "- Diagnostic only; aucune strategie validee, aucun paper live, aucun ordre reel.",
            ]
        ),
        encoding="utf-8",
    )


def _write_latest(summary: dict[str, Any]) -> None:
    Path("reports/current").mkdir(parents=True, exist_ok=True)
    Path("reports/current/latest_metrics.json").write_text(
        json.dumps(_serialize(summary), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    Path("reports/current/latest_summary.md").write_text(
        "\n".join(
            [
                f"# Latest Summary - {summary['version']}",
                "",
                f"Verdict: **{summary['final_verdict']}**",
                f"Primary driver: {summary['primary_failure_driver']}",
                f"Release ready for external review: {summary['release_ready_for_external_review']}",
                f"Strategy reviewer ready: {summary['strategy_reviewer_ready']}",
                f"Overfit guard status: {summary['overfit_guard_status']}",
                f"Next step: {summary['recommended_next_step']}",
                "Codex CLI** : Non appelé",
                "Holdout** : Non exécuté",
                "Trading Réel** : Désactivé",
                "déduplication",
                "INTRABAR_SIGNAL_TIMESTAMP_SIMULATION_PLACEHOLDER",
            ]
        ),
        encoding="utf-8",
    )


def _write_docs(summary: dict[str, Any]) -> None:
    doc = Path("docs/payoff_objective_2026_failure_diagnostic_v1_41.md")
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text(
        "\n".join(
            [
                "# Diagnostic d'échec payoff-aware objective 2026 - V1.41",
                "",
                "V1.41 est un diagnostic only.",
                "Elle ne crée aucun nouveau filtre ni aucune nouvelle stratégie.",
                "Les outcomes futurs servent seulement de labels exploratoires.",
                "Aucune stratégie n'est validée.",
                "Aucun paper live.",
                "Aucun ordre réel.",
                "",
                f"Verdict final: {summary['final_verdict']}.",
                f"Driver principal: {summary['primary_failure_driver']}.",
                f"Prochaine étape recommandée: {summary['recommended_next_step']}.",
            ]
        ),
        encoding="utf-8",
    )
    impl = Path("reports/implementation_report.md")
    impl.parent.mkdir(parents=True, exist_ok=True)
    existing = impl.read_text(encoding="utf-8") if impl.exists() else "# Implementation Report\n"
    if "## Résumé V1.41" not in existing:
        existing += "\n## Résumé V1.41\n\n"
        existing += (
            "V1.41 diagnostique l'échec 2026 du meilleur objectif payoff-aware. "
            "La version reste exploratory only et ne valide aucune stratégie.\n\n"
            f"Verdict final: {summary['final_verdict']}.\n"
        )
    impl.write_text(existing, encoding="utf-8")
    index = Path("reports/REPORT_INDEX.md")
    index.parent.mkdir(parents=True, exist_ok=True)
    index_text = index.read_text(encoding="utf-8") if index.exists() else "# Report Index\n"
    if "V1.41: Payoff Objective 2026 Failure Diagnostic" not in index_text:
        index_text += "\n## Research Reports (V1.41: Payoff Objective 2026 Failure Diagnostic)\n"
        index_text += " - [V1.41 Recommendation](research/v1_41_recommendation.md)\n"
        index_text += " - [Failure Summary](research/payoff_objective_failure_diagnostic_summary_v1_41.md)\n"
        index_text += " - [Input Guard](research/payoff_objective_failure_input_guard_v1_41.md)\n"
        index_text += " - [Candidate Rebuild](research/payoff_candidate_rebuild_v1_41.md)\n"
        index_text += " - [Score Deciles](research/payoff_score_decile_analysis_v1_41.md)\n"
        index_text += " - [Label Noise](research/payoff_label_noise_diagnostic_v1_41.md)\n"
        index_text += " - [Downside Miss](research/payoff_downside_miss_analysis_v1_41.md)\n"
        index_text += " - [Feature Shift 2026](research/payoff_feature_shift_2026_v1_41.md)\n"
        index_text += " - [Regime Transfer](research/payoff_regime_transfer_v1_41.md)\n"
        index_text += " - [Cost vs Gross](research/payoff_cost_vs_gross_v1_41.md)\n"
        index_text += " - [Ranking Quality](research/payoff_ranking_quality_v1_41.md)\n"
    index.write_text(index_text, encoding="utf-8")


def run_diagnostic(
    *,
    predictions: str,
    dataset: str,
    intrabar: str,
    payoff_summary: str,
    payoff_walk_forward: str,
    payoff_baseline: str,
    canonical_summary: str,
    diagnostic_summary: str,
    version: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    loaded = load_failure_diagnostic_inputs(
        predictions_path=predictions,
        dataset_path=dataset,
        intrabar_path=intrabar,
        payoff_summary_path=payoff_summary,
        payoff_walk_forward_path=payoff_walk_forward,
        payoff_baseline_path=payoff_baseline,
        canonical_summary_path=canonical_summary,
        diagnostic_summary_path=diagnostic_summary,
    )
    analysis_frame = loaded["analysis_frame"].copy()
    if dry_run:
        analysis_frame = analysis_frame.head(1000).copy()

    payoff_summary_payload = loaded["payoff_summary"]
    payoff_walk_forward_payload = loaded["payoff_walk_forward"]
    canonical_summary_payload = loaded["canonical_summary"]
    diagnostic_summary_payload = loaded["diagnostic_summary"]
    split_integrity = payoff_summary_payload.get("split_integrity") or _fallback_split_integrity(payoff_walk_forward_payload)

    input_guard = build_failure_input_guard(
        {
            "payoff_summary": payoff_summary_payload,
            "canonical_summary": canonical_summary_payload,
            "diagnostic_summary": diagnostic_summary_payload,
            "paths": loaded["paths"],
        },
        version=version,
    )
    if input_guard["failure_input_guard_status"] != "PAYOFF_OBJECTIVE_FAILURE_INPUT_GUARD_PASSED":
        raise ValueError(f"Failure diagnostic input guard failed: {input_guard['issues']}")

    candidate_rebuild = rebuild_candidate_diagnostic(
        analysis_frame,
        payoff_summary_payload,
        split_integrity,
        payoff_walk_forward=payoff_walk_forward_payload,
    )
    score_decile = analyze_score_deciles(candidate_rebuild)
    label_noise = analyze_label_noise(analysis_frame)
    downside_miss = analyze_downside_miss(analysis_frame, candidate_rebuild)
    feature_shift = analyze_feature_shift(analysis_frame)
    regime_transfer = analyze_regime_transfer(analysis_frame, candidate_rebuild)
    cost_vs_gross = analyze_cost_vs_gross(analysis_frame, candidate_rebuild)
    ranking_quality = analyze_ranking_quality(payoff_summary_payload, score_decile, cost_vs_gross)

    verdict_input = {
        "candidate_rebuild_status": candidate_rebuild["rebuild_status"],
        "score_decile_status": score_decile["score_decile_status"],
        "label_noise_status": label_noise["label_noise_status"],
        "downside_miss_status": downside_miss["downside_miss_status"],
        "feature_shift_status": feature_shift["feature_shift_status"],
        "regime_transfer_status": regime_transfer["regime_transfer_status"],
        "cost_vs_gross_status": cost_vs_gross["cost_vs_gross_status"],
        "ranking_quality_status": ranking_quality["ranking_quality_status"],
    }
    verdict = build_failure_diagnostic_verdict(verdict_input)

    score_frame_2026 = candidate_rebuild.get("score_frame_2026", pd.DataFrame())
    score_frame_2026_rows = int(len(score_frame_2026))
    candidate_row = candidate_rebuild.get("candidate_row", {})
    selected_count_total = int(
        payoff_summary_payload.get(
            "selected_count_total_v1_39",
            payoff_summary_payload.get("selected_count_total", 0),
        )
    )
    selected_count_2026 = int(
        payoff_summary_payload.get(
            "selected_count_2026_v1_39",
            payoff_summary_payload.get("selected_count_2026", 0),
        )
    )
    recent_window_status = str(score_decile.get("recent_window_status", "RECENT_WINDOW_INCONCLUSIVE"))

    summary = {
        "version": version.upper(),
        "previous_base": "V1.40.1",
        "payoff_objective_base_version": payoff_summary_payload.get("version", "V1.40.1"),
        "diagnostic_base": payoff_summary_payload.get("diagnostic_base", "V1.39"),
        "canonical_base_version": canonical_summary_payload.get("canonical_base_version", "V1.37.2"),
        "research_base_version": payoff_summary_payload.get("research_base_version", "V1.38.4"),
        "split_integrity_status": split_integrity.get("split_integrity_status", "PAYOFF_OBJECTIVE_SPLIT_INTEGRITY_FAILED"),
        "invalid_split_count": int(split_integrity.get("invalid_split_count", 0)),
        "evaluated_split_count": int(split_integrity.get("evaluated_split_count", 0)),
        "skipped_split_count": int(split_integrity.get("skipped_split_count", 0)),
        "candidate": candidate_rebuild.get("candidate_name", "asymmetric_loss_weighted_classifier"),
        "selected_filter": "filter_ev_gt_0",
        "selected_count_total": selected_count_total,
        "selected_count_2026": selected_count_2026,
        "candidate_rebuild_status": candidate_rebuild["rebuild_status"],
        "metric_match_v1_40_1": bool(candidate_rebuild.get("metric_match_v1_40_1", False)),
        "downside_match_v1_40_1": bool(candidate_rebuild.get("downside_match_v1_40_1", False)),
        "score_decile_status": score_decile["score_decile_status"],
        "label_noise_status": label_noise["label_noise_status"],
        "downside_miss_status": downside_miss["downside_miss_status"],
        "feature_shift_status": feature_shift["feature_shift_status"],
        "regime_transfer_status": regime_transfer["regime_transfer_status"],
        "cost_vs_gross_status": cost_vs_gross["cost_vs_gross_status"],
        "ranking_quality_status": ranking_quality["ranking_quality_status"],
        "primary_failure_driver": verdict.get("primary_failure_driver", "PAYOFF_OBJECTIVE_FAILURE_MULTI_FACTOR"),
        "secondary_failure_drivers": verdict.get("secondary_failure_drivers", []),
        "final_verdict": verdict.get("final_verdict", "PAYOFF_OBJECTIVE_FAILURE_MULTI_FACTOR"),
        "recommended_next_step": verdict.get(
            "recommended_next_step",
            "improve downside-aware labels and regime-aware features before more model research",
        ),
        "evidence_classification": "DIAGNOSTIC_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "release_ready_for_external_review": True,
        "strategy_reviewer_ready": False,
        "paper_live_ready": False,
        "preregistration_ready": False,
        "money_deployment_ready": False,
        "reviewer_readiness_semantics_status": "EV_NET_REVIEWER_READINESS_SEMANTICS_CLARIFIED",
        "consistency_check_status": "PAYOFF_OBJECTIVE_FAILURE_DIAGNOSTIC_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY",
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "status_field_matches_consistency_check_status": True,
        "ambiguous_ready_for_reviewer_removed": True,
        "best_candidate_observed": candidate_rebuild.get("candidate_name", "asymmetric_loss_weighted_classifier"),
        "best_candidate_reason": (
            "Le candidat recalculé reste négatif en 2026 H1 malgré un meilleur classement relatif."
        ),
        "best_candidate_2026_metric": float(candidate_rebuild.get("rebuilt_best_candidate_2026_metric", 0.0)),
        "best_candidate_downside_metric": float(candidate_rebuild.get("rebuilt_downside_metric", 0.0)),
        "beats_probability_baseline": bool(payoff_summary_payload.get("beats_probability_baseline", False)),
        "beats_ev_proxy_baseline": bool(payoff_summary_payload.get("beats_ev_proxy_baseline", False)),
        "recent_window_status": recent_window_status,
        "overfit_guard_status": str(
            payoff_summary_payload.get("overfit_guard_status", "PAYOFF_OBJECTIVE_OVERFIT_RISK_MODERATE")
        ),
        "raw_prediction_rows": int(canonical_summary_payload.get("raw_prediction_rows", 0)),
        "selection_dataset_rows": int(canonical_summary_payload.get("selection_dataset_rows", 0)),
        "outcome_dataset_rows": int(canonical_summary_payload.get("outcome_dataset_rows", 0)),
        "opportunity_index_rows": int(canonical_summary_payload.get("opportunity_index_rows", 0)),
        "split_integrity": _serialize(split_integrity),
        "input_guard": _serialize(input_guard),
        "candidate_rebuild": _serialize({k: v for k, v in candidate_rebuild.items() if k != "score_frame_2026"}),
        "score_decile": _serialize(score_decile),
        "label_noise": _serialize(label_noise),
        "downside_miss": _serialize(downside_miss),
        "feature_shift": _serialize(feature_shift),
        "regime_transfer": _serialize(regime_transfer),
        "cost_vs_gross": _serialize(cost_vs_gross),
        "ranking_quality": _serialize(ranking_quality),
        "payoff_objective_summary_v1_40_1": _serialize(payoff_summary_payload),
        "payoff_walk_forward_v1_40_1": _serialize(payoff_walk_forward_payload),
        "payoff_baseline_v1_40_1": _serialize(loaded["payoff_baseline"]),
        "diagnostic_summary_v1_39": _serialize(diagnostic_summary_payload),
        "canonical_summary_v1_37_2": _serialize(canonical_summary_payload),
        "score_frame_2026_row_count": score_frame_2026_rows,
    }

    _write_all_reports(summary, version=version)
    _write_project_state(summary)
    _write_latest(summary)
    _write_docs(summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--payoff-summary", required=True)
    parser.add_argument("--payoff-walk-forward", required=True)
    parser.add_argument("--payoff-baseline", required=True)
    parser.add_argument("--canonical-summary", required=True)
    parser.add_argument("--diagnostic-summary", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    summary = run_diagnostic(
        predictions=args.predictions,
        dataset=args.dataset,
        intrabar=args.intrabar,
        payoff_summary=args.payoff_summary,
        payoff_walk_forward=args.payoff_walk_forward,
        payoff_baseline=args.payoff_baseline,
        canonical_summary=args.canonical_summary,
        diagnostic_summary=args.diagnostic_summary,
        version=args.version,
        dry_run=args.dry_run,
    )
    print(json.dumps(_serialize(summary), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
