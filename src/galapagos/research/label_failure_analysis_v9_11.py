from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from galapagos.data.public_market.provenance import sha256_file


VERSION = "V9.11"
LAST_VALIDATED_VERSION = "V9.6_to_V9.10"
DECISION_TYPE = "label_failure_analysis_and_redesign_plan"
WINDOW = {"window_start": "2023-03-25", "window_end": "2024-03-24", "total_days": 366}
TIMEFRAMES = ["1m", "5m", "15m", "1h"]
ALLOWED_DECISIONS = {
    "label_redesign_plan_horizon_extension",
    "label_redesign_plan_binary_directional",
    "label_redesign_plan_quantile_based",
    "label_redesign_plan_event_based",
    "label_redesign_plan_feature_first",
    "label_redesign_plan_extend_data_first",
    "stop_refined_label_branch",
}

REPORT_JSON_PATH = Path("reports/research_decisions/label_failure_analysis_v9_11.json")
REPORT_MD_PATH = Path("reports/research_decisions/label_failure_analysis_v9_11.md")
MANIFEST_PATH = Path("reports/manifests/label_failure_analysis_v9_11_manifest.json")
DOC_PATH = Path("docs/label_failure_analysis_v9_11.md")

INPUT_PATHS = {
    "v9_4_decision": Path("reports/research_decisions/refined_research_decision_gate_v9_4.json"),
    "v9_5_label_audit": Path("reports/research_decisions/alternative_label_design_audit_v9_5.json"),
    "v9_5_manifest": Path("reports/manifests/alternative_label_design_audit_v9_5_manifest.json"),
    "v9_6_labels": Path("reports/labels/refined_volatility_normalized_labels_v9_6.json"),
    "v9_6_manifest": Path("reports/manifests/refined_volatility_normalized_labels_v9_6_manifest.json"),
    "v9_7_dataset": Path("reports/datasets/refined_volnorm_labels_dataset_v9_7.json"),
    "v9_7_manifest": Path("reports/manifests/refined_volnorm_labels_dataset_v9_7_manifest.json"),
    "v9_8_ml": Path("reports/ml/refined_volnorm_labels_offline_ml_v9_8.json"),
    "v9_8_scores": Path("reports/ml/refined_volnorm_labels_offline_scores_v9_8.json"),
    "v9_8_manifest": Path("reports/manifests/refined_volnorm_labels_offline_ml_v9_8_manifest.json"),
    "v9_9_walk_forward": Path("reports/ml/refined_volnorm_strict_walk_forward_v9_9.json"),
    "v9_9_scores": Path("reports/ml/refined_volnorm_strict_walk_forward_scores_v9_9.json"),
    "v9_9_manifest": Path("reports/manifests/refined_volnorm_strict_walk_forward_v9_9_manifest.json"),
    "v9_10_decision": Path("reports/research_decisions/refined_volnorm_research_decision_gate_v9_10.json"),
    "v9_10_manifest": Path("reports/manifests/refined_volnorm_research_decision_gate_v9_10_manifest.json"),
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
    "ml_enabled": False,
    "labels_generated": False,
    "dataset_generated": False,
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
    "no_strategy": True,
    "no_actionable_signal": True,
    "no_persistent_model": True,
    "api_key_used": False,
    "private_endpoint_used": False,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}

FORBIDDEN_TERMS = {
    "pnl",
    "sharpe",
    "drawdown",
    "equity_curve",
    "profit_factor",
    "trading_signal",
    "order",
    "position_size",
    "strategy_validated",
    "tradable_edge_confirmed",
}


def run_label_failure_analysis_v9_11(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_label_failure_analysis_v9_11(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_11(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    manifest = build_manifest_v9_11(root, report)
    _write_json(root / MANIFEST_PATH, manifest)
    update_state_surfaces_v9_11(root, report)
    return report


def build_label_failure_analysis_v9_11(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    payloads = {name: item["payload"] for name, item in inputs.items()}
    recap = build_decision_recap_v9_11(payloads)
    label_analysis = analyze_v9_6_labels_v9_11(root, payloads["v9_6_labels"], payloads["v9_7_dataset"])
    ml_analysis = analyze_v9_8_ml_v9_11(payloads["v9_8_ml"])
    walk_forward_analysis = analyze_v9_9_walk_forward_v9_11(payloads["v9_9_walk_forward"], payloads["v9_10_decision"])
    hypotheses = classify_failure_hypotheses_v9_11(label_analysis, ml_analysis, walk_forward_analysis)
    future_designs = compare_future_label_designs_v9_11(hypotheses)
    decision = choose_decision_v9_11(hypotheses, future_designs, walk_forward_analysis)
    packaging_notes = {
        "exclude_icon_files_from_future_zips": True,
        "exclude_icon_carriage_return_files_from_future_zips": True,
        "add_internal_timeouts_to_smoke_import_subprocesses": True,
        "add_internal_timeouts_to_pytest_collect_only": True,
        "do_not_reintroduce_sha256_sidecars": True,
        "do_not_reintroduce_zip_fingerprints": True,
    }
    return {
        "version": VERSION,
        "status": "PASS",
        "decision_type": DECISION_TYPE,
        "created_at_utc": _utc_now(),
        "inputs": {name: {"path": item["path"], "sha256": item["sha256"]} for name, item in inputs.items()},
        "window": WINDOW,
        "decision_recap": recap,
        "label_analysis_v9_6": label_analysis,
        "ml_analysis_v9_8": ml_analysis,
        "walk_forward_analysis_v9_9": walk_forward_analysis,
        "failure_hypotheses": hypotheses,
        "future_designs_compared": future_designs,
        "v9_11_decision": decision,
        "next_step_recommendation": decision["next_step_recommendation"],
        "packaging_observations": packaging_notes,
        "forbidden_terms_scan": forbidden_terms_scan_v9_11({"hypotheses": hypotheses, "future_designs": future_designs}),
        "findings": dict(FINDINGS),
        "safety": dict(SAFETY),
        "safety_flags": dict(SAFETY_FLAGS),
        "limitations": [
            "V9.11 analyse uniquement l'echec des labels V9.6/V9.10 et propose un plan de redesign.",
            "V9.11 ne cree aucun nouveau label full, aucun dataset, aucun modele ML, aucun walk-forward et aucun backtest.",
            "La recommandation V9.11 ne justifie aucun trading, paper live, ordre, strategie ou signal actionnable.",
        ],
    }


def build_decision_recap_v9_11(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "v9_4": {
            "decision": payloads["v9_4_decision"].get("research_decision"),
            "interpretation": "Aucun backtest; raffinement des labels demande.",
        },
        "v9_5": {
            "decision": payloads["v9_5_label_audit"].get("v9_5_decision", {}).get("decision"),
            "interpretation": "Candidat volatility-normalized recommande pour une factory future.",
        },
        "v9_10": {
            "decision": payloads["v9_10_decision"].get("research_decision"),
            "static_split_decision": payloads["v9_10_decision"].get("static_split_assessment_v9_8", {}).get("decision"),
            "walk_forward_decision": payloads["v9_10_decision"].get("walk_forward_assessment_v9_9", {}).get("decision"),
            "interpretation": "Les labels volatility-normalized restent trop proches des labels melanges.",
        },
    }


def analyze_v9_6_labels_v9_11(root: Path, label_report: dict[str, Any], dataset_report: dict[str, Any]) -> dict[str, Any]:
    timeframes: dict[str, Any] = {}
    full_data_available = True
    for timeframe in TIMEFRAMES:
        quality = label_report.get("quality", {}).get(timeframe, {})
        label_path = Path(label_report.get("outputs", {}).get(timeframe, {}).get("path", ""))
        dataset_path = Path(dataset_report.get("outputs", {}).get(timeframe, {}).get("path", ""))
        full_data_available = full_data_available and (root / label_path).is_file() and (root / dataset_path).is_file()
        enriched = {
            "timeframe": timeframe,
            "class_distribution": quality.get("class_distribution", {}),
            "fixed_label_distribution_h1": quality.get("fixed_label_distribution_h1", {}),
            "flat_rate_reduction_vs_fixed_h1": quality.get("flat_rate_reduction_vs_fixed_h1"),
            "majority_class": quality.get("majority_class"),
            "majority_rate": quality.get("majority_rate"),
            "entropy_bits": quality.get("entropy_bits"),
            "valid_rows": quality.get("valid_rows"),
            "invalid_rows": quality.get("invalid_rows"),
            "warmup_rows": quality.get("warmup_rows"),
            "distribution_by_month": {},
            "distribution_by_split": {},
            "distribution_by_walk_forward_group": {},
        }
        if (root / label_path).is_file():
            labels = pd.read_parquet(root / label_path, columns=["event_ts", "up_down_flat_volnorm_h1", "label_valid_volnorm_h1"], engine="pyarrow")
            valid = labels[labels["label_valid_volnorm_h1"] == True].copy()  # noqa: E712
            valid["month"] = pd.to_datetime(valid["event_ts"], utc=True).dt.strftime("%Y-%m")
            enriched["distribution_by_month"] = _distribution_by_group(valid, "month", "up_down_flat_volnorm_h1")
        if (root / dataset_path).is_file():
            dataset = pd.read_parquet(root / dataset_path, columns=["split", "walk_forward_group", "up_down_flat_volnorm_h1", "label_valid_volnorm_h1"], engine="pyarrow")
            valid_dataset = dataset[dataset["label_valid_volnorm_h1"] == True].copy()  # noqa: E712
            enriched["distribution_by_split"] = _distribution_by_group(valid_dataset, "split", "up_down_flat_volnorm_h1")
            enriched["distribution_by_walk_forward_group"] = _distribution_by_group(valid_dataset, "walk_forward_group", "up_down_flat_volnorm_h1")
        timeframes[timeframe] = enriched
    flat_rates = {
        timeframe: payload.get("class_distribution", {}).get("FLAT", {}).get("rate")
        for timeframe, payload in timeframes.items()
    }
    return {
        "target_name": label_report.get("target_name"),
        "selected_k": label_report.get("selected_volatility_threshold_multiplier"),
        "parameters_tested": label_report.get("parameters_tested", []),
        "selection_basis": label_report.get("selection_basis"),
        "full_parquet_read_only_used": full_data_available,
        "timeframes": timeframes,
        "flat_rates": flat_rates,
        "dominance_flat_remaining": max((rate for rate in flat_rates.values() if isinstance(rate, (int, float))), default=0.0),
        "design_limits": [
            "k=0.5 reduit la dominance FLAT du 1m mais ne rend pas le label falsifiable par les modeles offline.",
            "Le seuil normalise par volatilite reste local au retour h1 et peut conserver un bruit directionnel eleve.",
            "La selection V9.6 n'utilise volontairement aucune performance ML, donc elle ne garantit pas une cible apprenable.",
        ],
    }


def analyze_v9_8_ml_v9_11(ml_report: dict[str, Any]) -> dict[str, Any]:
    metrics = ml_report.get("metrics", {})
    learned = [item for item in metrics.values() if item.get("model_name") in {"logistic_regression", "decision_tree_depth_2"} and item.get("split") in {"validation", "test"}]
    baselines = [item for item in metrics.values() if item.get("model_name") in {"majority_class_baseline", "random_seeded_baseline"} and item.get("split") in {"validation", "test"}]
    best_cases = sorted(learned, key=lambda item: (item.get("macro_f1", 0.0), item.get("balanced_accuracy", 0.0)), reverse=True)[:5]
    worst_cases = sorted(learned, key=lambda item: (item.get("macro_f1", 0.0), item.get("balanced_accuracy", 0.0)))[:5]
    no_clear = [item for item in ml_report.get("label_shuffle_falsification", {}).values() if item.get("no_clear_edge_vs_shuffled_labels")]
    baseline_macro_f1_by_timeframe_split = {
        f"{item['timeframe']}.{item['split']}": max(
            [
                baseline.get("macro_f1", 0.0)
                for baseline in baselines
                if baseline.get("timeframe") == item.get("timeframe") and baseline.get("split") == item.get("split")
            ],
            default=0.0,
        )
        for item in learned
    }
    weak_learned_cases = [
        {
            "timeframe": item.get("timeframe"),
            "model_name": item.get("model_name"),
            "split": item.get("split"),
            "macro_f1": item.get("macro_f1"),
            "best_baseline_macro_f1": baseline_macro_f1_by_timeframe_split.get(f"{item.get('timeframe')}.{item.get('split')}"),
        }
        for item in learned
        if item.get("macro_f1", 0.0) <= baseline_macro_f1_by_timeframe_split.get(f"{item.get('timeframe')}.{item.get('split')}", 0.0) + 0.02
    ]
    return {
        "decision": ml_report.get("decision"),
        "learned_vs_baselines": {
            "learned_cases": len(learned),
            "baseline_cases": len(baselines),
            "weak_learned_cases_count": len(weak_learned_cases),
            "weak_learned_cases_examples": weak_learned_cases[:8],
        },
        "close_to_shuffled_labels": {
            "count": len(no_clear),
            "by_timeframe": dict(sorted(Counter(item["timeframe"] for item in no_clear).items())),
            "by_model": dict(sorted(Counter(item["model_name"] for item in no_clear).items())),
        },
        "best_cases": [_metric_summary(item) for item in best_cases],
        "worst_cases": [_metric_summary(item) for item in worst_cases],
        "models_learning_nothing": sorted({item["model_name"] for item in weak_learned_cases}),
        "metric_floor_assessment": "Les meilleurs learned cases restent trop faibles et trop proches des labels melanges pour justifier une suite backtest.",
    }


def analyze_v9_9_walk_forward_v9_11(wf_report: dict[str, Any], decision_report: dict[str, Any]) -> dict[str, Any]:
    aggregate = wf_report.get("aggregate_metrics", {})
    no_clear = [item for item in wf_report.get("label_shuffle_falsification", {}).values() if item.get("no_clear_edge_vs_shuffled_labels")]
    weak_folds = [
        {"timeframe_model": key, "weak_folds": value.get("weak_folds", [])}
        for key, value in aggregate.items()
        if value.get("weak_folds")
    ]
    unstable_folds = [
        {"timeframe_model": key, "unstable_folds": value.get("unstable_folds", [])}
        for key, value in aggregate.items()
        if value.get("unstable_folds")
    ]
    concentration = [
        {"timeframe_model": key, "warnings": value.get("fold_concentration_warnings", [])}
        for key, value in aggregate.items()
        if value.get("fold_concentration_warnings")
    ]
    return {
        "decision": wf_report.get("decision"),
        "v9_10_summary": decision_report.get("walk_forward_assessment_v9_9", {}),
        "no_clear_edge_vs_shuffled_labels_count": len(no_clear),
        "no_clear_by_timeframe": dict(sorted(Counter(item["timeframe"] for item in no_clear).items())),
        "no_clear_by_model": dict(sorted(Counter(item["model_name"] for item in no_clear).items())),
        "weak_folds_count": sum(len(item["weak_folds"]) for item in weak_folds),
        "weak_folds_examples": weak_folds[:8],
        "unstable_folds_count": sum(len(item["unstable_folds"]) for item in unstable_folds),
        "unstable_folds_examples": unstable_folds[:8],
        "fold_concentration_warnings_count": len(concentration),
        "fold_concentration_examples": concentration[:8],
        "comparison_to_static_split_v9_8": wf_report.get("comparison_to_static_split_v9_8", {}),
        "interpretation": "Le walk-forward strict confirme que la proximite aux labels melanges n'est pas un artefact du static split.",
    }


def classify_failure_hypotheses_v9_11(label_analysis: dict[str, Any], ml_analysis: dict[str, Any], walk_forward_analysis: dict[str, Any]) -> list[dict[str, Any]]:
    no_clear = walk_forward_analysis.get("no_clear_edge_vs_shuffled_labels_count", 0)
    weak = walk_forward_analysis.get("weak_folds_count", 0)
    unstable = walk_forward_analysis.get("unstable_folds_count", 0)
    max_flat = label_analysis.get("dominance_flat_remaining", 0.0)
    weak_learned = ml_analysis.get("learned_vs_baselines", {}).get("weak_learned_cases_count", 0)
    return [
        _hypothesis("H1", "horizon h1 trop bruite", "likely", no_clear + weak >= 50, ["76 cas no-clear en walk-forward", "best learned macro_f1 faible"], "Tester un horizon plus long avant tout backtest."),
        _hypothesis("H2", "features actuelles insuffisantes pour predire ce label", "likely", weak_learned >= 8, ["Les modeles appris restent proches des baselines", "V8.9/V9.0 avaient deja fortement reduit les features"], "Coupler le redesign label a un audit feature si le label reste non falsifiable."),
        _hypothesis("H3", "classe FLAT encore mal definie", "possible", max_flat >= 0.45, [f"FLAT max apres V9.6 = {max_flat:.3f}", "FLAT reste majoritaire sur tous les timeframes"], "Comparer une cible binaire et une cible event-based."),
        _hypothesis("H4", "seuil k=0.5 trop permissif", "likely", True, ["k=0.5 a ete retenu pour distribution, pas pour apprenabilite", "les labels restent proches du shuffle"], "Tester k plus strict ou barriere de mouvement significatif."),
        _hypothesis("H5", "labels multi-classes trop difficiles", "possible", weak_learned >= 8, ["DOWN/FLAT/UP cree une classe intermediaire difficile", "plusieurs modeles predisent essentiellement FLAT"], "Evaluer un design binaire directionnel comme diagnostic, sans signal trading."),
        _hypothesis("H6", "fenetre 2023-2024 pas assez robuste", "possible", unstable >= 10, ["20 unstable folds", "22 weak folds"], "Etendre les donnees uniquement apres un label mieux defini."),
        _hypothesis("H7", "probleme de regime de marche", "possible", unstable >= 10, ["Instabilite par folds", "concentration temporelle residuelle"], "Ajouter une analyse de regime descriptive dans la prochaine iteration."),
        _hypothesis("H8", "signal absent dans OHLCV+trades agreges actuels", "plausible", no_clear >= 50 and weak >= 10, ["76 cas no-clear", "aucun backtest justifie"], "Prevoir un critere d'arret si un redesign label plus strict reste non falsifiable."),
    ]


def compare_future_label_designs_v9_11(hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    likely_ids = {item["id"] for item in hypotheses if item["severity"] in {"likely", "plausible"}}
    return [
        _design("longer_horizon_labels", "labels horizon plus long", "high", "Reduit le bruit h1; cible H1/H7.", "Latence de label plus longue et moins de lignes valides en bord de fenetre.", "accept_for_future_experiment"),
        _design("multi_horizon_labels", "labels multi-horizon", "medium", "Peut separer bruit court terme et mouvement plus durable.", "Risque de complexite et de leakage si les disponibilites ne sont pas strictes.", "review_before_experiment"),
        _design("binary_directional_without_flat", "labels binaires directionnels sans FLAT", "medium" if "H5" in likely_ids else "low", "Teste si la classe FLAT bloque l'apprentissage.", "Peut forcer des mouvements non significatifs dans UP/DOWN.", "review_before_experiment"),
        _design("quantile_based_labels", "labels quantile-based", "medium", "Controle la distribution sans optimiser le trading.", "Peut creer un equilibre artificiel et instable par regime.", "review_before_experiment"),
        _design("event_based_labels", "labels event-based", "high", "Cible des mouvements significatifs plutot qu'un horizon fixe bruite.", "Doit definir une disponibilite label_available_ts stricte et ne pas devenir un backtest.", "accept_for_future_experiment"),
        _design("volnorm_different_k", "volatility-normalized avec k different", "medium", "Teste H4 avec seuils plus stricts.", "Peut augmenter FLAT et reduire trop fortement les evenements.", "review_before_experiment"),
        _design("significant_move_with_descriptive_cost", "mouvement significatif avec cout theorique descriptif", "medium", "Filtre le bruit minuscule sans produire de PnL.", "Le cout theorique doit rester descriptif et non backtest.", "review_before_experiment"),
        _design("feature_or_data_extension_first", "extension features/data avant nouveau label", "medium", "Adresse H2/H6 si le label n'est pas seul responsable.", "Risque de retarder la correction du target.", "review_before_experiment"),
    ]


def choose_decision_v9_11(hypotheses: list[dict[str, Any]], future_designs: list[dict[str, Any]], walk_forward_analysis: dict[str, Any]) -> dict[str, Any]:
    likely = [item for item in hypotheses if item["severity"] in {"likely", "plausible"}]
    if walk_forward_analysis.get("no_clear_edge_vs_shuffled_labels_count", 0) >= 50:
        decision = "label_redesign_plan_horizon_extension"
        recommendation = "V9.12 - Label Redesign Candidate: horizon extension + event-based diagnostic, sans ML ni backtest dans la phase de design."
    elif any(item["id"] == "H2" and item["severity"] == "likely" for item in likely):
        decision = "label_redesign_plan_feature_first"
        recommendation = "V9.12 - Feature/data extension diagnostic avant nouvelle factory."
    else:
        decision = "label_redesign_plan_event_based"
        recommendation = "V9.12 - Event-Based Label Redesign Candidate."
    return {
        "decision": decision,
        "confidence": "medium",
        "justification": "Le label volatility-normalized ameliore la distribution mais reste non falsifie face aux labels melanges en static split et walk-forward.",
        "primary_evidence": {
            "no_clear_edge_vs_shuffled_labels_count": walk_forward_analysis.get("no_clear_edge_vs_shuffled_labels_count"),
            "weak_folds_count": walk_forward_analysis.get("weak_folds_count"),
            "unstable_folds_count": walk_forward_analysis.get("unstable_folds_count"),
            "top_hypotheses": [item["id"] for item in likely[:5]],
            "accepted_future_designs": [item["design_id"] for item in future_designs if item["decision"] == "accept_for_future_experiment"],
        },
        "next_step_recommendation": recommendation,
        "explicit_no_backtest_statement": "Aucun backtest n'est justifie par V9.11.",
        "explicit_no_trading_statement": "V9.11 n'autorise aucun trading, paper live, ordre, strategie ou signal actionnable.",
    }


def forbidden_terms_scan_v9_11(payload: Any) -> dict[str, Any]:
    found: list[str] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                text = str(key).casefold()
                if text in FORBIDDEN_TERMS:
                    found.append(f"{path}.{key}")
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(payload, "payload")
    return {"passed": not found, "forbidden_paths": found}


def build_manifest_v9_11(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "status": report["status"],
        "decision_type": DECISION_TYPE,
        "created_at_utc": report["created_at_utc"],
        "report_path": REPORT_JSON_PATH.as_posix(),
        "report_sha256": sha256_file(root / REPORT_JSON_PATH) if (root / REPORT_JSON_PATH).exists() else None,
        "v9_11_decision": report["v9_11_decision"],
        "inputs": report["inputs"],
        "findings": report["findings"],
        "safety": report["safety"],
        "safety_flags": report["safety_flags"],
        "packaging_observations": report["packaging_observations"],
        "limitations": report["limitations"],
    }


def build_markdown_v9_11(report: dict[str, Any]) -> str:
    lines = [
        "# V9.11 - Label Failure Analysis & Redesign Plan",
        "",
        "## Resume executif",
        f"- Decision V9.11 : `{report['v9_11_decision']['decision']}`.",
        f"- Recommandation : {report['next_step_recommendation']}",
        "- Aucun backtest n'est justifie. Aucun trading, paper live, ordre, strategie ou signal actionnable.",
        "",
        "## Recap decisions",
    ]
    for version, payload in report["decision_recap"].items():
        lines.append(f"- `{version}` : `{payload['decision']}` - {payload['interpretation']}")
    lines.extend(["", "## Diagnostic d'echec", ""])
    for hypothesis in report["failure_hypotheses"]:
        lines.append(f"- `{hypothesis['id']}` {hypothesis['name']} : `{hypothesis['severity']}`. {hypothesis['recommended_action']}")
    lines.extend(["", "## Designs futurs compares", ""])
    for design in report["future_designs_compared"]:
        lines.append(f"- `{design['design_id']}` : priorite `{design['priority']}`, decision `{design['decision']}`.")
    lines.extend(
        [
            "",
            "## Garde-fous",
            "- V9.11 ne cree aucun nouveau label full.",
            "- V9.11 ne lance aucun ML, aucun walk-forward et aucun backtest.",
            "- V9.11 ne produit aucun signal actionnable, aucune strategie, aucun ordre et aucun trading reel.",
            "- Les prochains ZIP doivent exclure `Icon`, `Icon\\r`, `.DS_Store`, caches, secrets, modeles persistants, sidecars SHA256 et empreintes ZIP.",
        ]
    )
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_11(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "direction": DECISION_TYPE,
        "v9_11_decision": report["v9_11_decision"]["decision"],
        "next_step_recommendation": report["next_step_recommendation"],
        "no_trading": True,
        "no_paper_live": True,
        "no_orders": True,
        "no_backtest_performed": True,
        "no_strategy": True,
        "no_actionable_signal": True,
        "no_persistent_model": True,
        "api_key_used": False,
        "private_endpoint_used": False,
        "no_sidecars": True,
        "no_zip_fingerprints": True,
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(root / "reports/PROJECT_STATE.json", state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    summary = (
        "# Synthese courante - V9.11\n\n"
        "- Derniere version validee : `V9.6_to_V9.10`.\n"
        "- Candidate : `V9.11`.\n"
        "- Statut : `pending_external_audit`.\n"
        "- Direction : analyse d'echec des labels et plan de redesign.\n"
        f"- Decision V9.11 : `{report['v9_11_decision']['decision']}`.\n"
        "- Aucun trading, paper live, ordre, backtest, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", summary)
    _write_text(root / "reports/current/latest_summary.md", summary)
    _write_text(root / "reports/current/latest_metrics.md", summary)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V9.6_to_V9.10.\n"
        "- Candidate : V9.11, analyse d'echec des labels et plan de redesign.\n"
        f"- Decision V9.11 : {report['v9_11_decision']['decision']}.\n\n"
        "Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal actionnable, aucun modele persistant, aucune API privee et aucune cle API.\n"
        "Le packaging V9.11 ne produit aucun sidecar et aucune empreinte ZIP.\n",
    )


def _distribution_by_group(frame: pd.DataFrame, group_column: str, label_column: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for group_value, group in frame.groupby(group_column, sort=True):
        counts = group[label_column].astype(str).value_counts().to_dict()
        total = int(sum(counts.values()))
        result[str(group_value)] = {
            "rows": total,
            "distribution": {label: {"count": int(count), "rate": float(count / total) if total else 0.0} for label, count in sorted(counts.items())},
            "majority_class": max(counts, key=counts.get) if counts else None,
            "majority_rate": float(max(counts.values()) / total) if counts and total else None,
        }
    return result


def _metric_summary(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "timeframe": item.get("timeframe"),
        "model_name": item.get("model_name"),
        "split": item.get("split"),
        "accuracy": item.get("accuracy"),
        "balanced_accuracy": item.get("balanced_accuracy"),
        "macro_f1": item.get("macro_f1"),
    }


def _hypothesis(hid: str, name: str, severity: str, active: bool, evidence: list[str], action: str) -> dict[str, Any]:
    return {"id": hid, "name": name, "severity": severity if active else "low", "active": bool(active), "evidence": evidence, "recommended_action": action}


def _design(design_id: str, name: str, priority: str, advantage: str, risk: str, decision: str) -> dict[str, Any]:
    return {
        "design_id": design_id,
        "name": name,
        "priority": priority,
        "advantages": advantage,
        "risks": risk,
        "causality": "Doit garantir feature_available_ts <= decision_ts et label_available_ts > decision_ts.",
        "leakage_risk": "A verifier explicitement dans une future factory; aucune validation trading n'est impliquee.",
        "decision": decision,
    }


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    return {"path": path.as_posix(), "sha256": sha256_file(full), "payload": _read_json(full) if path.suffix == ".json" else {"text_available": full.exists()}}


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
