from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.datasets.h4_label_candidate_dataset_v9_13_schemas import ML_FEATURE_COLUMNS_V9_13, TARGET_NAME_V9_13, TIMEFRAMES_V9_13


VERSION = "V9.14"
LAST_VALIDATED_VERSION = "V9.13"
DECISION_TYPE = "feature_label_separability_and_branch_decision"
WINDOW = {"window_start": "2023-03-25", "window_end": "2024-03-24", "total_days": 366}
REPORT_JSON_PATH = Path("reports/research_decisions/feature_label_separability_v9_14.json")
REPORT_MD_PATH = Path("reports/research_decisions/feature_label_separability_v9_14.md")
MANIFEST_PATH = Path("reports/manifests/feature_label_separability_v9_14_manifest.json")
DOC_PATH = Path("docs/feature_label_separability_v9_14.md")

ALLOWED_DECISIONS = {
    "feature_first_before_more_labels",
    "label_redesign_binary_directional_candidate",
    "label_redesign_quantile_candidate",
    "extend_data_first_before_more_labels",
    "stop_refined_label_branch",
    "inconclusive_need_manual_review",
}

INPUT_PATHS = {
    "v9_13_dataset": Path("reports/datasets/h4_label_candidate_dataset_v9_13.json"),
    "v9_13_ml": Path("reports/ml/h4_label_candidate_offline_ml_v9_13.json"),
    "v9_13_scores": Path("reports/ml/h4_label_candidate_offline_scores_v9_13.json"),
    "v9_12_labels": Path("reports/labels/horizon_event_label_redesign_v9_12.json"),
    "v9_11_failure": Path("reports/research_decisions/label_failure_analysis_v9_11.json"),
    "v9_10_decision": Path("reports/research_decisions/refined_volnorm_research_decision_gate_v9_10.json"),
    "v9_8_ml": Path("reports/ml/refined_volnorm_labels_offline_ml_v9_8.json"),
    "v9_9_walk_forward": Path("reports/ml/refined_volnorm_strict_walk_forward_v9_9.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
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

SAFETY = {
    "public_read_only": True,
    "authentication_used": False,
    "api_key_used": False,
    "private_endpoint_used": False,
    "orders_enabled": False,
    "paper_live_enabled": False,
    "trading_enabled": False,
    "labels_generated": False,
    "dataset_generated": False,
    "ml_training_enabled": False,
    "walk_forward_enabled": False,
    "backtest_enabled": False,
    "strategy_enabled": False,
    "execution_enabled": False,
    "persistent_model_created": False,
    "sidecars_created": False,
    "zip_fingerprints_created": False,
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
    "api_key_used": False,
    "private_endpoint_used": False,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}

FORBIDDEN_METRIC_TERMS = {"pnl", "sharpe", "drawdown", "equity_curve", "profit_factor"}
TARGET_CLASSES = ["DOWN", "FLAT", "UP"]


def run_feature_label_separability_v9_14(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_feature_label_separability_report_v9_14(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_14(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    manifest = build_manifest_v9_14(root, report)
    _write_json(root / MANIFEST_PATH, manifest)
    update_state_surfaces_v9_14(root, report)
    return report


def build_feature_label_separability_report_v9_14(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    payloads = {name: item["payload"] for name, item in inputs.items()}
    label_diagnostic = analyze_label_diagnostic_v9_14(root, payloads["v9_13_dataset"], payloads["v9_12_labels"])
    ml_diagnostic = analyze_ml_diagnostic_v9_14(payloads["v9_13_ml"], payloads["v9_8_ml"], payloads["v9_9_walk_forward"])
    separability = analyze_feature_label_separability_v9_14(root, payloads["v9_13_dataset"])
    hypotheses = classify_hypotheses_v9_14(label_diagnostic, ml_diagnostic, separability)
    decision = decide_v9_14(hypotheses, ml_diagnostic, separability)
    return {
        "version": VERSION,
        "status": "PASS",
        "decision_type": DECISION_TYPE,
        "created_at_utc": _utc_now(),
        "inputs": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "window": WINDOW,
        "target_name": TARGET_NAME_V9_13,
        "feature_columns": ML_FEATURE_COLUMNS_V9_13,
        "feature_columns_count": len(ML_FEATURE_COLUMNS_V9_13),
        "full_data_available": label_diagnostic["full_parquet_read_only_used"] and separability["full_parquet_read_only_used"],
        "label_diagnostic_v9_13": label_diagnostic,
        "ml_diagnostic_v9_13": ml_diagnostic,
        "feature_label_separability": separability,
        "hypotheses": hypotheses,
        "v9_14_decision": decision,
        "next_step_recommendation": decision["next_step_recommendation"],
        "forbidden_metric_scan": forbidden_metric_scan_v9_14({"ml": ml_diagnostic, "separability": separability}),
        "findings": dict(FINDINGS),
        "safety": dict(SAFETY),
        "safety_flags": dict(SAFETY_FLAGS),
        "limitations": [
            "V9.14 est une analyse descriptive de separabilite features/labels et une decision de branche.",
            "V9.14 ne cree aucun nouveau label full, aucun modele ML, aucun walk-forward, aucun backtest, aucune strategie, aucun signal actionnable et aucun ordre.",
            "Les scores de separabilite ne constituent pas des signaux et ne justifient aucun trading.",
        ],
    }


def analyze_label_diagnostic_v9_14(root: Path, dataset_report: dict[str, Any], v9_12_report: dict[str, Any]) -> dict[str, Any]:
    timeframes: dict[str, Any] = {}
    full_available = True
    for timeframe in TIMEFRAMES_V9_13:
        output = dataset_report.get("outputs", {}).get(timeframe, {})
        dataset_path = root / output.get("path", "")
        full_available = full_available and dataset_path.is_file()
        base = {
            "timeframe": timeframe,
            "rows": output.get("rows"),
            "class_distribution": dataset_report.get("target_distributions", {}).get(timeframe, {}).get("class_distribution", {}),
            "split_distribution": {},
            "walk_forward_group_distribution": {},
            "flat_too_low": False,
            "flat_too_high": False,
            "data_source": "report_only",
        }
        flat_rate = base["class_distribution"].get("FLAT", {}).get("rate")
        if isinstance(flat_rate, (int, float)):
            base["flat_too_low"] = flat_rate < 0.10
            base["flat_too_high"] = flat_rate > 0.55
        if dataset_path.is_file():
            frame = pd.read_parquet(
                dataset_path,
                columns=["split", "walk_forward_group", TARGET_NAME_V9_13, "label_valid", "warmup_row"],
                engine="pyarrow",
            )
            valid = frame[(frame["label_valid"] == True) & (frame["warmup_row"] == False)].copy()  # noqa: E712
            base["split_distribution"] = distribution_by_group_v9_14(valid, "split", TARGET_NAME_V9_13)
            base["walk_forward_group_distribution"] = distribution_by_group_v9_14(valid, "walk_forward_group", TARGET_NAME_V9_13)
            base["data_source"] = "full_parquet_read_only"
        timeframes[timeframe] = base
    recommended = v9_12_report.get("recommended_candidate", {})
    return {
        "target_name": TARGET_NAME_V9_13,
        "full_parquet_read_only_used": full_available,
        "v9_12_recommended_candidate": {
            "target_name": recommended.get("target_name"),
            "horizon_name": recommended.get("horizon_name"),
            "multiplier": recommended.get("multiplier"),
            "candidate_family": recommended.get("candidate_family"),
        },
        "timeframes": timeframes,
        "flat_low_timeframes": [tf for tf, item in timeframes.items() if item["flat_too_low"]],
        "flat_high_timeframes": [tf for tf, item in timeframes.items() if item["flat_too_high"]],
        "comparison_with_v9_6_v9_12": {
            "v9_6_target": "up_down_flat_volnorm_h1",
            "v9_12_selected_target": "up_down_flat_volnorm_h4",
            "interpretation": "Le h4 reduit le bruit h1 de facon descriptive, mais V9.13 reste proche des labels melanges.",
        },
    }


def analyze_ml_diagnostic_v9_14(v9_13_ml: dict[str, Any], v9_8_ml: dict[str, Any], v9_9_walk_forward: dict[str, Any]) -> dict[str, Any]:
    metrics = v9_13_ml.get("metrics", {})
    learned = [
        item
        for item in metrics.values()
        if item.get("model_name") in {"logistic_regression", "decision_tree_depth_2"} and item.get("split") in {"validation", "test"}
    ]
    collapse_cases = []
    for key, item in metrics.items():
        pred_distribution = item.get("class_distribution_pred", {})
        missing_classes = [label for label in TARGET_CLASSES if int(pred_distribution.get(label, 0)) == 0]
        rows = max(int(item.get("rows", 0)), 1)
        max_pred_rate = max((int(value) / rows for value in pred_distribution.values()), default=0.0)
        if missing_classes or max_pred_rate > 0.90:
            collapse_cases.append(
                {
                    "metric_key": key,
                    "timeframe": item.get("timeframe"),
                    "split": item.get("split"),
                    "model_name": item.get("model_name"),
                    "missing_predicted_classes": missing_classes,
                    "max_predicted_class_rate": max_pred_rate,
                    "class_distribution_pred": pred_distribution,
                    "confusion_matrix": item.get("confusion_matrix"),
                }
            )
    best_cases = sorted(learned, key=lambda item: (item.get("macro_f1", 0.0), item.get("balanced_accuracy", 0.0)), reverse=True)[:5]
    worst_cases = sorted(learned, key=lambda item: (item.get("macro_f1", 0.0), item.get("balanced_accuracy", 0.0)))[:5]
    shuffle = v9_13_ml.get("label_shuffle_falsification", {})
    no_clear_cases = [item for item in shuffle.values() if item.get("no_clear_edge_vs_shuffled_labels")]
    deltas = [float(item.get("delta_original_vs_shuffled", 0.0)) for item in shuffle.values()]
    return {
        "decision": v9_13_ml.get("decision"),
        "global_decision": v9_13_ml.get("global_decision", {}).get("decision"),
        "learned_vs_baselines": {
            "clear_wins_count": v9_13_ml.get("baseline_comparison", {}).get("clear_wins_count"),
            "mean_delta_macro_f1_vs_best_baseline": v9_13_ml.get("baseline_comparison", {}).get("mean_delta_macro_f1_vs_best_baseline"),
            "interpretation": "Aucun modele appris ne bat clairement les baselines sur V9.13.",
        },
        "learned_vs_shuffled_labels": {
            "no_clear_edge_vs_shuffled_labels_count": len(no_clear_cases),
            "mean_delta_original_vs_shuffled": sum(deltas) / len(deltas) if deltas else None,
            "min_delta_original_vs_shuffled": min(deltas) if deltas else None,
            "max_delta_original_vs_shuffled": max(deltas) if deltas else None,
        },
        "class_collapse_cases": collapse_cases,
        "class_collapse_cases_count": len(collapse_cases),
        "best_cases": best_cases,
        "worst_cases": worst_cases,
        "comparison_v9_8_v9_13": v9_13_ml.get("comparison_with_v9_8", {}),
        "v9_8_decision": v9_8_ml.get("decision"),
        "v9_9_decision": v9_9_walk_forward.get("decision"),
        "walk_forward_not_repeated_in_v9_14": True,
    }


def analyze_feature_label_separability_v9_14(root: Path, dataset_report: dict[str, Any]) -> dict[str, Any]:
    by_timeframe: dict[str, Any] = {}
    full_available = True
    for timeframe in TIMEFRAMES_V9_13:
        dataset_path = root / dataset_report.get("outputs", {}).get(timeframe, {}).get("path", "")
        full_available = full_available and dataset_path.is_file()
        if not dataset_path.is_file():
            by_timeframe[timeframe] = {"timeframe": timeframe, "data_source": "missing_full_parquet", "feature_scores": [], "top_features": []}
            continue
        frame = pd.read_parquet(
            dataset_path,
            columns=[*ML_FEATURE_COLUMNS_V9_13, TARGET_NAME_V9_13, "split", "label_valid", "warmup_row"],
            engine="pyarrow",
        )
        frame = frame[(frame["label_valid"] == True) & (frame["warmup_row"] == False)].copy()  # noqa: E712
        feature_scores = compute_univariate_separability_v9_14(frame, ML_FEATURE_COLUMNS_V9_13, TARGET_NAME_V9_13)
        split_scores = {
            split: compute_univariate_separability_v9_14(split_frame, ML_FEATURE_COLUMNS_V9_13, TARGET_NAME_V9_13)[:5]
            for split, split_frame in frame.groupby("split", sort=True)
        }
        by_timeframe[timeframe] = {
            "timeframe": timeframe,
            "data_source": "full_parquet_read_only",
            "rows_used": int(len(frame)),
            "feature_scores": feature_scores,
            "top_features": [item["feature_name"] for item in feature_scores[:5]],
            "weak_features": [item["feature_name"] for item in feature_scores if item["eta_squared"] < 0.001 and item["standardized_class_mean_range"] < 0.05],
            "split_top_features": {split: [item["feature_name"] for item in scores] for split, scores in split_scores.items()},
            "class_separability": class_separability_v9_14(frame, ML_FEATURE_COLUMNS_V9_13, TARGET_NAME_V9_13),
        }
    top_sets = [set(item.get("top_features", [])) for item in by_timeframe.values() if item.get("top_features")]
    common_top = sorted(set.intersection(*top_sets)) if top_sets else []
    top_counts: dict[str, int] = {}
    for item in by_timeframe.values():
        for feature in item.get("top_features", []):
            top_counts[feature] = top_counts.get(feature, 0) + 1
    unstable_top = sorted([feature for feature, count in top_counts.items() if top_sets and count < len(top_sets)])
    no_discrimination = sorted(set.intersection(*[set(item.get("weak_features", [])) for item in by_timeframe.values() if item.get("weak_features")])) if by_timeframe else []
    return {
        "full_parquet_read_only_used": full_available,
        "method": "eta_squared_and_standardized_class_mean_range_by_feature",
        "model_training_performed": False,
        "signal_produced": False,
        "by_timeframe": by_timeframe,
        "common_top_features_between_timeframes": common_top,
        "unstable_top_features": unstable_top,
        "features_with_low_univariate_discrimination_all_timeframes": no_discrimination,
        "summary": {
            "common_top_features_count": len(common_top),
            "unstable_top_features_count": len(unstable_top),
            "low_discrimination_features_count": len(no_discrimination),
        },
    }


def compute_univariate_separability_v9_14(frame: pd.DataFrame, features: list[str], target: str) -> list[dict[str, Any]]:
    scores: list[dict[str, Any]] = []
    for feature in features:
        series = pd.to_numeric(frame[feature], errors="coerce")
        valid = frame[[target]].copy()
        valid[feature] = series
        valid = valid.dropna(subset=[feature, target])
        total_var = float(valid[feature].var(ddof=0) or 0.0)
        global_mean = float(valid[feature].mean()) if len(valid) else 0.0
        grouped = valid.groupby(target)[feature]
        class_means = {str(k): float(v) for k, v in grouped.mean().to_dict().items()}
        class_counts = {str(k): int(v) for k, v in grouped.count().to_dict().items()}
        if total_var > 0 and len(valid):
            between = sum(count * (class_means[label] - global_mean) ** 2 for label, count in class_counts.items()) / len(valid)
            eta_squared = max(0.0, min(1.0, between / total_var))
            standardized_range = (max(class_means.values()) - min(class_means.values())) / (total_var ** 0.5) if class_means else 0.0
        else:
            eta_squared = 0.0
            standardized_range = 0.0
        scores.append(
            {
                "feature_name": feature,
                "eta_squared": eta_squared,
                "standardized_class_mean_range": standardized_range,
                "class_means": class_means,
                "class_counts": class_counts,
            }
        )
    return sorted(scores, key=lambda item: (item["eta_squared"], item["standardized_class_mean_range"]), reverse=True)


def class_separability_v9_14(frame: pd.DataFrame, features: list[str], target: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for label in TARGET_CLASSES:
        label_scores = []
        for feature in features:
            series = pd.to_numeric(frame[feature], errors="coerce")
            std = float(series.std(ddof=0) or 0.0)
            if std <= 0:
                continue
            class_values = series[frame[target] == label].dropna()
            other_values = series[frame[target] != label].dropna()
            if class_values.empty or other_values.empty:
                continue
            label_scores.append(abs(float(class_values.mean()) - float(other_values.mean())) / std)
        result[label] = {
            "mean_one_vs_rest_standardized_difference": sum(label_scores) / len(label_scores) if label_scores else 0.0,
            "features_evaluated": len(label_scores),
        }
    weakest = min(result.items(), key=lambda item: item[1]["mean_one_vs_rest_standardized_difference"])[0] if result else None
    return {"by_class": result, "weakest_class": weakest}


def classify_hypotheses_v9_14(label_diagnostic: dict[str, Any], ml_diagnostic: dict[str, Any], separability: dict[str, Any]) -> list[dict[str, Any]]:
    clear_wins = int(ml_diagnostic["learned_vs_baselines"].get("clear_wins_count") or 0)
    no_clear = int(ml_diagnostic["learned_vs_shuffled_labels"].get("no_clear_edge_vs_shuffled_labels_count") or 0)
    common_top = int(separability["summary"]["common_top_features_count"])
    unstable_top = int(separability["summary"]["unstable_top_features_count"])
    return [
        {"id": "H1", "hypothesis": "label encore mal defini", "support": "high" if no_clear >= 10 else "medium", "evidence": f"{no_clear} cas restent trop proches des labels melanges."},
        {"id": "H2", "hypothesis": "features actuelles insuffisantes", "support": "high" if clear_wins == 0 and common_top <= 1 else "medium", "evidence": f"clear wins={clear_wins}, top features communes={common_top}."},
        {"id": "H3", "hypothesis": "horizon h4 pas adapte", "support": "medium", "evidence": "Le h4 ameliore legerement la distance aux labels melanges mais reste insuffisant."},
        {"id": "H4", "hypothesis": "multi-classe DOWN/FLAT/UP trop difficile", "support": "medium", "evidence": "Les distributions extremes du FLAT en 1m et 1h persistent."},
        {"id": "H5", "hypothesis": "fenetre 2023-2024 trop limitee", "support": "medium", "evidence": "La stabilite regime/fenetre reste non prouvee sans extension de donnees."},
        {"id": "H6", "hypothesis": "OHLCV+trades agreges peu informatifs", "support": "high" if unstable_top >= 8 else "medium", "evidence": f"top features instables={unstable_top}."},
        {"id": "H7", "hypothesis": "extension data/features avant nouveau label", "support": "high", "evidence": "Les labels h1 puis h4 ne rendent pas les modeles clairement falsifiables."},
        {"id": "H8", "hypothesis": "arret de branche refined labels", "support": "medium", "evidence": "Plusieurs redesign labels successifs restent proches du shuffle; arret possible si feature/data-first echoue."},
    ]


def decide_v9_14(hypotheses: list[dict[str, Any]], ml_diagnostic: dict[str, Any], separability: dict[str, Any]) -> dict[str, Any]:
    clear_wins = int(ml_diagnostic["learned_vs_baselines"].get("clear_wins_count") or 0)
    no_clear = int(ml_diagnostic["learned_vs_shuffled_labels"].get("no_clear_edge_vs_shuffled_labels_count") or 0)
    common_top = int(separability["summary"]["common_top_features_count"])
    if clear_wins == 0 and no_clear >= 10 and common_top <= 1:
        decision = "feature_first_before_more_labels"
        recommendation = "V9.15 Feature Separability / Feature Refinement Candidate."
        confidence = "medium"
        justification = "Les labels h4 restent proches du shuffle et les features ne montrent pas une separabilite commune stable entre timeframes."
    elif clear_wins == 0 and no_clear >= 10:
        decision = "extend_data_first_before_more_labels"
        recommendation = "V9.15 Data Window Extension Diagnostic."
        confidence = "medium"
        justification = "Les resultats restent faibles; l'extension de fenetre peut verifier si le probleme vient du regime 2023-2024."
    else:
        decision = "inconclusive_need_manual_review"
        recommendation = "Revue manuelle des diagnostics avant toute nouvelle version."
        confidence = "low"
        justification = "Les diagnostics ne suffisent pas a choisir un redesign label unique."
    return {
        "decision": decision,
        "confidence": confidence,
        "justification": justification,
        "next_step_recommendation": recommendation,
        "explicit_no_backtest_statement": "Aucun backtest n'est justifie ou execute par V9.14.",
        "explicit_no_trading_statement": "V9.14 n'autorise aucun trading, paper live, ordre, strategie ou signal actionnable.",
    }


def distribution_by_group_v9_14(frame: pd.DataFrame, group_column: str, target_column: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for group_value, group in frame.groupby(group_column, sort=True):
        counts = group[target_column].value_counts().reindex(TARGET_CLASSES, fill_value=0)
        total = int(counts.sum())
        result[str(group_value)] = {
            label: {"count": int(count), "rate": float(count / total) if total else 0.0}
            for label, count in counts.items()
        }
    return result


def forbidden_metric_scan_v9_14(payload: dict[str, Any]) -> dict[str, Any]:
    text = json.dumps(payload, ensure_ascii=False).casefold()
    hits = sorted(term for term in FORBIDDEN_METRIC_TERMS if term in text)
    return {"passed": not hits, "forbidden_terms_present": hits}


def build_manifest_v9_14(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "decision_type": DECISION_TYPE,
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "inputs": report["inputs"],
        "target_name": report["target_name"],
        "full_data_available": report["full_data_available"],
        "v9_14_decision": report["v9_14_decision"],
        "findings": report["findings"],
        "safety": report["safety"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_14(report: dict[str, Any]) -> str:
    decision = report["v9_14_decision"]
    labels = report["label_diagnostic_v9_13"]
    ml = report["ml_diagnostic_v9_13"]
    sep = report["feature_label_separability"]
    lines = [
        "# V9.14 - Feature/Label Separability Diagnostic & Next Branch Decision",
        "",
        "## Executive summary",
        f"- Decision : `{decision['decision']}`.",
        f"- Justification : {decision['justification']}",
        "- V9.14 est une analyse descriptive offline, pas un walk-forward et pas un backtest.",
        "- Aucun trading, aucun paper live, aucun ordre, aucune strategie, aucun signal actionnable.",
        "",
        "## Diagnostic labels V9.13",
        f"- Target : `{report['target_name']}`.",
        f"- Donnees full lues en read-only : `{labels['full_parquet_read_only_used']}`.",
        f"- FLAT trop faible : `{labels['flat_low_timeframes']}`.",
        f"- FLAT trop eleve : `{labels['flat_high_timeframes']}`.",
        "",
        "## Diagnostic ML V9.13",
        f"- Decision ML : `{ml['decision']}`.",
        f"- Clear wins vs baselines : `{ml['learned_vs_baselines']['clear_wins_count']}`.",
        f"- Cas proches des labels melanges : `{ml['learned_vs_shuffled_labels']['no_clear_edge_vs_shuffled_labels_count']}`.",
        f"- Collapses de classes detectes : `{ml['class_collapse_cases_count']}`.",
        "",
        "## Separabilite features/labels",
        f"- Methode : `{sep['method']}`.",
        f"- Top features communes entre timeframes : `{sep['common_top_features_between_timeframes']}`.",
        f"- Top features instables : `{sep['unstable_top_features']}`.",
        "",
        "## Hypotheses",
    ]
    for item in report["hypotheses"]:
        lines.append(f"- `{item['id']}` {item['hypothesis']} : `{item['support']}` - {item['evidence']}")
    lines.extend(
        [
            "",
            "## Recommandation suivante",
            f"- {decision['next_step_recommendation']}",
            "- Aucun backtest n'est recommande a ce stade.",
            "",
            "## Interdits maintenus",
            "- Aucun trading reel.",
            "- Aucun paper live.",
            "- Aucun ordre.",
            "- Aucun backtest execute.",
            "- Aucun walk-forward.",
            "- Aucune strategie.",
            "- Aucun signal actionnable.",
            "- Aucun modele persistant.",
            "- Aucune API privee.",
            "- Aucune cle API.",
            "- Aucun sidecar et aucune empreinte ZIP.",
        ]
    )
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_14(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "direction": "feature_label_separability_and_branch_decision",
        "target_name": TARGET_NAME_V9_13,
        "v9_14_decision": report["v9_14_decision"]["decision"],
        "recommended_next_step": report["v9_14_decision"]["next_step_recommendation"],
        **SAFETY_FLAGS,
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    summary = (
        "# Synthese courante - V9.14\n\n"
        "- Derniere version validee : `V9.13`.\n"
        "- Candidate : `V9.14`.\n"
        "- Statut : `pending_external_audit`.\n"
        "- Direction : separabilite features/labels et decision de branche.\n"
        f"- Decision V9.14 : `{report['v9_14_decision']['decision']}`.\n"
        f"- Recommandation : {report['v9_14_decision']['next_step_recommendation']}\n"
        "- Aucun trading, paper live, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", summary)
    _write_text(root / "reports/current/latest_summary.md", summary)
    _write_text(root / "reports/current/latest_metrics.md", summary)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V9.13.\n"
        "- Candidate : V9.14, separabilite features/labels et decision de branche.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n",
    )


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    if not full.exists():
        return {"path": path.as_posix(), "available": False, "payload": {}}
    if path.suffix == ".json":
        payload: Any = _read_json(full)
    else:
        payload = {"text": full.read_text(encoding="utf-8")}
    return {"path": path.as_posix(), "available": True, "payload": payload}


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
