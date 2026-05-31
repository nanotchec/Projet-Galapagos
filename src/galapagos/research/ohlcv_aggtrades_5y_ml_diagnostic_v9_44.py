from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


VERSION = "V9.44"
SOURCE_VERSION = "V9.43"
REPORT_JSON_PATH = Path("reports/research_decisions/ohlcv_aggtrades_5y_ml_diagnostic_v9_44.json")
REPORT_MD_PATH = Path("reports/research_decisions/ohlcv_aggtrades_5y_ml_diagnostic_v9_44.md")
MANIFEST_PATH = Path("reports/manifests/ohlcv_aggtrades_5y_ml_diagnostic_v9_44_manifest.json")
DOC_PATH = Path("docs/ohlcv_aggtrades_5y_ml_diagnostic_v9_44.md")

INPUT_PATHS = {
    "ml_report_v9_43": Path("reports/ml/ohlcv_aggtrades_5y_offline_ml_v9_43.json"),
    "ml_scores_v9_43": Path("reports/ml/ohlcv_aggtrades_5y_offline_scores_v9_43.json"),
    "ml_manifest_v9_43": Path("reports/manifests/ohlcv_aggtrades_5y_offline_ml_v9_43_manifest.json"),
    "dataset_validation_v9_42": Path("reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42.json"),
    "dataset_v9_41": Path("reports/datasets/ohlcv_aggtrades_5y_dataset_v9_41.json"),
    "label_factory_v9_40": Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json"),
    "feature_validation_v9_38": Path("reports/features/ohlcv_aggtrades_5y_feature_store_validation_v9_38.json"),
    "feature_store_v9_37": Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_37.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "project_state": Path("reports/PROJECT_STATE.json"),
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

SAFETY_FLAGS = {
    "no_trading": True,
    "no_paper_live": True,
    "no_orders": True,
    "no_backtest": True,
    "no_walk_forward": True,
    "no_strategy": True,
    "no_actionable_signal": True,
    "no_persistent_model": True,
    "no_model_training_heavy": True,
    "api_key_used": False,
    "private_endpoint_used": False,
    "exchange_auth_used": False,
    "websocket_live_used": False,
    "network_used": False,
    "no_new_data_download": True,
    "no_destructive_cleanup": True,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}

OPTION_COMPARISON = {
    "feature_enrichment_aggtrades_exact": {
        "rating": "recommended_first",
        "reason": "Les modeles V9.43 ne sortent presque jamais de FLAT; les features aggTrades disponibles restent agrégées et ne couvrent pas les comptages exacts buyer-maker, tailles medianes, gros trades et buckets de taille.",
        "examples": [
            "buyer_maker_count exact",
            "taker buy/sell count exact",
            "median_trade_size exact",
            "large_trade_count exact",
            "trade size distribution buckets",
            "burst/intensity features plus fines",
        ],
    },
    "label_redesign": {
        "rating": "recommended_after_feature_gap",
        "reason": "Le label h1 est majoritairement FLAT mais pas suffisamment extreme pour expliquer seul l'absence de discrimination; il faut toutefois tester un label directionnel binaire ou quantile apres enrichissement.",
        "examples": ["binary directional", "quantile-based", "h1 seuil different", "h4 seuil different", "event-based non trading"],
    },
    "derivatives_data_extension": {
        "rating": "defer_until_aggtrades_exact_review",
        "reason": "Funding/open interest peuvent ajouter un regime derivatives utile, mais le diagnostic actuel pointe d'abord un manque de microstructure spot exacte dans les features existantes.",
        "examples": ["funding rates", "open interest", "liquidations"],
    },
    "walk_forward": {
        "rating": "not_justified",
        "reason": "Aucun edge robuste n'est demontre par V9.43; les resultats sont proches du shuffle et des baselines.",
    },
    "stop_branch_or_manual_review": {
        "rating": "not_primary",
        "reason": "Les donnees et labels sont valides; l'etape la plus informative reste un enrichissement feature cible, puis un nouveau diagnostic.",
    },
}


def run_ml_diagnostic_v9_44(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    inputs = {name: _read_json(root / path) for name, path in INPUT_PATHS.items() if (root / path).is_file()}
    missing_inputs = [path.as_posix() for name, path in INPUT_PATHS.items() if name not in inputs]
    ml_report = inputs["ml_report_v9_43"]
    dataset_validation = inputs["dataset_validation_v9_42"]
    label_factory = inputs["label_factory_v9_40"]
    feature_validation = inputs["feature_validation_v9_38"]
    feature_store = inputs.get("feature_store_v9_37", {})

    ml_result_summary = _build_ml_result_summary(ml_report)
    label_diagnostic = _build_label_diagnostic(dataset_validation, label_factory)
    feature_diagnostic = _build_feature_diagnostic(feature_validation, feature_store, ml_report)
    decision, next_recommendation = _decide(ml_result_summary, label_diagnostic, feature_diagnostic)
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS",
        "created_at_utc": _utc_now(),
        "diagnostic_only": True,
        "heavy_ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "model_persisted": False,
        "network_used": False,
        "new_data_downloaded": False,
        "inputs": {name: path.as_posix() for name, path in INPUT_PATHS.items()},
        "missing_inputs": missing_inputs,
        "ml_result_summary": ml_result_summary,
        "label_diagnostic": label_diagnostic,
        "feature_diagnostic": feature_diagnostic,
        "option_comparison": OPTION_COMPARISON,
        "decision": decision,
        "next_recommendation": next_recommendation,
        "blockers": [],
        "warnings": _build_warnings(ml_result_summary, label_diagnostic, feature_diagnostic),
        "limitations": [
            "Diagnostic fonde sur les rapports V9.43/V9.42/V9.40/V9.38, sans relecture massive du dataset full.",
            "Aucun nouveau label, aucune nouvelle feature et aucun entrainement lourd ne sont produits en V9.44.",
            "La disponibilite predictive de funding/open interest n'est pas testee dans cette version.",
        ],
        "findings": FINDINGS,
        "safety_flags": SAFETY_FLAGS,
    }
    _write_outputs(root, report)
    _update_current_state(root, report)
    return report


def _build_ml_result_summary(ml_report: dict[str, Any]) -> dict[str, Any]:
    comparisons = ml_report.get("baseline_comparison", {}).get("comparisons", {})
    learned_comparisons = [
        item
        for item in comparisons.values()
        if item.get("model_name") in {"logistic_regression", "decision_tree_depth_2"} and item.get("split") in {"validation", "test"}
    ]
    model_results = ml_report.get("model_results_by_timeframe", {})
    collapse = {}
    best_case: dict[str, Any] | None = None
    worst_case: dict[str, Any] | None = None
    for timeframe, payload in model_results.items():
        tf_metrics = payload.get("metrics", {})
        learned_rows = []
        for metric in tf_metrics.values():
            if metric.get("model_name") not in {"logistic_regression", "decision_tree_depth_2"} or metric.get("split") not in {"validation", "test"}:
                continue
            prediction_distribution = metric.get("prediction_distribution", {})
            rows = metric.get("rows") or sum(prediction_distribution.values())
            flat_ratio = (prediction_distribution.get("FLAT", 0) / rows) if rows else 0.0
            down_up_ratio = ((prediction_distribution.get("DOWN", 0) + prediction_distribution.get("UP", 0)) / rows) if rows else 0.0
            learned_rows.append(
                {
                    "model_name": metric.get("model_name"),
                    "split": metric.get("split"),
                    "accuracy": _round(metric.get("accuracy")),
                    "balanced_accuracy": _round(metric.get("balanced_accuracy")),
                    "macro_f1": _round(metric.get("macro_f1")),
                    "flat_prediction_ratio": _round(flat_ratio),
                    "down_up_prediction_ratio": _round(down_up_ratio),
                    "prediction_distribution": prediction_distribution,
                    "per_class_recall": metric.get("per_class_recall", {}),
                }
            )
            candidate = {
                "timeframe": timeframe,
                "model_name": metric.get("model_name"),
                "split": metric.get("split"),
                "macro_f1": metric.get("macro_f1", 0.0),
                "balanced_accuracy": metric.get("balanced_accuracy", 0.0),
                "flat_prediction_ratio": flat_ratio,
            }
            if best_case is None or candidate["macro_f1"] > best_case["macro_f1"]:
                best_case = candidate
            if worst_case is None or candidate["macro_f1"] < worst_case["macro_f1"]:
                worst_case = candidate
        collapse[timeframe] = {
            "learned_models": learned_rows,
            "all_learned_models_predict_mostly_flat": all(item["flat_prediction_ratio"] >= 0.97 for item in learned_rows),
            "decision_tree_equals_majority_baseline": all(
                item["flat_prediction_ratio"] == 1.0 for item in learned_rows if item["model_name"] == "decision_tree_depth_2"
            ),
        }
    mean_delta_macro = _mean([item.get("delta_macro_f1_vs_best_baseline", 0.0) for item in learned_comparisons])
    mean_delta_accuracy = _mean([item.get("delta_accuracy_vs_best_baseline", 0.0) for item in learned_comparisons])
    shuffle_deltas = ml_report.get("original_vs_shuffled_delta", {})
    learned_shuffle = [
        item
        for item in shuffle_deltas.values()
        if item.get("model_name") in {"logistic_regression", "decision_tree_depth_2"} and item.get("split") in {"validation", "test"}
    ]
    return {
        "target": ml_report.get("target"),
        "target_name": ml_report.get("target_name"),
        "models_executed": ml_report.get("models_executed", []),
        "feature_columns_count": ml_report.get("feature_columns_count"),
        "baseline_clear_wins_count": ml_report.get("baseline_comparison", {}).get("clear_wins_count"),
        "weak_vs_baselines_count": ml_report.get("baseline_comparison", {}).get("weak_vs_baselines_count"),
        "no_clear_edge_vs_shuffled_labels_count": ml_report.get("no_clear_edge_vs_shuffled_labels_count"),
        "mean_delta_macro_f1_vs_best_baseline": _round(mean_delta_macro),
        "mean_delta_accuracy_vs_best_baseline": _round(mean_delta_accuracy),
        "max_delta_macro_f1_original_vs_shuffled": _round(max((item.get("delta_macro_f1_original_vs_shuffled", 0.0) for item in learned_shuffle), default=0.0)),
        "learned_vs_baseline_summary": "Aucun modele learned ne produit de clear win; la moyenne de macro-F1 vs meilleure baseline est negative.",
        "learned_vs_shuffled_summary": "Quinze comparaisons restent proches du shuffle; seul le meilleur cas 1h validation reste legerement au-dessus mais non suffisant.",
        "model_collapse_summary": "Les modeles learned predisent presque exclusivement FLAT; les arbres depth-2 sont equivalants a une majority baseline sur validation/test.",
        "timeframe_collapse": collapse,
        "best_case_summary": _format_case(best_case),
        "worst_case_summary": _format_case(worst_case),
    }


def _build_label_diagnostic(dataset_validation: dict[str, Any], label_factory: dict[str, Any]) -> dict[str, Any]:
    target_name = dataset_validation.get("target_name")
    flat_ratio = dataset_validation.get("flat_ratio", {})
    majority_ratio = dataset_validation.get("majority_class_ratio", {})
    entropy = dataset_validation.get("entropy", {})
    target_distribution = dataset_validation.get("target_distribution", {})
    by_split = dataset_validation.get("target_distribution_by_split", {})
    by_year = dataset_validation.get("target_distribution_by_year", {})
    by_month = dataset_validation.get("target_distribution_by_month", {})
    alternative_labels = {}
    for timeframe, labels in label_factory.get("label_distribution", {}).items():
        if isinstance(labels, dict):
            alternative_labels[timeframe] = {label: {"flat_ratio": values.get("flat_ratio"), "majority_class_ratio": values.get("majority_class_ratio"), "entropy": values.get("entropy")} for label, values in labels.items() if isinstance(values, dict)}
    return {
        "target_name": target_name,
        "distribution_by_timeframe": target_distribution,
        "distribution_by_split": by_split,
        "distribution_by_year_available": bool(by_year),
        "distribution_by_month_available": bool(by_month),
        "majority_class_ratio": majority_ratio,
        "flat_ratio": flat_ratio,
        "entropy": entropy,
        "max_flat_ratio": _round(max(flat_ratio.values(), default=0.0) if isinstance(flat_ratio, dict) else 0.0),
        "min_entropy": _round(min(entropy.values(), default=0.0) if isinstance(entropy, dict) else 0.0),
        "label_too_flat_dominated": bool(isinstance(flat_ratio, dict) and max(flat_ratio.values(), default=0.0) >= 0.67),
        "three_class_structure_difficult": True,
        "h1_too_noisy": "possible",
        "h4_too_flat": "possible selon V9.40, a verifier dans une version dediee sans changer le label en V9.44",
        "binary_directional_more_relevant": "candidate_for_v9_45_or_later",
        "quantile_label_more_relevant": "candidate_for_v9_45_or_later",
        "transition_rate_available": False,
        "autocorrelation_available": False,
        "alternative_label_summary": alternative_labels,
        "diagnosis": "Le label contribue fortement au collapse FLAT, mais les ratios FLAT de 61-67% n'expliquent pas seuls l'incapacite des modeles a predire DOWN/UP.",
    }


def _build_feature_diagnostic(feature_validation: dict[str, Any], feature_store: dict[str, Any], ml_report: dict[str, Any]) -> dict[str, Any]:
    feature_columns = ml_report.get("feature_columns", feature_validation.get("feature_columns", []))
    missing_exact = {
        "median_trade_size_exact": "absent",
        "large_trade_count_exact": "absent",
        "buyer_maker_count_exact": "absent",
        "taker_buy_sell_count_exact": "absent",
        "trade_size_distribution_buckets": "absent",
    }
    families = feature_validation.get("feature_families", feature_store.get("feature_families", {}))
    agg_limitations = feature_validation.get("aggtrades_feature_limitations", {})
    return {
        "feature_columns_count": len(feature_columns),
        "feature_columns": feature_columns,
        "feature_families": families,
        "direct_aggtrades_full_scan_performed": False,
        "missing_exact_aggtrades_features": missing_exact,
        "aggtrades_feature_limitations": agg_limitations,
        "zero_trade_flags_present": any("zero_trade" in column for column in feature_columns),
        "warmup_impact_available": bool(feature_store.get("warmup_summary")),
        "features_too_aggregated": True,
        "relation_with_flat_collapse": "Les features agrégées ne donnent pas assez de separation directionnelle; les modeles reduisent le risque en predisant la classe majoritaire FLAT.",
        "recommended_next_feature_scope": [
            "recalcul exact buyer_maker/taker side depuis aggTrades silver",
            "distribution de tailles de trades",
            "large trade counts robustes par timeframe",
            "burst/intensity microstructure intrabar",
            "features de desequilibre acheteur/vendeur si reconstructibles sans endpoint prive",
        ],
    }


def _decide(ml_summary: dict[str, Any], label_diagnostic: dict[str, Any], feature_diagnostic: dict[str, Any]) -> tuple[str, str]:
    if ml_summary.get("baseline_clear_wins_count") == 0 and ml_summary.get("no_clear_edge_vs_shuffled_labels_count", 0) >= 12:
        if feature_diagnostic.get("features_too_aggregated"):
            return "feature_enrichment_before_more_ml", "V9.45 - AggTrades Exact Feature Enrichment"
        if label_diagnostic.get("label_too_flat_dominated"):
            return "label_redesign_before_more_ml", "V9.45 - 5Y Label Redesign"
    return "ml_diagnostic_inconclusive_manual_review_required", "V9.45 - Manual ML Diagnostic Pack"


def _build_warnings(ml_summary: dict[str, Any], label_diagnostic: dict[str, Any], feature_diagnostic: dict[str, Any]) -> list[str]:
    warnings = [
        "Walk-forward non justifie tant que les modeles learned ne battent pas clairement les baselines.",
        "Les resultats V9.43 ne doivent pas etre interpretes comme un signal actionnable.",
    ]
    if label_diagnostic.get("label_too_flat_dominated"):
        warnings.append("Le label principal est proche du seuil de dominance FLAT sur certains timeframes.")
    if feature_diagnostic.get("features_too_aggregated"):
        warnings.append("Les features aggTrades exactes sont absentes et doivent etre enrichies avant plus de ML lourd.")
    if ml_summary.get("no_clear_edge_vs_shuffled_labels_count", 0) > 0:
        warnings.append("Les comparaisons proches des labels melanges restent bloquantes pour toute decision research avancee.")
    return warnings


def _write_outputs(root: Path, report: dict[str, Any]) -> None:
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = _render_markdown(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    manifest = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": report["created_at_utc"],
        "decision": report["decision"],
        "next_recommendation": report["next_recommendation"],
        "artifacts": [REPORT_JSON_PATH.as_posix(), REPORT_MD_PATH.as_posix(), DOC_PATH.as_posix()],
        "inputs": report["inputs"],
        "diagnostic_only": True,
        "safety_flags": SAFETY_FLAGS,
        "findings": FINDINGS,
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    _write_json(root / MANIFEST_PATH, manifest)


def _update_current_state(root: Path, report: dict[str, Any]) -> None:
    latest_metrics_path = root / "reports/current/latest_metrics.json"
    if latest_metrics_path.exists():
        latest = _read_json(latest_metrics_path)
    else:
        latest = {}
    latest.update(
        {
            "last_validated_version": "V9.43",
            "candidate_version": VERSION,
            "candidate_status": "pending_external_audit",
            "direction": "ohlcv_aggtrades_5y_ml_diagnostic",
            "quality_status": report["status"],
            "decision_v9_44": report["decision"],
            "ml_diagnostic_v9_44_decision": report["decision"],
            "ml_diagnostic_v9_44_next_recommendation": report["next_recommendation"],
            "ml_diagnostic_v9_44_baseline_clear_wins_count": report["ml_result_summary"]["baseline_clear_wins_count"],
            "ml_diagnostic_v9_44_no_clear_edge_vs_shuffled_labels_count": report["ml_result_summary"]["no_clear_edge_vs_shuffled_labels_count"],
            "recommended_next_step": report["next_recommendation"],
            **SAFETY_FLAGS,
        }
    )
    _write_json(latest_metrics_path, latest)
    latest_md = (
        "# Latest Metrics\n\n"
        f"- Version candidate : `{VERSION}`.\n"
        "- Statut candidat : `pending_external_audit`.\n"
        f"- Decision V9.44 : `{report['decision']}`.\n"
        f"- Recommandation : `{report['next_recommendation']}`.\n"
        "- Diagnostic-only : aucun ML lourd, aucun backtest, aucun walk-forward, aucun signal.\n"
    )
    _write_text(root / "reports/current/latest_metrics.md", latest_md)
    summary = (
        "# Synthese courante\n\n"
        "V9.44 produit un diagnostic ML/feature/label a partir de V9.43. "
        "Les modeles learned restent proches des labels melanges, ne battent pas les baselines et collapsent presque toujours vers FLAT. "
        f"Decision : `{report['decision']}`. Prochaine etape recommandee : `{report['next_recommendation']}`.\n\n"
        "Aucun reseau, aucun telechargement, aucun backtest, aucun walk-forward, aucune strategie et aucun signal actionnable.\n"
    )
    _write_text(root / "reports/current/latest_summary.md", summary)
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(
        {
            "last_validated_version": "V9.43",
            "candidate_version": VERSION,
            "candidate_status": "pending_external_audit",
            "direction": "ohlcv_aggtrades_5y_ml_diagnostic",
            "decision_v9_44": report["decision"],
            "next_recommendation_v9_44": report["next_recommendation"],
            "ml_diagnostic_v9_44_created": True,
            "baseline_clear_wins_count_v9_44": report["ml_result_summary"]["baseline_clear_wins_count"],
            "no_clear_edge_vs_shuffled_labels_count_v9_44": report["ml_result_summary"]["no_clear_edge_vs_shuffled_labels_count"],
            **FINDINGS,
            **SAFETY_FLAGS,
        }
    )
    _write_json(state_path, state)
    _write_text(
        root / "reports/PROJECT_STATE.md",
        "# Etat Projet Galapagos\n\n"
        f"- Derniere version validee : `V9.43`.\n"
        f"- Version candidate : `{VERSION}`.\n"
        "- Statut candidat : `pending_external_audit`.\n"
        "- Direction : `ohlcv_aggtrades_5y_ml_diagnostic`.\n"
        f"- Decision candidate : `{report['decision']}`.\n"
        f"- Recommandation : `{report['next_recommendation']}`.\n"
        "- Aucun trading, paper live, ordre, backtest, walk-forward, strategie, signal, modele persistant, API privee, cle API, reseau ou telechargement.\n",
    )
    readme_path = root / "README.md"
    if readme_path.exists():
        readme = readme_path.read_text(encoding="utf-8")
    else:
        readme = "# Projet Galapagos\n"
    marker = "## V9.44 - 5Y ML Diagnostic / Feature & Label Review"
    block = (
        f"\n{marker}\n\n"
        "- Diagnostic-only sur les sorties V9.43.\n"
        f"- Decision : `{report['decision']}`.\n"
        f"- Recommandation : `{report['next_recommendation']}`.\n"
        "- Aucun reseau, aucun telechargement, aucun backtest, aucun walk-forward, aucune strategie, aucun signal actionnable.\n"
    )
    if marker not in readme:
        _write_text(readme_path, readme.rstrip() + "\n" + block)


def _render_markdown(report: dict[str, Any]) -> str:
    ml = report["ml_result_summary"]
    label = report["label_diagnostic"]
    feature = report["feature_diagnostic"]
    options = report["option_comparison"]
    lines = [
        "# Diagnostic ML/feature/label V9.44",
        "",
        f"- Version : `{VERSION}`.",
        f"- Source : `{SOURCE_VERSION}`.",
        f"- Decision : `{report['decision']}`.",
        f"- Recommandation : `{report['next_recommendation']}`.",
        "",
        "## Diagnostic ML",
        "",
        f"- Baseline clear wins : `{ml['baseline_clear_wins_count']}`.",
        f"- Comparaisons proches du shuffle : `{ml['no_clear_edge_vs_shuffled_labels_count']}`.",
        f"- Delta macro-F1 moyen vs meilleure baseline : `{ml['mean_delta_macro_f1_vs_best_baseline']}`.",
        f"- Synthese baselines : {ml['learned_vs_baseline_summary']}",
        f"- Synthese shuffle : {ml['learned_vs_shuffled_summary']}",
        f"- Collapse : {ml['model_collapse_summary']}",
        f"- Meilleur cas : {ml['best_case_summary']}.",
        f"- Pire cas : {ml['worst_case_summary']}.",
        "",
        "## Diagnostic label",
        "",
        f"- Label : `{label['target_name']}`.",
        f"- Ratio FLAT par timeframe : `{label['flat_ratio']}`.",
        f"- Entropie par timeframe : `{label['entropy']}`.",
        f"- Diagnostic : {label['diagnosis']}",
        "",
        "## Diagnostic features",
        "",
        f"- Nombre de features : `{feature['feature_columns_count']}`.",
        f"- Scan direct aggTrades full : `{feature['direct_aggtrades_full_scan_performed']}`.",
        f"- Features exactes manquantes : `{feature['missing_exact_aggtrades_features']}`.",
        f"- Relation au collapse : {feature['relation_with_flat_collapse']}",
        "",
        "## Comparaison options",
        "",
    ]
    for name, payload in options.items():
        lines.append(f"- `{name}` : `{payload['rating']}` - {payload['reason']}")
    lines.extend(
        [
            "",
            "## Garde-fous",
            "",
            "- Aucun trading.",
            "- Aucun paper live.",
            "- Aucun ordre.",
            "- Aucun backtest.",
            "- Aucun walk-forward.",
            "- Aucune strategie.",
            "- Aucun signal actionnable.",
            "- Aucun modele persistant.",
            "- Aucun reseau.",
            "- Aucun telechargement de nouvelles donnees.",
            "- Aucune suppression destructive.",
            "- Aucun sidecar et aucune empreinte ZIP.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_case(case: dict[str, Any] | None) -> str:
    if not case:
        return "n/a"
    return (
        f"{case['timeframe']} {case['model_name']} {case['split']} "
        f"macro_f1={_round(case['macro_f1'])}, balanced_accuracy={_round(case['balanced_accuracy'])}, "
        f"flat_prediction_ratio={_round(case['flat_prediction_ratio'])}"
    )


def _round(value: Any, digits: int = 6) -> Any:
    if isinstance(value, float):
        return round(value, digits)
    return value


def _mean(values: list[float]) -> float:
    finite = [float(value) for value in values if isinstance(value, (int, float)) and math.isfinite(float(value))]
    return sum(finite) / len(finite) if finite else 0.0


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
