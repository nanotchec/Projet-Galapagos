from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


VERSION = "V9.4"
LAST_VALIDATED_VERSION = "V9.0_to_V9.3.2"
WINDOW_START = "2023-03-25"
WINDOW_END = "2024-03-24"
TOTAL_DAYS = 366
TIMEFRAMES = ["1m", "5m", "15m", "1h"]
MODELS = [
    "majority_class_baseline",
    "random_seeded_baseline",
    "logistic_regression",
    "decision_tree_depth_2",
]
LEARNED_MODELS = ["logistic_regression", "decision_tree_depth_2"]

MANIFEST_PATH = Path("reports/manifests/refined_research_decision_gate_v9_4_manifest.json")
REPORT_JSON_PATH = Path("reports/research_decisions/refined_research_decision_gate_v9_4.json")
REPORT_MD_PATH = Path("reports/research_decisions/refined_research_decision_gate_v9_4.md")
DOC_MD_PATH = Path("docs/refined_research_decision_gate_v9_4.md")

INPUT_PATHS = {
    "v9_0_manifest": Path("reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json"),
    "v9_1_manifest": Path("reports/manifests/refined_ohlcv_trades_offline_supervised_dataset_v9_1_manifest.json"),
    "v9_2_manifest": Path("reports/manifests/refined_ohlcv_trades_offline_ml_research_v9_2_manifest.json"),
    "v9_3_manifest": Path("reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json"),
    "v9_2_report": Path("reports/ml/refined_ohlcv_trades_offline_ml_research_v9_2.json"),
    "v9_2_scores_report": Path("reports/ml/refined_ohlcv_trades_offline_research_scores_v9_2.json"),
    "v9_3_report": Path("reports/ml/refined_strict_walk_forward_validation_v9_3.json"),
    "v9_3_scores_report": Path("reports/ml/refined_strict_walk_forward_scores_v9_3.json"),
    "v9_3_2_attestation": Path("reports/audit_lite/v9_0_to_v9_3_2_full_local_validation_attestation.json"),
    "v9_3_2_inventory": Path("reports/audit_lite/v9_0_to_v9_3_2_artifact_inventory.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
}

SAFETY = {
    "public_read_only": True,
    "authentication_used": False,
    "api_key_used": False,
    "private_endpoint_used": False,
    "orders_enabled": False,
    "paper_live_enabled": False,
    "trading_enabled": False,
    "ml_enabled": False,
    "labels_enabled": False,
    "dataset_enabled": False,
    "backtest_enabled": False,
    "strategy_enabled": False,
    "execution_enabled": False,
}

FINDINGS = {
    "robust_edge_claimed": False,
    "strategy_validated": False,
    "backtest_performed": False,
    "actionable_signal_produced": False,
    "walk_forward_validated_for_trading": False,
    "trading_allowed": False,
    "paper_live_allowed": False,
    "real_trading_allowed": False,
}

ALLOWED_RESEARCH_DECISIONS = {
    "backtest_not_justified_refine_features",
    "backtest_not_justified_refine_labels",
    "backtest_not_justified_extend_data",
    "limited_research_backtest_candidate",
    "stop_research_branch",
}

LIMITATIONS = [
    "V9.4 analyse uniquement les resultats offline V9.2/V9.3 et ne modifie aucun artefact metier.",
    "V9.4 ne lance aucun backtest, aucune strategie, aucun signal actionnable et aucun ordre.",
    "Les resultats restent descriptifs et ne prouvent aucun edge exploitable.",
]


def run_refined_research_decision_gate_v9_4(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    decision = build_refined_research_decision_gate_v9_4(root)
    _write_json(root / REPORT_JSON_PATH, decision)
    markdown = build_decision_markdown_v9_4(decision)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_MD_PATH, markdown)
    manifest = build_manifest_v9_4(root, decision)
    _write_json(root / MANIFEST_PATH, manifest)
    update_state_surfaces_v9_4(root, decision, manifest)
    return manifest


def build_refined_research_decision_gate_v9_4(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    v90 = inputs["v9_0_manifest"]["payload"]
    v91 = inputs["v9_1_manifest"]["payload"]
    v92 = inputs["v9_2_manifest"]["payload"]
    v93 = inputs["v9_3_manifest"]["payload"]
    v92_report = inputs["v9_2_report"]["payload"]
    v93_report = inputs["v9_3_report"]["payload"]
    attestation = inputs["v9_3_2_attestation"]["payload"]

    v92_performance = build_static_split_assessment_v9_4(v92_report)
    v93_performance = build_walk_forward_assessment_v9_4(v93)
    baseline_assessment = build_baseline_assessment_v9_4(v92_report, v93)
    fold_assessment = build_fold_stability_assessment_v9_4(v93)
    timeframe_assessment = build_timeframe_stability_assessment_v9_4(v93)
    label_shuffle = build_label_shuffle_assessment_v9_4(v93)
    static_vs_walk_forward = build_static_vs_walk_forward_assessment_v9_4(v93)
    leakage = build_leakage_assessment_v9_4(v93)
    metric_scan = build_metric_forbidden_assessment_v9_4(v92, v93)
    feature_coherence = build_selected_feature_coherence_v9_4(v90, v92, v93)
    claims = build_claims_assessment_v9_4(v93, attestation)
    warnings = build_warnings_v9_4(v93, baseline_assessment, label_shuffle, static_vs_walk_forward)
    research_decision = choose_research_decision_v9_4(
        baseline_assessment=baseline_assessment,
        fold_assessment=fold_assessment,
        label_shuffle=label_shuffle,
        static_vs_walk_forward=static_vs_walk_forward,
        leakage=leakage,
        metric_scan=metric_scan,
        claims=claims,
    )

    return {
        "version": VERSION,
        "status": "PASS",
        "decision_gate_type": "research_only",
        "created_at_utc": _utc_now(),
        "inputs": {
            name: {
                "path": item["path"],
                "sha256": item["sha256"],
            }
            for name, item in inputs.items()
        },
        "window": {
            "window_start": WINDOW_START,
            "window_end": WINDOW_END,
            "total_days": TOTAL_DAYS,
        },
        "source_versions": {
            "last_validated_version": LAST_VALIDATED_VERSION,
            "feature_store": v90.get("version"),
            "dataset": v91.get("version"),
            "static_split_ml": v92.get("version"),
            "strict_walk_forward": v93.get("version"),
        },
        "target_name": v93.get("target_name"),
        "models": v93.get("models", []),
        "timeframes": TIMEFRAMES,
        "feature_columns_count": v93.get("feature_columns_count"),
        "selected_features_count": v90.get("selected_features_count"),
        "v9_2_static_split_assessment": v92_performance,
        "v9_3_walk_forward_assessment": v93_performance,
        "baseline_assessment": baseline_assessment,
        "fold_stability_assessment": fold_assessment,
        "timeframe_stability_assessment": timeframe_assessment,
        "label_shuffle_assessment": label_shuffle,
        "static_split_vs_walk_forward_assessment": static_vs_walk_forward,
        "feature_leakage_scan": leakage,
        "metric_forbidden_scan": metric_scan,
        "selected_features_coherence": feature_coherence,
        "forbidden_claims_assessment": claims,
        "research_decision": research_decision,
        "decision_justification": build_decision_justification_v9_4(research_decision, baseline_assessment, label_shuffle, fold_assessment),
        "evidence_used": [
            "V9.2 static split metrics",
            "V9.3 strict walk-forward aggregate metrics",
            "V9.3 fold concentration warnings",
            "V9.3 label shuffle falsification",
            "V9.3 feature leakage scan",
            "V9.3 metric forbidden scan",
            "V9.0 selected feature coherence",
            "V9.0_to_V9.3.2 audit-lite attestation",
        ],
        "warnings": warnings,
        "confidence_level": "medium_high",
        "next_step_recommendation": "V9.5 - Alternative Label Design Audit avant tout backtest research.",
        "secondary_next_step_recommendation": "Revenir aux features seulement si le redesign de labels ne reduit pas le bruit.",
        "explicit_no_trading_statement": "V9.4 est une decision research offline : aucun trading, aucun paper live, aucun ordre et aucun signal actionnable.",
        "findings": dict(FINDINGS),
        "safety": dict(SAFETY),
        "limitations": LIMITATIONS,
    }


def build_manifest_v9_4(root: Path, decision: dict[str, Any]) -> dict[str, Any]:
    report_json = root / REPORT_JSON_PATH
    report_md = root / REPORT_MD_PATH
    doc_md = root / DOC_MD_PATH
    return {
        "version": VERSION,
        "status": "PASS",
        "created_at_utc": _utc_now(),
        "decision_gate_type": "research_only",
        "research_decision": decision["research_decision"],
        "input_reports": decision["inputs"],
        "window": decision["window"],
        "feature_columns_count": decision["feature_columns_count"],
        "selected_features_count": decision["selected_features_count"],
        "outputs": {
            "decision_json": _artifact_block(report_json, REPORT_JSON_PATH),
            "decision_markdown": _artifact_block(report_md, REPORT_MD_PATH),
            "documentation": _artifact_block(doc_md, DOC_MD_PATH),
        },
        "baseline_assessment": decision["baseline_assessment"],
        "fold_stability_assessment": decision["fold_stability_assessment"],
        "timeframe_stability_assessment": decision["timeframe_stability_assessment"],
        "label_shuffle_assessment": decision["label_shuffle_assessment"],
        "static_split_vs_walk_forward_assessment": decision["static_split_vs_walk_forward_assessment"],
        "feature_leakage_scan": decision["feature_leakage_scan"],
        "metric_forbidden_scan": decision["metric_forbidden_scan"],
        "selected_features_coherence": decision["selected_features_coherence"],
        "findings": decision["findings"],
        "safety": decision["safety"],
        "limitations": decision["limitations"],
    }


def build_static_split_assessment_v9_4(v92_report: dict[str, Any]) -> dict[str, Any]:
    test_metrics = {
        key: value
        for key, value in v92_report.get("metrics", {}).items()
        if key.endswith(".test")
    }
    summary = {}
    for key, metric in sorted(test_metrics.items()):
        summary[key] = {
            "timeframe": metric["timeframe"],
            "model_name": metric["model_name"],
            "accuracy": metric["accuracy"],
            "balanced_accuracy": metric["balanced_accuracy"],
            "macro_f1": metric["macro_f1"],
            "rows": metric["rows"],
        }
    return {
        "status": "PASS",
        "descriptive_only": True,
        "not_a_backtest": True,
        "metrics_count": len(summary),
        "test_metrics": summary,
    }


def build_walk_forward_assessment_v9_4(v93: dict[str, Any]) -> dict[str, Any]:
    aggregate = {}
    for key, metric in sorted(v93.get("aggregate_metrics", {}).items()):
        aggregate[key] = {
            "timeframe": metric["timeframe"],
            "model_name": metric["model_name"],
            "folds_count": metric["folds_count"],
            "mean_validation_accuracy": metric["mean_validation_accuracy"],
            "mean_test_accuracy": metric["mean_test_accuracy"],
            "std_test_accuracy": metric["std_test_accuracy"],
            "mean_test_macro_f1": metric["mean_test_macro_f1"],
            "std_test_macro_f1": metric["std_test_macro_f1"],
            "weak_folds": metric.get("weak_folds", []),
            "unstable_folds": metric.get("unstable_folds", []),
            "fold_concentration_warnings": metric.get("fold_concentration_warnings", []),
        }
    return {
        "status": "PASS",
        "descriptive_only": True,
        "not_a_backtest": True,
        "aggregate_metrics": aggregate,
        "findings_false": all(v93.get("findings", {}).get(key) is False for key in FINDINGS if key in v93.get("findings", {})),
    }


def build_baseline_assessment_v9_4(v92_report: dict[str, Any], v93: dict[str, Any]) -> dict[str, Any]:
    static_comparisons = _compare_against_baselines_static(v92_report)
    walk_forward_comparisons = _compare_against_baselines_walk_forward(v93)
    clear_static = sum(item["clear_win"] for item in static_comparisons.values())
    clear_wf = sum(item["clear_win"] for item in walk_forward_comparisons.values())
    mixed_wf = sum(item["mixed_or_small_win"] for item in walk_forward_comparisons.values())
    return {
        "verdict": "mitige_gain_insuffisant_pour_backtest",
        "clear_static_split_wins": clear_static,
        "clear_walk_forward_wins": clear_wf,
        "mixed_walk_forward_cases": mixed_wf,
        "clear_win_policy": "accuracy and macro_f1 above majority and random baselines by more than 0.01",
        "static_split_comparisons": static_comparisons,
        "walk_forward_comparisons": walk_forward_comparisons,
        "learned_models_clearly_beat_baselines": clear_wf >= 6,
        "backtest_not_justified": True,
    }


def build_fold_stability_assessment_v9_4(v93: dict[str, Any]) -> dict[str, Any]:
    aggregate = v93.get("aggregate_metrics", {})
    weak = {key: metric.get("weak_folds", []) for key, metric in aggregate.items() if metric.get("weak_folds")}
    unstable = {key: metric.get("unstable_folds", []) for key, metric in aggregate.items() if metric.get("unstable_folds")}
    concentration = {
        key: metric.get("fold_concentration_warnings", [])
        for key, metric in aggregate.items()
        if metric.get("fold_concentration_warnings")
    }
    return {
        "verdict": "instable_concentration_presente" if concentration or unstable else "stable",
        "weak_entries_count": len(weak),
        "unstable_entries_count": len(unstable),
        "fold_concentration_entries_count": len(concentration),
        "weak_folds_by_model_timeframe": weak,
        "unstable_folds_by_model_timeframe": unstable,
        "fold_concentration_warnings_by_model_timeframe": concentration,
        "backtest_not_justified_due_to_concentration": bool(concentration or unstable),
    }


def build_timeframe_stability_assessment_v9_4(v93: dict[str, Any]) -> dict[str, Any]:
    by_model: dict[str, dict[str, Any]] = {}
    for model in MODELS:
        values = {
            timeframe: v93["aggregate_metrics"][f"{timeframe}.{model}"]["mean_test_macro_f1"]
            for timeframe in TIMEFRAMES
        }
        best_timeframe = max(values, key=values.get)
        worst_timeframe = min(values, key=values.get)
        by_model[model] = {
            "mean_test_macro_f1_by_timeframe": values,
            "best_timeframe": best_timeframe,
            "worst_timeframe": worst_timeframe,
            "macro_f1_range": round(values[best_timeframe] - values[worst_timeframe], 12),
            "dominant_timeframe_warning": (values[best_timeframe] - values[worst_timeframe]) > 0.08,
        }
    return {
        "verdict": "non_uniforme_entre_timeframes",
        "by_model": by_model,
        "dominant_timeframe_warnings_count": sum(item["dominant_timeframe_warning"] for item in by_model.values()),
    }


def build_label_shuffle_assessment_v9_4(v93: dict[str, Any]) -> dict[str, Any]:
    cases = {
        key: value
        for key, value in v93.get("label_shuffle_falsification", {}).items()
        if value.get("no_clear_edge_vs_shuffled_labels")
    }
    by_timeframe = Counter(value["timeframe"] for value in cases.values())
    by_model = Counter(value["model_name"] for value in cases.values())
    by_role = Counter(value["fold_role"] for value in cases.values())
    return {
        "verdict": "falsification_non_propre",
        "falsification_clean": not cases,
        "no_clear_edge_vs_shuffled_labels_count": len(cases),
        "no_clear_edge_by_timeframe": dict(sorted(by_timeframe.items())),
        "no_clear_edge_by_model": dict(sorted(by_model.items())),
        "no_clear_edge_by_fold_role": dict(sorted(by_role.items())),
        "examples": sorted(cases)[:10],
        "backtest_not_justified_due_to_shuffle": bool(cases),
    }


def build_static_vs_walk_forward_assessment_v9_4(v93: dict[str, Any]) -> dict[str, Any]:
    comparison = v93.get("comparison_to_static_split_v9_2", {})
    comparisons = comparison.get("comparisons", {})
    large_accuracy_delta = {
        key: value
        for key, value in comparisons.items()
        if abs(value.get("accuracy_delta_v9_3_minus_v9_2_static", 0.0)) > 0.05
    }
    large_macro_f1_delta = {
        key: value
        for key, value in comparisons.items()
        if abs(value.get("macro_f1_delta_v9_3_minus_v9_2_static", 0.0)) > 0.05
    }
    return {
        "verdict": "comparaison_descriptive_non_equivalente",
        "descriptive_only": comparison.get("descriptive_only") is True,
        "not_same_validation_design": comparison.get("not_same_validation_design") is True,
        "comparisons_count": len(comparisons),
        "large_accuracy_delta_count": len(large_accuracy_delta),
        "large_macro_f1_delta_count": len(large_macro_f1_delta),
        "large_accuracy_delta_examples": sorted(large_accuracy_delta)[:10],
        "large_macro_f1_delta_examples": sorted(large_macro_f1_delta)[:10],
        "backtest_not_justified_due_to_design_gap": comparison.get("not_same_validation_design") is True,
    }


def build_leakage_assessment_v9_4(v93: dict[str, Any]) -> dict[str, Any]:
    scan = v93.get("feature_leakage_scan", {})
    return {
        "passed": scan.get("feature_leakage_detected") is False and not scan.get("forbidden_feature_columns_present"),
        "feature_leakage_detected": bool(scan.get("feature_leakage_detected")),
        "forbidden_feature_columns_present": scan.get("forbidden_feature_columns_present", []),
        "feature_columns_checked": scan.get("feature_columns_checked", []),
    }


def build_metric_forbidden_assessment_v9_4(v92: dict[str, Any], v93: dict[str, Any]) -> dict[str, Any]:
    v92_scan = _scan_metric_terms(v92)
    v93_reported = v93.get("metric_forbidden_scan", {})
    detected = bool(v92_scan["forbidden_terms_present"] or v93_reported.get("forbidden_terms_present"))
    return {
        "passed": not detected and v93_reported.get("metric_forbidden_terms_detected") is False,
        "v9_2_forbidden_terms_present": v92_scan["forbidden_terms_present"],
        "v9_3_forbidden_terms_present": v93_reported.get("forbidden_terms_present", []),
        "metric_forbidden_terms_detected": detected,
    }


def build_selected_feature_coherence_v9_4(v90: dict[str, Any], v92: dict[str, Any], v93: dict[str, Any]) -> dict[str, Any]:
    selected = list(v90.get("selected_features", []))
    v92_features = list(v92.get("feature_columns", []))
    v93_features = list(v93.get("feature_columns", []))
    return {
        "passed": bool(selected) and selected == v92_features == v93_features,
        "selected_features_count": len(selected),
        "v9_2_feature_columns_count": len(v92_features),
        "v9_3_feature_columns_count": len(v93_features),
        "selected_features": selected,
        "missing_in_v9_2": sorted(set(selected) - set(v92_features)),
        "missing_in_v9_3": sorted(set(selected) - set(v93_features)),
        "extra_in_v9_2": sorted(set(v92_features) - set(selected)),
        "extra_in_v9_3": sorted(set(v93_features) - set(selected)),
    }


def build_claims_assessment_v9_4(v93: dict[str, Any], attestation: dict[str, Any]) -> dict[str, Any]:
    false_findings = {
        key: v93.get("findings", {}).get(key)
        for key in [
            "robust_edge_claimed",
            "strategy_validated",
            "backtest_performed",
            "actionable_signal_produced",
            "walk_forward_validated_for_trading",
        ]
    }
    attestation_flags = {
        key: attestation.get(key)
        for key in ["no_trading", "no_backtest", "no_orders", "no_strategy", "no_persistent_model", "api_key_used", "private_endpoint_used"]
    }
    return {
        "passed": all(value is False for value in false_findings.values())
        and all(attestation_flags[key] is True for key in ["no_trading", "no_backtest", "no_orders", "no_strategy", "no_persistent_model"])
        and attestation_flags["api_key_used"] is False
        and attestation_flags["private_endpoint_used"] is False,
        "v9_3_findings": false_findings,
        "v9_3_2_attestation_flags": attestation_flags,
    }


def choose_research_decision_v9_4(
    *,
    baseline_assessment: dict[str, Any],
    fold_assessment: dict[str, Any],
    label_shuffle: dict[str, Any],
    static_vs_walk_forward: dict[str, Any],
    leakage: dict[str, Any],
    metric_scan: dict[str, Any],
    claims: dict[str, Any],
) -> str:
    if not leakage["passed"] or not metric_scan["passed"] or not claims["passed"]:
        return "stop_research_branch"
    if label_shuffle["no_clear_edge_vs_shuffled_labels_count"] >= 5:
        return "backtest_not_justified_refine_labels"
    if fold_assessment["fold_concentration_entries_count"] or fold_assessment["unstable_entries_count"]:
        return "backtest_not_justified_refine_features"
    if not baseline_assessment["learned_models_clearly_beat_baselines"]:
        return "backtest_not_justified_refine_features"
    if static_vs_walk_forward["not_same_validation_design"]:
        return "backtest_not_justified_extend_data"
    return "limited_research_backtest_candidate"


def build_decision_justification_v9_4(
    decision: str,
    baseline_assessment: dict[str, Any],
    label_shuffle: dict[str, Any],
    fold_assessment: dict[str, Any],
) -> str:
    if decision == "backtest_not_justified_refine_labels":
        return (
            "Le backtest n'est pas justifie : "
            f"{label_shuffle['no_clear_edge_vs_shuffled_labels_count']} cas restent trop proches des labels melanges, "
            f"avec {fold_assessment['fold_concentration_entries_count']} entrees de concentration et seulement "
            f"{baseline_assessment['clear_walk_forward_wins']} gains walk-forward clairs contre les baselines."
        )
    if decision == "backtest_not_justified_refine_features":
        return "Le backtest n'est pas justifie : les gains restent instables et concentres sur certains folds ou timeframes."
    if decision == "backtest_not_justified_extend_data":
        return "Le backtest n'est pas justifie : les designs static split et walk-forward restent trop differents."
    if decision == "stop_research_branch":
        return "La branche doit etre arretee tant que les scans de securite ou de fuite ne sont pas propres."
    return "Candidat theorique uniquement, sous reserve de criteres stricts non observes ici."


def build_warnings_v9_4(
    v93: dict[str, Any],
    baseline_assessment: dict[str, Any],
    label_shuffle: dict[str, Any],
    static_vs_walk_forward: dict[str, Any],
) -> list[str]:
    warnings = list(v93.get("findings", {}).get("warnings", []))
    if baseline_assessment["clear_walk_forward_wins"] < 6:
        warnings.append("Les modeles appris ne battent pas clairement les baselines de facon generalisee.")
    if label_shuffle["no_clear_edge_vs_shuffled_labels_count"] > 0:
        warnings.append("La falsification label shuffle reste trop proche dans plusieurs cas.")
    if static_vs_walk_forward["not_same_validation_design"]:
        warnings.append("La comparaison V9.2 static split / V9.3 walk-forward n'est pas equivalente.")
    return sorted(set(warnings))


def build_decision_markdown_v9_4(decision: dict[str, Any]) -> str:
    return f"""# Refined Research Decision Gate V9.4

## Resume executif

Decision research : `{decision['research_decision']}`.

V9.4 analyse les resultats V9.2 et V9.3 de la chaine refined OHLCV + trades. Le verdict est conservateur : aucun backtest research n'est justifie maintenant. Les resultats restent descriptifs, instables par endroits et trop proches des labels melanges dans plusieurs cas.

## Entrees

- Derniere version validee : `{LAST_VALIDATED_VERSION}`.
- Fenetre : `{WINDOW_START}` -> `{WINDOW_END}` (`{TOTAL_DAYS}` jours).
- Target : `{decision['target_name']}`.
- Modeles : `{decision['models']}`.
- Timeframes : `{TIMEFRAMES}`.
- Selected features : `{decision['selected_features_count']}`.

## Diagnostic V9.2 static split

V9.2 fournit des metriques offline descriptives sur split temporel simple. Ces metriques ne sont pas un backtest et ne produisent aucun signal actionnable.

## Diagnostic V9.3 walk-forward strict

- Entrees de concentration fold/timeframe : `{decision['fold_stability_assessment']['fold_concentration_entries_count']}`.
- Entrees instables : `{decision['fold_stability_assessment']['unstable_entries_count']}`.
- Cas trop proches des labels melanges : `{decision['label_shuffle_assessment']['no_clear_edge_vs_shuffled_labels_count']}`.
- Fuite feature detectee : `{decision['feature_leakage_scan']['feature_leakage_detected']}`.
- Metriques interdites detectees : `{decision['metric_forbidden_scan']['metric_forbidden_terms_detected']}`.

## Comparaison aux baselines

- Gains walk-forward clairs : `{decision['baseline_assessment']['clear_walk_forward_wins']}`.
- Cas walk-forward mitiges : `{decision['baseline_assessment']['mixed_walk_forward_cases']}`.
- Politique : `{decision['baseline_assessment']['clear_win_policy']}`.

Les gains ne sont pas assez nets et generalises pour justifier un backtest.

## Label shuffle falsification

La falsification n'est pas propre : `{decision['label_shuffle_assessment']['no_clear_edge_vs_shuffled_labels_count']}` cas restent trop proches des labels melanges. Cela pointe plutot vers un probleme de definition ou de bruit des labels que vers un edge exploitable.

## Static split vs walk-forward

La comparaison V9.2/V9.3 est descriptive uniquement. Les deux designs ne sont pas equivalents : `{decision['static_split_vs_walk_forward_assessment']['not_same_validation_design']}`.

## Decision

Justification : {decision['decision_justification']}

Niveau de confiance : `{decision['confidence_level']}`.

Prochaine etape recommandee : {decision['next_step_recommendation']}

Etape secondaire : {decision['secondary_next_step_recommendation']}

## Interdits maintenus

V9.4 ne valide aucune strategie, ne produit aucun backtest, ne produit aucun signal actionnable, ne produit aucun ordre, n'autorise aucun paper live et n'autorise aucun trading reel. Aucun modele persistant, aucune API privee et aucune cle API ne sont utilises.
"""


def update_state_surfaces_v9_4(root: Path, decision: dict[str, Any], manifest: dict[str, Any]) -> None:
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "direction": "refined research decision gate",
        "research_decision_v9_4": decision["research_decision"],
        "research_decision_gate_v9_4_status": decision["status"],
        "research_decision_gate_v9_4_report": REPORT_JSON_PATH.as_posix(),
        "research_decision_gate_v9_4_manifest": MANIFEST_PATH.as_posix(),
        "feature_columns_count": decision["feature_columns_count"],
        "selected_features_count": decision["selected_features_count"],
        "label_shuffle_no_clear_edge_cases_v9_4": decision["label_shuffle_assessment"]["no_clear_edge_vs_shuffled_labels_count"],
        "fold_concentration_entries_v9_4": decision["fold_stability_assessment"]["fold_concentration_entries_count"],
        "backtest_performed": False,
        "strategy_enabled": False,
        "actionable_signal_produced": False,
        "orders_enabled": False,
        "trading_enabled": False,
        "paper_live_enabled": False,
        "persistent_model_created": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "external_validation_required": True,
    }
    state.update(metrics)
    _write_json(state_path, state, sort_keys=False)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    _write_text(
        root / "reports/PROJECT_STATE.md",
        "# Etat du Projet : V9.0_to_V9.3.2 validee + candidat V9.4\n\n"
        "- **Derniere version validee** : V9.0_to_V9.3.2.\n"
        "- **Version candidate** : V9.4.\n"
        "- **Statut candidate** : `pending_external_audit`.\n"
        "- **Direction** : refined research decision gate.\n"
        f"- **Decision research** : `{decision['research_decision']}`.\n\n"
        "V9.4 ne lance aucun backtest et ne produit aucun signal actionnable.\n\n"
        "Aucun trading, paper live, ordre, strategie, modele persistant, API privee ou cle API.\n",
    )
    _write_text(
        root / "reports/current/latest_metrics.md",
        "# Latest Metrics V9.4\n\n"
        "- Derniere version validee : V9.0_to_V9.3.2.\n"
        "- Candidate : V9.4.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Decision research : `{decision['research_decision']}`.\n"
        f"- Selected features : `{decision['selected_features_count']}`.\n"
        f"- Cas trop proches des labels melanges : `{decision['label_shuffle_assessment']['no_clear_edge_vs_shuffled_labels_count']}`.\n"
        f"- Entrees de concentration fold/timeframe : `{decision['fold_stability_assessment']['fold_concentration_entries_count']}`.\n\n"
        "Aucun backtest, aucune strategie, aucun signal actionnable, aucun ordre, aucun trading reel.\n",
    )
    _write_text(
        root / "reports/current/latest_summary.md",
        "# Latest Summary V9.4\n\n"
        "V9.0_to_V9.3.2 est la derniere version validee par audit externe.\n\n"
        "V9.4 est la candidate courante. Elle produit uniquement un decision gate research sur les resultats V9.2/V9.3 de la chaine refined OHLCV + trades.\n\n"
        f"Decision : `{decision['research_decision']}`. Le backtest n'est pas justifie maintenant ; la priorite recommandee est un audit/redesign des labels.\n\n"
        "La candidate reste `pending_external_audit`. Aucun trading, paper live, ordre, backtest execute, strategie, signal actionnable ou modele persistant n'est produit.\n",
    )
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V9.0_to_V9.3.2.\n"
        "- Candidate : V9.4, refined research decision gate.\n"
        f"- Decision research : {decision['research_decision']}.\n\n"
        "V9.4 analyse uniquement les resultats offline V9.2/V9.3. Elle ne lance aucun backtest, ne produit aucune strategie, aucun signal actionnable et aucun ordre.\n\n"
        "Aucun trading reel, aucun paper live, aucune API privee, aucune cle API et aucun modele persistant.\n",
    )


def _compare_against_baselines_static(v92_report: dict[str, Any]) -> dict[str, Any]:
    metrics = v92_report.get("metrics", {})
    comparisons = {}
    for timeframe in TIMEFRAMES:
        majority = metrics[f"{timeframe}.majority_class_baseline.test"]
        random = metrics[f"{timeframe}.random_seeded_baseline.test"]
        for model in LEARNED_MODELS:
            learned = metrics[f"{timeframe}.{model}.test"]
            comparisons[f"{timeframe}.{model}"] = _comparison_block(learned, majority, random)
    return comparisons


def _compare_against_baselines_walk_forward(v93: dict[str, Any]) -> dict[str, Any]:
    aggregate = v93.get("aggregate_metrics", {})
    comparisons = {}
    for timeframe in TIMEFRAMES:
        majority = aggregate[f"{timeframe}.majority_class_baseline"]
        random = aggregate[f"{timeframe}.random_seeded_baseline"]
        for model in LEARNED_MODELS:
            learned = aggregate[f"{timeframe}.{model}"]
            comparisons[f"{timeframe}.{model}"] = _comparison_block(learned, majority, random, aggregate=True)
    return comparisons


def _comparison_block(learned: dict[str, Any], majority: dict[str, Any], random: dict[str, Any], aggregate: bool = False) -> dict[str, Any]:
    accuracy_key = "mean_test_accuracy" if aggregate else "accuracy"
    f1_key = "mean_test_macro_f1" if aggregate else "macro_f1"
    acc_delta_majority = learned[accuracy_key] - majority[accuracy_key]
    acc_delta_random = learned[accuracy_key] - random[accuracy_key]
    f1_delta_majority = learned[f1_key] - majority[f1_key]
    f1_delta_random = learned[f1_key] - random[f1_key]
    clear_win = all(value > 0.01 for value in [acc_delta_majority, acc_delta_random, f1_delta_majority, f1_delta_random])
    mixed = not clear_win and any(value > 0.01 for value in [acc_delta_majority, acc_delta_random, f1_delta_majority, f1_delta_random])
    return {
        "timeframe": learned["timeframe"],
        "model_name": learned["model_name"],
        "accuracy": learned[accuracy_key],
        "macro_f1": learned[f1_key],
        "delta_accuracy_vs_majority": round(acc_delta_majority, 12),
        "delta_accuracy_vs_random": round(acc_delta_random, 12),
        "delta_macro_f1_vs_majority": round(f1_delta_majority, 12),
        "delta_macro_f1_vs_random": round(f1_delta_random, 12),
        "clear_win": clear_win,
        "mixed_or_small_win": mixed,
    }


def _scan_metric_terms(payload: Any) -> dict[str, Any]:
    forbidden_terms = {"pnl", "sharpe", "drawdown", "equity_curve", "profit_factor", "trading_win_rate"}
    present: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                key_text = str(key).casefold()
                for term in forbidden_terms:
                    if term in key_text:
                        present.add(term)
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return {"forbidden_terms_present": sorted(present)}


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    file_path = root / path
    if not file_path.exists():
        raise FileNotFoundError(f"missing required V9.4 input: {path}")
    payload: Any
    if file_path.suffix == ".json":
        payload = _read_json(file_path)
    else:
        payload = file_path.read_text(encoding="utf-8")
    return {"path": path.as_posix(), "sha256": _sha256_file(file_path), "payload": payload}


def _artifact_block(path: Path, display_path: Path) -> dict[str, Any]:
    return {"path": display_path.as_posix(), "sha256": _sha256_file(path), "bytes": path.stat().st_size}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any], *, sort_keys: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=sort_keys, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
