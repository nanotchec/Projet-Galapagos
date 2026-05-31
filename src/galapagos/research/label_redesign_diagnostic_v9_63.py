from __future__ import annotations

import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


VERSION = "V9.63"
SOURCE_VERSION = "V9.59_to_V9.62"
DIRECTION = "label_redesign_diagnostic"
REPORT_JSON_PATH = Path("reports/research_decisions/label_redesign_diagnostic_v9_63.json")
REPORT_MD_PATH = Path("reports/research_decisions/label_redesign_diagnostic_v9_63.md")
MANIFEST_PATH = Path("reports/manifests/label_redesign_diagnostic_v9_63_manifest.json")

INPUT_PATHS = {
    "v9_59_to_v9_62_chain": Path("reports/research_decisions/funding_common_window_ml_chain_v9_59_to_v9_62.json"),
    "v9_62_ml": Path("reports/ml/ohlcv_aggtrades_exact_funding_5y_offline_ml_v9_62.json"),
    "v9_62_scores": Path("reports/ml/ohlcv_aggtrades_exact_funding_5y_offline_scores_v9_62.json"),
    "v9_48_to_v9_51_protocol": Path("reports/research_decisions/ohlcv_aggtrades_exact_5y_protocol_v9_48_to_v9_51.json"),
    "v9_51_ml": Path("reports/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.json"),
    "v9_51_scores": Path("reports/ml/ohlcv_aggtrades_exact_5y_offline_scores_v9_51.json"),
    "v9_43_ml": Path("reports/ml/ohlcv_aggtrades_5y_offline_ml_v9_43.json"),
    "v9_40_label_factory": Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json"),
    "v9_40_label_distribution": Path("reports/labels/ohlcv_aggtrades_5y_label_distribution_v9_40.json"),
    "v9_42_dataset_validation": Path("reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
}

ALLOWED_DECISIONS = {
    "label_redesign_candidate_binary_directional",
    "label_redesign_candidate_quantile_directional",
    "label_redesign_candidate_multiclass_quantile",
    "label_redesign_manual_review_required",
    "label_redesign_not_recommended",
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
    "no_ml": True,
    "no_dataset_supervised": True,
    "no_strategy": True,
    "no_actionable_signal": True,
    "no_persistent_model": True,
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


def run_label_redesign_diagnostic_v9_63(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_label_redesign_diagnostic_v9_63(root)
    _write_json(root / REPORT_JSON_PATH, report)
    _write_text(root / REPORT_MD_PATH, markdown_v9_63(report))
    _write_json(root / MANIFEST_PATH, manifest_v9_63(report))
    return report


def build_label_redesign_diagnostic_v9_63(root: Path) -> dict[str, Any]:
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    missing = [name for name, block in inputs.items() if not block["available"] and name != "latest_summary"]
    v9_62 = inputs["v9_62_ml"]["payload"]
    v9_40_distribution = inputs["v9_40_label_distribution"]["payload"]

    current_target = summarize_current_target(v9_62, v9_40_distribution)
    candidate_options = evaluate_candidate_options(v9_40_distribution)
    historical_ml = summarize_historical_ml(inputs)
    selected = select_candidate(candidate_options, current_target, missing)
    decision = selected["decision"]
    status = "PASS" if decision != "label_redesign_manual_review_required" and decision != "label_redesign_not_recommended" else "REVIEW"
    warnings = []
    if current_target["class_collapse_warning_count"] > 0:
        warnings.append("class collapse persistant avec le label actuel")
    if current_target["flat_dominance_detected"]:
        warnings.append("dominance FLAT descriptive du target actuel")
    if missing:
        warnings.append(f"rapports manquants non bloquants pour diagnostic descriptif: {', '.join(missing)}")
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": status,
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "question": "Un label alternatif ameliore-t-il la separabilite offline sans fuite et sans collapse ?",
        "inputs": inputs,
        "current_target_diagnostic": current_target,
        "historical_ml_summary": historical_ml,
        "candidate_options": candidate_options,
        "selected_primary_label": selected["selected_primary_label"],
        "selected_label_family": selected["selected_label_family"],
        "selection_reason": selected["selection_reason"],
        "selection_methodology": {
            "selected_from_distribution_causality_stability": True,
            "selected_from_ml_performance": False,
            "validation_or_test_used_for_threshold_choice": False,
            "future_volatility_used": False,
            "random_split_used": False,
        },
        "decision": decision,
        "next_recommendation": recommendation_v9_63(decision),
        "warnings": warnings,
        "errors": [] if not missing else [],
        "limitations": [
            "V9.63 est un diagnostic plan-only et report-only.",
            "Aucun label, dataset, ML, backtest, walk-forward, strategie ou signal n'est cree.",
            "La selection est methodologique; elle ne revendique aucune performance future.",
        ],
        "runtime_seconds": round(time.monotonic() - started, 3),
        "labels_created": False,
        "dataset_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "findings": dict(FINDINGS),
        "safety_flags": dict(SAFETY_FLAGS),
    }
    if report["decision"] not in ALLOWED_DECISIONS:
        raise RuntimeError(f"invalid V9.63 decision: {report['decision']}")
    return report


def summarize_current_target(v9_62: dict[str, Any], v9_40_distribution: dict[str, Any]) -> dict[str, Any]:
    current_label = "up_down_flat_volnorm_h1_5y"
    distributions = {timeframe: labels.get(current_label, {}) for timeframe, labels in v9_40_distribution.items()}
    flat_ratios = [float(item.get("flat_ratio", 0.0)) for item in distributions.values() if item]
    majority_ratios = [float(item.get("majority_class_ratio", 0.0)) for item in distributions.values() if item]
    return {
        "current_label": current_label,
        "v9_62_decision": v9_62.get("decision"),
        "baseline_clear_wins": v9_62.get("baseline_comparison", {}).get("clear_wins_count"),
        "funding_clear_improvements": v9_62.get("funding_ablation_comparison", {}).get("clear_improvement_with_funding_count"),
        "no_clear_edge_vs_shuffled_labels_count": v9_62.get("no_clear_edge_vs_shuffled_labels_count"),
        "class_collapse_warning_count": v9_62.get("class_collapse_analysis", {}).get("collapse_warning_count", 0),
        "distributions_by_timeframe": distributions,
        "mean_flat_ratio": round(sum(flat_ratios) / len(flat_ratios), 6) if flat_ratios else 0.0,
        "max_majority_ratio": round(max(majority_ratios), 6) if majority_ratios else 0.0,
        "flat_dominance_detected": bool(flat_ratios and max(flat_ratios) >= 0.60),
    }


def evaluate_candidate_options(v9_40_distribution: dict[str, Any]) -> dict[str, Any]:
    return {
        "A_binary_directional_volnorm_h1_5y": {
            "status": "candidate_requires_factory",
            "label_family": "binary_directional",
            "horizon": "h1",
            "rationale": "supprime FLAT mais horizon court possiblement bruite; a produire en V9.64 pour diagnostic.",
        },
        "B_binary_directional_volnorm_h4_5y": option_from_existing_distribution(v9_40_distribution, "binary_directional_volnorm_h4_5y", "binary_directional", "h4"),
        "C_quantile_directional_h1_5y": {
            "status": "diagnostic_candidate",
            "label_family": "quantile_directional",
            "horizon": "h1",
            "rationale": "seuils train-only possibles, mais moins interpretable qu'un label directionnel causal simple.",
        },
        "D_quantile_directional_h4_5y": {
            "status": "diagnostic_candidate",
            "label_family": "quantile_directional",
            "horizon": "h4",
            "rationale": "quantiles train-only possibles, mais choix de seuils plus fragile pour audit.",
        },
        "E_up_down_flat_quantile_h1_5y": {
            "status": "secondary_candidate",
            "label_family": "multiclass_quantile",
            "horizon": "h1",
            "rationale": "peut equilibrer les classes, mais reintroduit une classe neutre et un risque de collapse multiclass.",
        },
        "F_keep_current_label": {
            "status": "not_recommended",
            "label_family": "current_multiclass_volnorm",
            "rationale": "class collapse et dominance FLAT persistent dans V9.62.",
        },
    }


def option_from_existing_distribution(distribution: dict[str, Any], label: str, family: str, horizon: str) -> dict[str, Any]:
    blocks = {timeframe: labels.get(label, {}) for timeframe, labels in distribution.items()}
    majority = [float(item.get("majority_class_ratio", 1.0)) for item in blocks.values() if item]
    entropy = [float(item.get("entropy", 0.0)) for item in blocks.values() if item]
    return {
        "status": "recommended_primary_candidate",
        "label": label,
        "label_family": family,
        "horizon": horizon,
        "distribution_by_timeframe": blocks,
        "max_majority_class_ratio": round(max(majority), 6) if majority else None,
        "mean_entropy": round(sum(entropy) / len(entropy), 6) if entropy else None,
        "rationale": "distribution proche 50/50 dans V9.40, pas de classe FLAT, causalite deja documentee; choix non fonde sur un resultat ML.",
    }


def summarize_historical_ml(inputs: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in ("v9_43_ml", "v9_51_ml", "v9_62_ml"):
        payload = inputs[key]["payload"]
        result[key] = {
            "available": inputs[key]["available"],
            "decision": payload.get("decision"),
            "class_collapse_warning_count": payload.get("class_collapse_analysis", {}).get("collapse_warning_count"),
            "baseline_clear_wins": payload.get("baseline_comparison", {}).get("clear_wins_count"),
            "no_clear_edge_vs_shuffled_labels_count": payload.get("no_clear_edge_vs_shuffled_labels_count"),
        }
    return result


def select_candidate(options: dict[str, Any], current_target: dict[str, Any], missing: list[str]) -> dict[str, str]:
    binary_h4 = options["B_binary_directional_volnorm_h4_5y"]
    if missing and "v9_40_label_distribution" in missing:
        return {
            "decision": "label_redesign_manual_review_required",
            "selected_primary_label": "none",
            "selected_label_family": "none",
            "selection_reason": "distribution V9.40 manquante",
        }
    if binary_h4.get("max_majority_class_ratio") is not None and binary_h4["max_majority_class_ratio"] <= 0.55:
        return {
            "decision": "label_redesign_candidate_binary_directional",
            "selected_primary_label": "binary_directional_volnorm_h4_5y",
            "selected_label_family": "binary_directional",
            "selection_reason": "le candidat binaire h4 retire la classe FLAT, conserve une distribution descriptive proche 50/50 et reste causalement interpretable.",
        }
    if current_target["flat_dominance_detected"]:
        return {
            "decision": "label_redesign_candidate_quantile_directional",
            "selected_primary_label": "quantile_directional_h4_5y",
            "selected_label_family": "quantile_directional",
            "selection_reason": "le binaire h4 existant n'est pas assez stable; quantile h4 train-only a tester comme alternative.",
        }
    return {
        "decision": "label_redesign_not_recommended",
        "selected_primary_label": "up_down_flat_volnorm_h1_5y",
        "selected_label_family": "current_multiclass_volnorm",
        "selection_reason": "les criteres descriptifs ne justifient pas un redesign automatique.",
    }


def recommendation_v9_63(decision: str) -> str:
    if decision.startswith("label_redesign_candidate_"):
        return "V9.64 - Label Candidate Factory"
    if decision == "label_redesign_manual_review_required":
        return "V9.64 - Manual Label Review Pack"
    return "V9.64 - Stop or manual research decision"


def manifest_v9_63(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "created_at_utc": report["created_at_utc"],
        "decision": report["decision"],
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "selected_primary_label": report["selected_primary_label"],
        "quality_status": report["status"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def markdown_v9_63(report: dict[str, Any]) -> str:
    return (
        "# V9.63 - Diagnostic redesign label\n\n"
        f"- Decision : `{report['decision']}`.\n"
        f"- Label principal candidat : `{report['selected_primary_label']}`.\n"
        f"- Famille : `{report['selected_label_family']}`.\n"
        f"- Raison : {report['selection_reason']}\n"
        f"- Collapse V9.62 : `{report['current_target_diagnostic']['class_collapse_warning_count']}` avertissements.\n"
        f"- Flat ratio moyen target actuel : `{report['current_target_diagnostic']['mean_flat_ratio']}`.\n\n"
        "Aucun label, dataset, ML, backtest, walk-forward, strategie, signal, ordre, reseau ou telechargement n'est execute en V9.63.\n"
    )


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    if path.suffix == ".md":
        payload: Any = full.read_text(encoding="utf-8") if full.is_file() else ""
    else:
        payload = _read_json(full) if full.is_file() else {}
    return {"path": path.as_posix(), "available": full.is_file(), "payload": payload}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
