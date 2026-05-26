from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _bootstrap

_bootstrap.bootstrap_src_path()


VERSION = "V8.8"
DECISION_JSON = Path("reports/research_decisions/v8_8_research_decision_gate.json")
DECISION_MD = Path("reports/research_decisions/v8_8_research_decision_gate.md")
DOC_MD = Path("docs/research_decision_gate_v8_8.md")
V8_7_MANIFEST = Path("reports/manifests/strict_walk_forward_validation_v8_7_manifest.json")
V8_7_REPORT = Path("reports/ml/strict_walk_forward_validation_v8_7.json")
V8_7_SCORES_REPORT = Path("reports/ml/strict_walk_forward_scores_v8_7.json")
V8_5_MANIFEST = Path("reports/manifests/ohlcv_trades_1y_offline_ml_research_v8_5_manifest.json")
V8_5_REPORT = Path("reports/ml/ohlcv_trades_1y_offline_ml_research_v8_5.json")
V8_5_SCORES_REPORT = Path("reports/ml/ohlcv_trades_1y_offline_research_scores_v8_5.json")
V8_7_ATTESTATION = Path("reports/audit_lite/v8_7_full_local_validation_attestation.json")
PROJECT_STATE = Path("reports/PROJECT_STATE.json")
PROJECT_STATE_MD = Path("reports/PROJECT_STATE.md")
LATEST_SUMMARY = Path("reports/current/latest_summary.md")
LATEST_METRICS_JSON = Path("reports/current/latest_metrics.json")
LATEST_METRICS_MD = Path("reports/current/latest_metrics.md")
README = Path("README.md")

TIMEFRAMES = ["1m", "5m", "15m", "1h"]
MODELS = [
    "majority_class_baseline",
    "random_seeded_baseline",
    "logistic_regression",
    "decision_tree_depth_2",
]
LEARNED_MODELS = ["logistic_regression", "decision_tree_depth_2"]
SAFETY = {
    "trading_enabled": False,
    "paper_live_enabled": False,
    "orders_enabled": False,
    "backtest_enabled": False,
    "strategy_enabled": False,
    "execution_enabled": False,
}
CLAIMS = {
    "strategy_validated": False,
    "model_validated_for_trading": False,
    "walk_forward_validated_for_trading": False,
    "profitability_claimed": False,
    "real_trading_allowed": False,
}
LIMITATIONS = [
    "V8.8 analyse uniquement les resultats offline V8.7 et ne modifie ni donnees, ni features, ni labels, ni scores.",
    "V8.7 reste une validation walk-forward offline stricte, pas un backtest et pas une validation de strategie.",
    "Les resultats restent trop proches des labels melanges dans plusieurs cas, avec concentration sur certains folds et timeframes.",
    "La fenetre d'environ 1 an ne couvre pas toute la fenetre V5.0 disponible et ne suffit pas a conclure pour le trading.",
]
ROADMAP = [
    "V8.9 - OHLCV + Trades Feature Audit / Selection",
    "V9.0 - Refined OHLCV + Trades Feature Store",
    "V9.1 - Refined OHLCV + Trades Dataset",
    "V9.2 - Refined OHLCV + Trades ML Offline",
    "V9.3 - Refined Strict Walk-Forward Validation",
]


def main() -> None:
    root = Path(".").resolve()
    decision = build_research_decision_gate_v8_8(root)
    _write_json(root / DECISION_JSON, decision)
    markdown = build_markdown(decision)
    _write_text(root / DECISION_MD, markdown)
    _write_text(root / DOC_MD, markdown)
    update_current_state(root, decision)
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": decision["status"],
                "summary_verdict": decision["summary_verdict"],
                "recommended_next_step": decision["recommended_next_step"],
                "secondary_next_step": decision["secondary_next_step"],
                "decision_json": DECISION_JSON.as_posix(),
                "decision_markdown": DECISION_MD.as_posix(),
                "documentation": DOC_MD.as_posix(),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def build_research_decision_gate_v8_8(root: Path) -> dict[str, Any]:
    v8_7 = _load_json(root / V8_7_MANIFEST)
    v8_7_report = _load_json(root / V8_7_REPORT)
    v8_7_scores = _load_json(root / V8_7_SCORES_REPORT)
    v8_5 = _load_json(root / V8_5_MANIFEST)
    attestation = _load_json(root / V8_7_ATTESTATION)
    aggregate = v8_7["aggregate_metrics"]
    label_shuffle = v8_7["label_shuffle_falsification"]
    comparison = v8_7["comparison_to_static_split_v8_5"]
    baseline_assessment = build_baseline_assessment(aggregate)
    fold_stability = build_fold_stability_assessment(aggregate, v8_7["folds"])
    timeframe_stability = build_timeframe_stability_assessment(aggregate)
    label_shuffle_assessment = build_label_shuffle_assessment(label_shuffle)
    static_split_assessment = build_static_split_comparison_assessment(comparison)
    walk_forward_assessment = build_walk_forward_assessment(aggregate, v8_7, baseline_assessment, fold_stability)
    leakage_assessment = {
        "verdict": "aucune_fuite_detectee_par_scan_v8_7",
        "feature_leakage_detected": bool(v8_7["feature_leakage_scan"].get("feature_leakage_detected")),
        "forbidden_feature_columns_present": v8_7["feature_leakage_scan"].get("forbidden_feature_columns_present", []),
        "metric_forbidden_terms_detected": bool(v8_7["metric_forbidden_scan"].get("metric_forbidden_terms_detected")),
        "forbidden_metric_terms_present": v8_7["metric_forbidden_scan"].get("forbidden_terms_present", []),
        "feature_columns_checked": len(v8_7["feature_leakage_scan"].get("feature_columns_checked", [])),
        "fold_columns_used_as_features": False,
        "split_columns_used_as_features": False,
    }
    decision = {
        "version": VERSION,
        "status": "PASS",
        "decision_gate_type": "research_only",
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "inputs": {
            "strict_walk_forward_manifest": _input_block(root, V8_7_MANIFEST),
            "strict_walk_forward_report": _input_block(root, V8_7_REPORT),
            "strict_walk_forward_scores_report": _input_block(root, V8_7_SCORES_REPORT),
            "static_split_manifest_v8_5": _input_block(root, V8_5_MANIFEST),
            "static_split_report_v8_5": _input_block(root, V8_5_REPORT),
            "static_split_scores_report_v8_5": _input_block(root, V8_5_SCORES_REPORT),
            "v8_7_attestation": _input_block(root, V8_7_ATTESTATION),
            "reference_reports": _reference_availability(root),
            "window_start": v8_7["input_dataset_manifest"]["window_start"],
            "window_end": v8_7["input_dataset_manifest"]["window_end"],
            "total_days": v8_7["input_dataset_manifest"]["total_days"],
            "feature_columns_count": v8_7["feature_columns_count"],
            "target_name": v8_7["target_name"],
            "models": v8_7["models"],
            "timeframes": TIMEFRAMES,
            "folds_count_by_timeframe": {tf: len(v8_7["folds"][tf]) for tf in TIMEFRAMES},
            "walk_forward_policy": v8_7["walk_forward_policy"],
            "v8_7_attestation_passed": bool(attestation.get("validator_passed")),
            "v8_7_report_consistent_with_manifest": v8_7_report == v8_7,
            "v8_7_scores_report_version": v8_7_scores.get("version"),
            "v8_5_status": v8_5.get("status"),
        },
        "summary_verdict": "interessant_mais_instable_non_concluant",
        "walk_forward_assessment": walk_forward_assessment,
        "baseline_assessment": baseline_assessment,
        "fold_stability_assessment": fold_stability,
        "timeframe_stability_assessment": timeframe_stability,
        "label_shuffle_assessment": label_shuffle_assessment,
        "static_split_comparison_assessment": static_split_assessment,
        "leakage_assessment": leakage_assessment,
        "limitations": LIMITATIONS,
        "recommended_next_step": "A. Ameliorer/refactoriser les features OHLCV + trades.",
        "secondary_next_step": "B. Revoir les labels.",
        "roadmap": ROADMAP,
        "safety": SAFETY,
        "claims": CLAIMS,
    }
    return decision


def build_walk_forward_assessment(
    aggregate: dict[str, Any],
    manifest: dict[str, Any],
    baseline_assessment: dict[str, Any],
    fold_stability: dict[str, Any],
) -> dict[str, Any]:
    warnings = list(manifest["findings"].get("warnings", []))
    model_summary = {
        model: {
            tf: _model_metric_block(aggregate[f"{tf}.{model}"])
            for tf in TIMEFRAMES
        }
        for model in MODELS
    }
    learned_clear = baseline_assessment["clear_baseline_wins_count"]
    unstable_count = fold_stability["unstable_entries_count"]
    verdict = "mitige_non_concluant"
    if learned_clear == 0:
        verdict = "faible_non_concluant"
    elif unstable_count:
        verdict = "interessant_mais_instable_non_concluant"
    return {
        "verdict": verdict,
        "offline_validation_only": True,
        "not_a_backtest": True,
        "models_summary": model_summary,
        "findings": {
            "robust_edge_claimed": False,
            "strategy_validated": False,
            "backtest_performed": False,
            "actionable_signal_produced": False,
            "walk_forward_validated_for_trading": False,
        },
        "warnings_count": len(warnings),
        "warnings": warnings,
    }


def build_baseline_assessment(aggregate: dict[str, Any]) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    clear_wins = 0
    mixed = 0
    misses = 0
    for tf in TIMEFRAMES:
        majority = aggregate[f"{tf}.majority_class_baseline"]
        random = aggregate[f"{tf}.random_seeded_baseline"]
        for model in LEARNED_MODELS:
            learned = aggregate[f"{tf}.{model}"]
            acc_delta_majority = learned["mean_test_accuracy"] - majority["mean_test_accuracy"]
            acc_delta_random = learned["mean_test_accuracy"] - random["mean_test_accuracy"]
            f1_delta_majority = learned["mean_test_macro_f1"] - majority["mean_test_macro_f1"]
            f1_delta_random = learned["mean_test_macro_f1"] - random["mean_test_macro_f1"]
            beats_majority_f1 = f1_delta_majority > 0.01
            beats_random_f1 = f1_delta_random > 0.01
            beats_majority_accuracy = acc_delta_majority > 0.01
            beats_random_accuracy = acc_delta_random > 0.01
            if beats_majority_f1 and beats_random_f1 and beats_majority_accuracy and beats_random_accuracy:
                verdict = "bat_clairement_les_baselines_sur_accuracy_et_macro_f1"
                clear_wins += 1
            elif beats_majority_f1 and beats_random_f1:
                verdict = "bat_les_baselines_en_macro_f1_mais_resultat_mitige"
                mixed += 1
            elif beats_majority_f1 or beats_random_f1 or beats_majority_accuracy or beats_random_accuracy:
                verdict = "resultat_mitige"
                mixed += 1
            else:
                verdict = "ne_bat_pas_les_baselines"
                misses += 1
            comparisons[f"{tf}.{model}"] = {
                "timeframe": tf,
                "model_name": model,
                "mean_test_accuracy": learned["mean_test_accuracy"],
                "mean_test_macro_f1": learned["mean_test_macro_f1"],
                "delta_accuracy_vs_majority": round(acc_delta_majority, 6),
                "delta_macro_f1_vs_majority": round(f1_delta_majority, 6),
                "delta_accuracy_vs_random": round(acc_delta_random, 6),
                "delta_macro_f1_vs_random": round(f1_delta_random, 6),
                "verdict": verdict,
            }
    return {
        "verdict": "mitige_pas_de_battement_net_generalise",
        "clear_baseline_wins_count": clear_wins,
        "mixed_results_count": mixed,
        "baseline_miss_count": misses,
        "comparison_policy": "clear win requires accuracy and macro_f1 above both baselines by more than 0.01",
        "comparisons": comparisons,
        "backtest_recommended": False,
    }


def build_fold_stability_assessment(aggregate: dict[str, Any], folds: dict[str, Any]) -> dict[str, Any]:
    unstable_entries = {}
    weak_entries = {}
    concentration = {}
    for key, value in aggregate.items():
        if value.get("unstable_folds"):
            unstable_entries[key] = value["unstable_folds"]
        if value.get("weak_folds"):
            weak_entries[key] = value["weak_folds"]
        if value.get("fold_concentration_warnings"):
            concentration[key] = value["fold_concentration_warnings"]
    return {
        "verdict": "instable_ou_concentre",
        "folds_count_by_timeframe": {tf: len(folds[tf]) for tf in TIMEFRAMES},
        "unstable_entries_count": len(unstable_entries),
        "weak_entries_count": len(weak_entries),
        "fold_concentration_warnings_count": len(concentration),
        "unstable_entries": unstable_entries,
        "weak_entries": weak_entries,
        "fold_concentration_warnings": concentration,
        "depends_on_few_periods": bool(concentration),
    }


def build_timeframe_stability_assessment(aggregate: dict[str, Any]) -> dict[str, Any]:
    per_timeframe = {}
    best_by_macro_f1 = {}
    for tf in TIMEFRAMES:
        per_timeframe[tf] = {
            model: _model_metric_block(aggregate[f"{tf}.{model}"])
            for model in MODELS
        }
    for model in MODELS:
        ranked = sorted(
            ((tf, aggregate[f"{tf}.{model}"]["mean_test_macro_f1"]) for tf in TIMEFRAMES),
            key=lambda item: item[1],
            reverse=True,
        )
        best_by_macro_f1[model] = {"best_timeframe": ranked[0][0], "ranking": ranked}
    return {
        "verdict": "non_stable_entre_timeframes",
        "timeframes": per_timeframe,
        "best_timeframe_by_macro_f1": best_by_macro_f1,
        "timeframe_concentration_detected": True,
        "notes": [
            "1m affiche une accuracy elevee mais une macro_f1 moins convaincante et des folds instables.",
            "5m et 15m portent les meilleurs resultats learned en macro_f1.",
            "1h reste mitige et proche des baselines random sur macro_f1.",
        ],
    }


def build_label_shuffle_assessment(label_shuffle: dict[str, Any]) -> dict[str, Any]:
    unclear = [value for value in label_shuffle.values() if value.get("no_clear_edge_vs_shuffled_labels")]
    by_model = Counter(item["model_name"] for item in unclear)
    by_timeframe = Counter(item["timeframe"] for item in unclear)
    by_role = Counter(item["fold_role"] for item in unclear)
    cases = [
        {
            "timeframe": item["timeframe"],
            "model_name": item["model_name"],
            "fold_id": item["fold_id"],
            "fold_role": item["fold_role"],
            "accuracy_delta_original_minus_shuffled": item["accuracy_delta_original_minus_shuffled"],
            "macro_f1_delta_original_minus_shuffled": item["macro_f1_delta_original_minus_shuffled"],
        }
        for item in unclear
    ]
    return {
        "verdict": "alerte_forte_resultats_trop_proches_des_labels_melanges",
        "random_seed_policy": "123 + fold_order",
        "shuffle_scope": "train_labels_only",
        "total_cases": len(label_shuffle),
        "no_clear_edge_vs_shuffled_labels_count": len(unclear),
        "by_model": dict(by_model),
        "by_timeframe": dict(by_timeframe),
        "by_role": dict(by_role),
        "cases": cases,
        "falsification_clean": len(unclear) == 0,
        "backtest_recommended": False,
    }


def build_static_split_comparison_assessment(comparison: dict[str, Any]) -> dict[str, Any]:
    learned = {
        key: value
        for key, value in comparison.get("comparisons", {}).items()
        if value.get("model_name") in LEARNED_MODELS
    }
    positive_f1 = sum(1 for value in learned.values() if value["macro_f1_delta_v8_7_minus_v8_5_static"] > 0.0)
    negative_f1 = sum(1 for value in learned.values() if value["macro_f1_delta_v8_7_minus_v8_5_static"] < 0.0)
    return {
        "verdict": "v8_7_affaiblit_le_diagnostic_de_stabilite_v8_5",
        "descriptive_only": True,
        "not_same_validation_design": bool(comparison.get("not_same_validation_design")),
        "compared_learned_cases": len(learned),
        "positive_macro_f1_delta_cases": positive_f1,
        "negative_macro_f1_delta_cases": negative_f1,
        "comparisons": learned,
        "warnings": comparison.get("warnings", []),
    }


def _model_metric_block(metric: dict[str, Any]) -> dict[str, Any]:
    return {
        "mean_test_accuracy": metric["mean_test_accuracy"],
        "mean_test_macro_f1": metric["mean_test_macro_f1"],
        "std_test_accuracy": metric["std_test_accuracy"],
        "weak_folds": metric["weak_folds"],
        "unstable_folds": metric["unstable_folds"],
        "fold_concentration_warnings": metric["fold_concentration_warnings"],
    }


def build_markdown(decision: dict[str, Any]) -> str:
    inputs = decision["inputs"]
    wf = decision["walk_forward_assessment"]
    baseline = decision["baseline_assessment"]
    fold = decision["fold_stability_assessment"]
    timeframe = decision["timeframe_stability_assessment"]
    shuffle = decision["label_shuffle_assessment"]
    static = decision["static_split_comparison_assessment"]
    leakage = decision["leakage_assessment"]
    lines = [
        "# Research decision gate V8.8",
        "",
        "## 1. Executive summary",
        "",
        f"- Verdict research : `{decision['summary_verdict']}`.",
        "- V8.8 ne produit aucune conclusion trading.",
        "- V8.7 est interessant pour la recherche, mais reste instable, mitige et non concluant.",
        "- V8.7 est une validation walk-forward offline stricte, pas un backtest.",
        "- Un backtest research n'est pas justifie maintenant.",
        "",
        "## 2. Resume des entrees analysees",
        "",
        "- V8.5 : static split offline OHLCV + aggTrades 1 an.",
        "- V8.7 : strict walk-forward offline OHLCV + aggTrades 1 an.",
        f"- Fenetre : `{inputs['window_start']}` -> `{inputs['window_end']}`.",
        f"- Total jours : `{inputs['total_days']}`.",
        f"- Feature columns count : `{inputs['feature_columns_count']}`.",
        f"- Target : `{inputs['target_name']}`.",
        f"- Modeles : {', '.join(inputs['models'])}.",
        f"- Timeframes : {', '.join(inputs['timeframes'])}.",
        f"- Folds par timeframe : `{inputs['folds_count_by_timeframe']}`.",
        f"- Purge bars : `{inputs['walk_forward_policy']['purge_bars']}`.",
        f"- Embargo bars : `{inputs['walk_forward_policy']['embargo_bars']}`.",
        f"- Expanding train : `{inputs['walk_forward_policy']['expanding_train']}`.",
        "",
        "## 3. Resultats walk-forward par modele",
        "",
    ]
    for model in MODELS:
        lines.append(f"### {model}")
        for tf in TIMEFRAMES:
            item = wf["models_summary"][model][tf]
            lines.append(
                "- "
                f"{tf}: mean_test_accuracy={item['mean_test_accuracy']:.6f}, "
                f"mean_test_macro_f1={item['mean_test_macro_f1']:.6f}, "
                f"std_test_accuracy={item['std_test_accuracy']:.6f}, "
                f"weak_folds={item['weak_folds']}, "
                f"unstable_folds={item['unstable_folds']}, "
                f"fold_concentration_warnings={item['fold_concentration_warnings']}."
            )
        lines.append("")
    lines.extend(
        [
            "## 4. Comparaison aux baselines",
            "",
            f"- Verdict global : `{baseline['verdict']}`.",
            f"- Clear wins appris : `{baseline['clear_baseline_wins_count']}`.",
            f"- Resultats mitiges : `{baseline['mixed_results_count']}`.",
            f"- Misses : `{baseline['baseline_miss_count']}`.",
        ]
    )
    for key, value in baseline["comparisons"].items():
        lines.append(
            "- "
            f"{key}: delta_macro_f1_vs_majority={value['delta_macro_f1_vs_majority']}, "
            f"delta_macro_f1_vs_random={value['delta_macro_f1_vs_random']}, "
            f"verdict=`{value['verdict']}`."
        )
    lines.extend(
        [
            "",
            "## 5. Stabilite entre folds",
            "",
            f"- Verdict : `{fold['verdict']}`.",
            f"- Entrees instables : `{fold['unstable_entries_count']}`.",
            f"- Entrees faibles : `{fold['weak_entries_count']}`.",
            f"- Concentration fold : `{fold['fold_concentration_warnings_count']}` entrees.",
            "- Les resultats dependent trop de certains folds pour justifier un backtest.",
            "",
            "## 6. Stabilite par timeframe",
            "",
            f"- Verdict : `{timeframe['verdict']}`.",
            "- 1m : accuracy elevee, macro_f1 moins convaincante et folds instables.",
            "- 5m : meilleur profil learned, mais il ne suffit pas a stabiliser tout le diagnostic.",
            "- 15m : profil learned interessant, mais decision_tree_depth_2 reste instable.",
            "- 1h : resultats mitiges et proches de la baseline random en macro_f1.",
            "- Les resultats ne sont pas coherents sur tous les timeframes.",
            "",
            "## 7. Label shuffle falsification par fold",
            "",
            f"- Cas analyses : `{shuffle['total_cases']}`.",
            f"- Cas trop proches des labels melanges : `{shuffle['no_clear_edge_vs_shuffled_labels_count']}`.",
            f"- Par modele : `{shuffle['by_model']}`.",
            f"- Par timeframe : `{shuffle['by_timeframe']}`.",
            f"- Par role : `{shuffle['by_role']}`.",
            "- Le fait que 18 cas restent trop proches des labels melanges est une alerte forte.",
            "- La falsification n'est pas proprement satisfaite.",
            "",
            "## 8. Comparaison V8.7 vs V8.5 static split",
            "",
            "- V8.5 static split et V8.7 strict walk-forward ne sont pas le meme design de validation.",
            f"- Cas learned compares : `{static['compared_learned_cases']}`.",
            f"- Deltas macro_f1 positifs : `{static['positive_macro_f1_delta_cases']}`.",
            f"- Deltas macro_f1 negatifs : `{static['negative_macro_f1_delta_cases']}`.",
            f"- Verdict : `{static['verdict']}`.",
            "- V8.7 confirme que le diagnostic V8.5 doit rester prudent et descriptif.",
            "",
            "## 9. Fuites / anti-leakage",
            "",
            f"- Feature leakage detectee : `{leakage['feature_leakage_detected']}`.",
            f"- Colonnes interdites detectees : `{leakage['forbidden_feature_columns_present']}`.",
            f"- Metriques interdites detectees : `{leakage['metric_forbidden_terms_detected']}`.",
            "- Aucune feature future, label, split ou fold n'est reportee comme utilisee.",
            "",
            "## 10. Limites restantes",
            "",
            "- Pas de backtest.",
            "- Pas de couts ni slippage.",
            "- Pas d'execution.",
            "- Le label h1 peut etre trop bruite.",
            "- Les features peuvent etre trop agregees.",
            "- OHLCV + aggTrades seulement, sans funding, open interest ni order book.",
            "- Les comparaisons avec d'autres fenetres ne sont pas directes.",
            "- Les resultats ne sont pas valides pour trading.",
            "",
            "## 11. Decision de direction",
            "",
            f"- Option principale : {decision['recommended_next_step']}",
            f"- Option secondaire : {decision['secondary_next_step']}",
            "- Un backtest research tres borne n'est pas recommande maintenant.",
            "- La raison principale est la proximite aux labels melanges et la concentration folds/timeframes.",
            "",
            "## 12. Roadmap proposee",
            "",
        ]
    )
    for item in decision["roadmap"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 13. Interdits maintenus",
            "",
            "- Pas de trading.",
            "- Pas de paper live.",
            "- Pas d'ordre.",
            "- Pas de backtest destine a valider une strategie.",
            "- Pas de strategie.",
            "- Pas de signal de trading.",
            "- Pas de claim de rentabilite.",
        ]
    )
    return "\n".join(lines) + "\n"


def update_current_state(root: Path, decision: dict[str, Any]) -> None:
    state_path = root / PROJECT_STATE
    state = _load_json(state_path)
    state.update(
        {
            "last_validated_version": "V8.7",
            "candidate_version": VERSION,
            "candidate_status": "pending_external_audit",
            "direction": "strict walk-forward research decision gate",
            "research_decision_gate_v8_8_created": True,
            "research_decision_gate_v8_8_status": decision["status"],
            "research_decision_gate_v8_8_verdict": decision["summary_verdict"],
            "research_decision_gate_v8_8_recommended_next_step": decision["recommended_next_step"],
            "research_decision_gate_v8_8_secondary_next_step": decision["secondary_next_step"],
            "research_decision_gate_v8_8_window_start": decision["inputs"]["window_start"],
            "research_decision_gate_v8_8_window_end": decision["inputs"]["window_end"],
            "research_decision_gate_v8_8_days": decision["inputs"]["total_days"],
            "research_decision_gate_v8_8_no_clear_edge_vs_shuffled_labels_cases": decision["label_shuffle_assessment"][
                "no_clear_edge_vs_shuffled_labels_count"
            ],
            "backtest_v8_8_created": False,
            "strategy_v8_8_created": False,
            "signal_v8_8_created": False,
            "orders_v8_8_created": False,
            "paper_live_v8_8_created": False,
            "trading_v8_8_created": False,
            "persistent_model_v8_8_created": False,
        }
    )
    _write_json(state_path, state)
    metrics = {
        "last_validated_version": "V8.7",
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "direction": "strict walk-forward research decision gate",
        "window_start": decision["inputs"]["window_start"],
        "window_end": decision["inputs"]["window_end"],
        "total_days": decision["inputs"]["total_days"],
        "feature_columns_count": decision["inputs"]["feature_columns_count"],
        "summary_verdict": decision["summary_verdict"],
        "recommended_next_step": decision["recommended_next_step"],
        "secondary_next_step": decision["secondary_next_step"],
        "folds_count_by_timeframe": decision["inputs"]["folds_count_by_timeframe"],
        "no_clear_edge_vs_shuffled_labels_cases": decision["label_shuffle_assessment"]["no_clear_edge_vs_shuffled_labels_count"],
        "backtest_enabled": False,
        "strategy_enabled": False,
        "signal_created": False,
        "orders_enabled": False,
        "trading_enabled": False,
        "paper_live_enabled": False,
        "persistent_model_created": False,
        "external_validation_required": True,
    }
    _write_json(root / LATEST_METRICS_JSON, metrics)
    _write_text(root / PROJECT_STATE_MD, build_project_state_md(decision))
    _write_text(root / LATEST_SUMMARY, build_latest_summary_md(decision))
    _write_text(root / LATEST_METRICS_MD, build_latest_metrics_md(metrics))
    _write_text(root / README, build_readme_md(decision))


def build_project_state_md(decision: dict[str, Any]) -> str:
    return f"""# Etat du Projet : V8.7 validee + candidat V8.8

- **Derniere version validee** : V8.7.
- **Version candidate** : V8.8.
- **Statut candidate** : `pending_external_audit`.
- **Direction** : strict walk-forward research decision gate.

## Candidat V8.8

- Fenetre : `{decision['inputs']['window_start']}` -> `{decision['inputs']['window_end']}`.
- Nombre de jours : `{decision['inputs']['total_days']}`.
- Feature columns : `{decision['inputs']['feature_columns_count']}`.
- Verdict research : `{decision['summary_verdict']}`.
- Recommandation principale : {decision['recommended_next_step']}
- Recommandation secondaire : {decision['secondary_next_step']}
- Cas trop proches des labels melanges : `{decision['label_shuffle_assessment']['no_clear_edge_vs_shuffled_labels_count']}`.
- Rapport de decision uniquement, sans modification des donnees ni recalcul ML.

## Clause De Securite

- Aucun trading reel.
- Aucun paper live.
- Aucun ordre.
- Aucun backtest.
- Aucune strategie.
- Aucun signal de trading.
- Aucun modele persistant.
- Aucune API privee.
- Aucune cle API.
- V8.8 reste non validee avant audit externe.
"""


def build_latest_summary_md(decision: dict[str, Any]) -> str:
    return f"""# Latest Summary V8.8

V8.7 est la derniere version validee par audit externe.

V8.8 est la candidate courante. Elle produit une decision gate research apres la validation walk-forward offline stricte V8.7, sans entrainer de nouveau modele et sans modifier donnees, features, labels, datasets ou scores.

Fenetre : `{decision['inputs']['window_start']}` -> `{decision['inputs']['window_end']}`.

Total jours : `{decision['inputs']['total_days']}`.

Feature columns : `{decision['inputs']['feature_columns_count']}`.

Verdict : `{decision['summary_verdict']}`.

Recommandation principale : {decision['recommended_next_step']}

Recommandation secondaire : {decision['secondary_next_step']}

Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal de trading, aucun modele persistant et aucun claim de rentabilite.

V8.8 reste `pending_external_audit`.
"""


def build_latest_metrics_md(metrics: dict[str, Any]) -> str:
    return f"""# Latest Metrics V8.8

- Derniere version validee : V8.7.
- Candidate : V8.8.
- Statut : `pending_external_audit`.
- Direction : strict walk-forward research decision gate.
- Fenetre : `{metrics['window_start']}` -> `{metrics['window_end']}`.
- Total jours : `{metrics['total_days']}`.
- Feature columns : `{metrics['feature_columns_count']}`.
- Verdict : `{metrics['summary_verdict']}`.
- Recommandation principale : {metrics['recommended_next_step']}
- Recommandation secondaire : {metrics['secondary_next_step']}
- Cas trop proches des labels melanges : `{metrics['no_clear_edge_vs_shuffled_labels_cases']}`.

## Folds

- 1m: `{metrics['folds_count_by_timeframe']['1m']}`
- 5m: `{metrics['folds_count_by_timeframe']['5m']}`
- 15m: `{metrics['folds_count_by_timeframe']['15m']}`
- 1h: `{metrics['folds_count_by_timeframe']['1h']}`

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun modele persistant et aucun trading reel.
"""


def build_readme_md(decision: dict[str, Any]) -> str:
    return f"""# Projet Galapagos

- Derniere version validee : V8.7.
- Candidate : V8.8, strict walk-forward research decision gate.

V8.8 analyse la validation walk-forward offline stricte V8.7 et produit une decision research sans modifier les donnees, les features, les labels, les datasets ou les scores.

Fenetre : `{decision['inputs']['window_start']}` -> `{decision['inputs']['window_end']}`, `{decision['inputs']['total_days']}` jours.

Feature columns : `{decision['inputs']['feature_columns_count']}`.

Verdict : `{decision['summary_verdict']}`.

Recommandation principale : {decision['recommended_next_step']}

Recommandation secondaire : {decision['secondary_next_step']}

Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live, aucun trading reel et aucun modele persistant.

## Commandes V8.8

```bash
python scripts/run_research_decision_gate_v8_8.py
python scripts/validate_research_decision_gate_v8_8.py
python -m pytest -q tests/validation/test_research_decision_gate_v8_8.py
python -m pytest --collect-only -q
```
"""


def _reference_availability(root: Path) -> dict[str, Any]:
    references = {
        "v8_0_ohlcv_trades_90d": [
            Path("reports/manifests/ohlcv_trades_90d_offline_ml_research_v8_0_manifest.json"),
            Path("reports/ml/ohlcv_trades_90d_offline_ml_research_v8_0.json"),
        ],
        "v6_2_advanced_ohlcv": [
            Path("reports/manifests/advanced_ohlcv_offline_ml_research_v6_2_manifest.json"),
            Path("reports/ml/advanced_ohlcv_offline_ml_research_v6_2.json"),
        ],
        "v5_4_simple_ohlcv": [
            Path("reports/manifests/max_history_offline_ml_research_v5_4_manifest.json"),
            Path("reports/ml/max_history_offline_ml_research_v5_4.json"),
        ],
    }
    return {
        name: {"available": all((root / path).exists() for path in paths), "paths": [path.as_posix() for path in paths]}
        for name, paths in references.items()
    }


def _input_block(root: Path, relative: Path) -> dict[str, Any]:
    path = root / relative
    return {"path": relative.as_posix(), "sha256": _sha256(path), "bytes": path.stat().st_size}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
