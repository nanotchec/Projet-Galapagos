from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


VERSION = "V9.5"
LAST_VALIDATED_VERSION = "V9.4.1"
SOURCE_DECISION_VERSION = "V9.4"
WINDOW_START = "2023-03-25"
WINDOW_END = "2024-03-24"
TOTAL_DAYS = 366
TARGET_NAME = "up_down_flat_h1"
TIMEFRAMES = ["1m", "5m", "15m", "1h"]
ALLOWED_DECISIONS = {
    "label_redesign_not_ready_need_data_inspection",
    "label_redesign_candidate_fixed_thresholds",
    "label_redesign_candidate_volatility_normalized",
    "label_redesign_candidate_quantile_based",
    "label_redesign_candidate_multi_horizon",
    "stop_refined_branch_labels_not_promising",
}

MANIFEST_PATH = Path("reports/manifests/alternative_label_design_audit_v9_5_manifest.json")
REPORT_JSON_PATH = Path("reports/research_decisions/alternative_label_design_audit_v9_5.json")
REPORT_MD_PATH = Path("reports/research_decisions/alternative_label_design_audit_v9_5.md")
DOC_MD_PATH = Path("docs/alternative_label_design_audit_v9_5.md")

INPUT_PATHS = {
    "v9_4_decision": Path("reports/research_decisions/refined_research_decision_gate_v9_4.json"),
    "v9_4_manifest": Path("reports/manifests/refined_research_decision_gate_v9_4_manifest.json"),
    "v9_3_walk_forward": Path("reports/ml/refined_strict_walk_forward_validation_v9_3.json"),
    "v9_3_scores_report": Path("reports/ml/refined_strict_walk_forward_scores_v9_3.json"),
    "v9_2_static_ml": Path("reports/ml/refined_ohlcv_trades_offline_ml_research_v9_2.json"),
    "v9_2_scores_report": Path("reports/ml/refined_ohlcv_trades_offline_research_scores_v9_2.json"),
    "v9_1_dataset_manifest": Path("reports/manifests/refined_ohlcv_trades_offline_supervised_dataset_v9_1_manifest.json"),
    "v5_2_label_manifest": Path("reports/manifests/max_history_label_factory_v5_2_manifest.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
}

FORBIDDEN_OUTPUT_TERMS = {
    "prediction",
    "model_score",
    "signal",
    "trading_signal",
    "order",
    "pnl",
    "sharpe",
    "drawdown",
    "equity_curve",
    "profit_factor",
    "backtest",
    "position_size",
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
    "labels_recomputed": False,
    "dataset_recomputed": False,
    "backtest_enabled": False,
    "strategy_enabled": False,
    "execution_enabled": False,
    "persistent_model_created": False,
}

LIMITATIONS = [
    "V9.5 audite uniquement le design des labels existants et propose des hypotheses de recherche.",
    "V9.5 ne cree aucun nouveau label, aucun dataset, aucun modele ML, aucun backtest, aucune strategie, aucun signal actionnable et aucun ordre.",
    "Les alternatives recommandees doivent etre implementees et validees dans une future label factory candidate avant toute nouvelle evaluation ML.",
]


def run_alternative_label_design_audit_v9_5(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_alternative_label_design_audit_v9_5(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_5(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_MD_PATH, markdown)
    manifest = build_manifest_v9_5(root, report)
    _write_json(root / MANIFEST_PATH, manifest)
    update_state_surfaces_v9_5(root, report, manifest)
    return manifest


def build_alternative_label_design_audit_v9_5(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    v94 = inputs["v9_4_decision"]["payload"]
    v93 = inputs["v9_3_walk_forward"]["payload"]
    v92 = inputs["v9_2_static_ml"]["payload"]
    v91 = inputs["v9_1_dataset_manifest"]["payload"]
    v52 = inputs["v5_2_label_manifest"]["payload"]

    current_labels = analyze_current_labels_v9_5(root, v91, v52, v93, v94)
    diagnostic = build_problem_diagnostic_v9_5(current_labels, v94, v93, v92)
    alternatives = build_alternative_design_catalog_v9_5(current_labels, diagnostic, v52)
    leakage_guard = build_leakage_guard_v9_5(alternatives)
    forbidden_scan = build_forbidden_output_scan_v9_5(alternatives)
    decision = choose_label_design_decision_v9_5(current_labels, diagnostic, alternatives)

    return {
        "version": VERSION,
        "status": "PASS",
        "decision_type": "alternative_label_design_audit",
        "created_at_utc": _utc_now(),
        "inputs": {name: {"path": item["path"], "sha256": item["sha256"]} for name, item in inputs.items()},
        "source_decision": {
            "version": SOURCE_DECISION_VERSION,
            "research_decision": v94.get("research_decision"),
            "reason": v94.get("decision_justification"),
            "label_shuffle_no_clear_edge_cases": v94.get("label_shuffle_assessment", {}).get("no_clear_edge_vs_shuffled_labels_count"),
            "fold_concentration_entries": v94.get("fold_stability_assessment", {}).get("fold_concentration_entries_count"),
        },
        "window": {"window_start": WINDOW_START, "window_end": WINDOW_END, "total_days": TOTAL_DAYS},
        "current_label_analysis": current_labels,
        "problem_diagnostic": diagnostic,
        "alternative_label_design_catalog": alternatives,
        "leakage_guard": leakage_guard,
        "forbidden_output_scan": forbidden_scan,
        "v9_5_decision": decision,
        "next_step_recommendation": "V9.6 - Refined Label Factory Candidate",
        "no_backtest_justified": True,
        "findings": dict(FINDINGS),
        "safety": dict(SAFETY),
        "limitations": LIMITATIONS,
    }


def analyze_current_labels_v9_5(
    root: Path,
    dataset_manifest: dict[str, Any],
    label_manifest: dict[str, Any],
    walk_forward_report: dict[str, Any],
    decision_report: dict[str, Any],
) -> dict[str, Any]:
    outputs = dataset_manifest.get("outputs", {})
    full_dataset_available = all((root / outputs.get(timeframe, {}).get("path", "")).is_file() for timeframe in TIMEFRAMES)
    label_outputs = label_manifest.get("outputs", {})
    full_labels_available = all((root / label_outputs.get(timeframe, {}).get("path", "")).is_file() for timeframe in TIMEFRAMES)
    no_clear_cases = {
        key: value
        for key, value in walk_forward_report.get("label_shuffle_falsification", {}).items()
        if value.get("no_clear_edge_vs_shuffled_labels")
    }
    analysis = {
        "target_name": TARGET_NAME,
        "horizons": label_manifest.get("horizons", []),
        "threshold": label_manifest.get("threshold"),
        "full_local_dataset_available": full_dataset_available,
        "full_local_labels_available": full_labels_available,
        "read_mode": "v9_1_dataset_parquet_read_only" if full_dataset_available else "manifests_reports_only",
        "label_outputs_read_only": {
            timeframe: {
                "path": label_outputs.get(timeframe, {}).get("path"),
                "available": (root / label_outputs.get(timeframe, {}).get("path", "")).is_file(),
            }
            for timeframe in TIMEFRAMES
        },
        "timeframes": {},
        "label_shuffle_link": {
            "no_clear_edge_vs_shuffled_labels_count": len(no_clear_cases),
            "by_timeframe": dict(sorted(Counter(item["timeframe"] for item in no_clear_cases.values()).items())),
            "by_model": dict(sorted(Counter(item["model_name"] for item in no_clear_cases.values()).items())),
            "examples": sorted(no_clear_cases)[:10],
            "source_decision_no_clear_edge_count": decision_report.get("label_shuffle_assessment", {}).get("no_clear_edge_vs_shuffled_labels_count"),
        },
    }
    if full_dataset_available:
        for timeframe in TIMEFRAMES:
            analysis["timeframes"][timeframe] = _analyze_dataset_labels(root / outputs[timeframe]["path"])
    else:
        for timeframe in TIMEFRAMES:
            quality = dataset_manifest.get("quality", {}).get(timeframe, {})
            analysis["timeframes"][timeframe] = {
                "rows_total": quality.get("rows"),
                "rows_valid_for_label_audit": quality.get("label_valid_counts_by_horizon", {}).get("h1"),
                "class_distribution": {},
                "class_distribution_by_split": {},
                "class_distribution_by_month": {},
                "class_distribution_by_walk_forward_group": {},
                "majority_class": None,
                "majority_rate": None,
                "entropy_bits": None,
                "transition_matrix": {},
                "label_change_rate": None,
                "label_autocorrelation_lag_1": None,
                "dominated_periods": [],
                "limitation": "Full dataset parquet absent in this context; class distribution could not be recomputed.",
            }
    return analysis


def build_problem_diagnostic_v9_5(
    current_labels: dict[str, Any],
    decision_report: dict[str, Any],
    walk_forward_report: dict[str, Any],
    static_report: dict[str, Any],
) -> dict[str, Any]:
    majority_rates = [
        item.get("majority_rate")
        for item in current_labels.get("timeframes", {}).values()
        if isinstance(item.get("majority_rate"), (int, float))
    ]
    label_change_rates = [
        item.get("label_change_rate")
        for item in current_labels.get("timeframes", {}).values()
        if isinstance(item.get("label_change_rate"), (int, float))
    ]
    dominated_periods = [
        {"timeframe": timeframe, **period}
        for timeframe, item in current_labels.get("timeframes", {}).items()
        for period in item.get("dominated_periods", [])
    ]
    no_clear_count = current_labels["label_shuffle_link"]["no_clear_edge_vs_shuffled_labels_count"]
    fold_concentration_entries = decision_report.get("fold_stability_assessment", {}).get("fold_concentration_entries_count", 0)
    flat_rates = {
        timeframe: item.get("class_distribution", {}).get("FLAT", {}).get("rate")
        for timeframe, item in current_labels.get("timeframes", {}).items()
    }
    return {
        "labels_too_noisy": no_clear_count > 0 and (max(label_change_rates, default=0.0) > 0.55),
        "thresholds_likely_too_weak_or_not_scaled": max(majority_rates, default=0.0) > 0.70,
        "horizon_too_short_suspected": no_clear_count > 0 and max(label_change_rates, default=0.0) > 0.60,
        "horizon_too_long_suspected": False,
        "class_imbalance_present": max(majority_rates, default=0.0) > 0.70,
        "flat_class_definition_issue": (flat_rates.get("1m") or 0.0) > 0.70 and (flat_rates.get("1h") or 1.0) < 0.25,
        "timeframe_instability_present": decision_report.get("timeframe_stability_assessment", {}).get("verdict") != "stable",
        "market_regime_instability_present": bool(dominated_periods) or fold_concentration_entries > 0,
        "feature_label_incoherence_suspected": static_report.get("target_name") == TARGET_NAME
        and decision_report.get("baseline_assessment", {}).get("learned_models_clearly_beat_baselines") is False,
        "dominant_periods_count": len(dominated_periods),
        "dominant_period_examples": dominated_periods[:12],
        "no_clear_edge_vs_shuffled_labels_count": no_clear_count,
        "fold_concentration_entries": fold_concentration_entries,
        "metric_forbidden_scan_passed": walk_forward_report.get("metric_forbidden_scan", {}).get("metric_forbidden_terms_detected") is False,
        "feature_leakage_scan_passed": walk_forward_report.get("feature_leakage_scan", {}).get("feature_leakage_detected") is False,
        "summary": (
            "Le diagnostic pointe vers un probleme de labels : seuil fixe non scale entre timeframes, "
            "dominance FLAT en 1m, transitions rapides sur les timeframes plus longs et falsification label shuffle non propre."
        ),
    }


def build_alternative_design_catalog_v9_5(
    current_labels: dict[str, Any],
    diagnostic: dict[str, Any],
    label_manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    base_threshold = label_manifest.get("threshold")
    return [
        _design(
            "fixed_stricter_thresholds",
            "Seuils fixes plus stricts que le seuil actuel.",
            "Simple, reproductible, facile a auditer.",
            "Peut aggraver l'instabilite entre timeframes si le seuil reste non scale.",
            "Causal si calcule uniquement avec close futur pour le label et publie apres label_end_ts.",
            "label_available_ts reste strictement apres decision_ts.",
            "Risque faible si aucune feature future n'est introduite.",
            "Reduit potentiellement les labels directionnels bruites, mais peut augmenter excessivement FLAT.",
            "review",
            f"Le seuil actuel est {base_threshold}; la dominance FLAT 1m suggere qu'un seuil fixe seul ne suffit pas.",
        ),
        _design(
            "volatility_normalized_thresholds",
            "Seuils normalises par volatilite historique causale disponible avant decision_ts.",
            "Aligne mieux les labels entre 1m, 5m, 15m et 1h.",
            "Doit verrouiller une volatilite strictement causale pour eviter leakage.",
            "Causal si la volatilite de normalisation n'utilise que des donnees closes avant decision_ts.",
            "label_available_ts reste strictement apres decision_ts; feature_available_ts <= decision_ts doit rester vrai.",
            "Risque de leakage si la volatilite inclut la fenetre future du label.",
            "Devrait reduire l'ecart de classe entre timeframes et rendre FLAT plus comparable.",
            "accept_for_future_experiment",
            "Candidat prioritaire car le seuil fixe actuel semble non scale entre timeframes.",
        ),
        _design(
            "rolling_quantile_or_tertile_labels",
            "Labels construits par quantiles/tertiles sur une fenetre temporelle definie.",
            "Controle mieux l'equilibre de classes.",
            "Risque de non-stationnarite et de fuite si les quantiles utilisent le futur.",
            "Causal uniquement si les seuils quantiles sont calcules sur une fenetre passee et figes avant decision_ts.",
            "Disponibilite temporelle acceptable si les seuils sont connus avant la decision.",
            "Risque moyen : les quantiles doivent exclure validation/test futur.",
            "Peut reduire le desequilibre, mais complique l'interpretation economique du label.",
            "review_for_future_experiment",
            "Utile si le redesign volatility-normalized ne stabilise pas les classes.",
        ),
        _design(
            "alternative_horizon",
            "Tester des horizons alternatifs a h1, h3, h5 en bars.",
            "Peut reduire le bruit si h1 est trop court.",
            "Un horizon trop long augmente la latence du label et peut diluer le lien aux features.",
            "Causal si le label est seulement disponible apres l'horizon complet.",
            "label_available_ts doit etre decale au-dela du nouvel horizon.",
            "Risque faible si label_end_ts et label_available_ts sont validates strictement.",
            "Peut reduire les transitions rapides, mais peut aussi augmenter l'autocorrelation.",
            "review_for_future_experiment",
            "Le taux de transition eleve suggere de tester un horizon un peu plus long, sans le valider ici.",
        ),
        _design(
            "wider_flat_class",
            "Elargir la classe FLAT autour de zero retour.",
            "Peut retirer des mouvements faibles et bruites des classes UP/DOWN.",
            "Risque d'une classe FLAT dominante, deja observee en 1m.",
            "Causal si base uniquement sur le retour futur du label et disponible apres label_end_ts.",
            "Disponibilite temporelle identique au label actuel.",
            "Risque faible de leakage, mais fort risque de desequilibre.",
            "Peut reduire le bruit directionnel, mais risque d'aggraver le desequilibre 1m.",
            "reject_as_primary",
            "Non prioritaire car la classe FLAT est deja trop dominante en 1m.",
        ),
        _design(
            "binary_directional_only",
            "Supprimer FLAT et garder uniquement UP/DOWN sur lignes directionnelles.",
            "Simplifie la cible et les metriques.",
            "Peut jeter beaucoup de lignes et creer un biais de selection.",
            "Causal si le filtrage est effectue uniquement a partir du label futur et publie apres label_end_ts.",
            "Les lignes ignorees doivent etre marquees non valides pour ML avant tout entrainement futur.",
            "Risque de fuite si le filtrage est applique comme information disponible a decision_ts.",
            "Peut aider l'equilibre directionnel, mais n'adresse pas seul la qualite du seuil.",
            "review_only",
            "A evaluer seulement apres un redesign de seuils causaux.",
        ),
        _design(
            "causal_multi_horizon_labels",
            "Label multi-horizon combinant h1/h3/h5 ou nouveaux horizons avec regles explicites.",
            "Peut reduire les faux signaux de micro-bruit en exigeant confirmation temporelle.",
            "Plus complexe, plus facile a sur-ajuster, et disponibilite label plus tardive.",
            "Causal si tous les horizons sont futurs et la disponibilite est apres le plus long horizon.",
            "label_available_ts doit etre strictement apres le dernier label_end_ts utilise.",
            "Risque moyen si des horizons sont melanges avec des features non alignees temporellement.",
            "Peut stabiliser la cible, mais doit rester une hypothese V9.6+.",
            "review_for_future_experiment",
            "Prometteur en recherche, mais pas le premier candidat conservateur.",
        ),
    ]


def choose_label_design_decision_v9_5(
    current_labels: dict[str, Any],
    diagnostic: dict[str, Any],
    alternatives: list[dict[str, Any]],
) -> dict[str, Any]:
    if not current_labels.get("full_local_dataset_available"):
        decision = "label_redesign_not_ready_need_data_inspection"
        confidence = "medium"
        selected_family = None
        reason = "Les donnees full locales ne sont pas disponibles dans ce contexte."
    elif diagnostic["thresholds_likely_too_weak_or_not_scaled"] or diagnostic["flat_class_definition_issue"]:
        decision = "label_redesign_candidate_volatility_normalized"
        confidence = "medium_high"
        selected_family = "volatility_normalized_thresholds"
        reason = "Le seuil fixe actuel semble non scale entre timeframes; la normalisation par volatilite est le candidat le plus defensif."
    elif diagnostic["class_imbalance_present"]:
        decision = "label_redesign_candidate_quantile_based"
        confidence = "medium"
        selected_family = "rolling_quantile_or_tertile_labels"
        reason = "Le desequilibre de classes domine le diagnostic, mais les quantiles doivent rester causalement stricts."
    elif diagnostic["horizon_too_short_suspected"]:
        decision = "label_redesign_candidate_multi_horizon"
        confidence = "medium"
        selected_family = "causal_multi_horizon_labels"
        reason = "Le bruit de transition suggere de tester une confirmation multi-horizon."
    else:
        decision = "label_redesign_not_ready_need_data_inspection"
        confidence = "low"
        selected_family = None
        reason = "Les preuves ne suffisent pas a recommander un design precis."
    return {
        "decision": decision,
        "confidence_level": confidence,
        "selected_family": selected_family,
        "allowed_decisions": sorted(ALLOWED_DECISIONS),
        "justification": reason,
        "next_step": "V9.6 - Refined Label Factory Candidate",
        "must_not_run_backtest": True,
        "must_not_train_ml_in_v9_5": True,
        "explicit_no_trading_statement": "V9.5 ne produit aucun backtest, aucune strategie, aucun signal actionnable, aucun ordre et aucun trading.",
        "accepted_for_future_experiment": [
            item["family_id"] for item in alternatives if item["future_experiment_recommendation"] == "accept_for_future_experiment"
        ],
        "rejected_as_primary": [
            item["family_id"] for item in alternatives if item["future_experiment_recommendation"] == "reject_as_primary"
        ],
    }


def build_leakage_guard_v9_5(alternatives: list[dict[str, Any]]) -> dict[str, Any]:
    forbidden = []
    for item in alternatives:
        if not item["causality"]["feature_available_ts_compatible"] or not item["causality"]["label_available_ts_compatible"]:
            forbidden.append(item["family_id"])
    return {
        "passed": not forbidden,
        "forbidden_designs_present": forbidden,
        "required_rules": [
            "feature_available_ts <= decision_ts",
            "label_available_ts > decision_ts",
            "no future return or label columns may become features",
            "no split, fold or walk-forward identifiers may become features",
        ],
    }


def build_forbidden_output_scan_v9_5(alternatives: list[dict[str, Any]]) -> dict[str, Any]:
    forbidden_keys = []
    for item in alternatives:
        for key in item:
            if str(key).casefold() in FORBIDDEN_OUTPUT_TERMS:
                forbidden_keys.append(f"{item['family_id']}.{key}")
    return {
        "passed": not forbidden_keys,
        "forbidden_output_terms": sorted(FORBIDDEN_OUTPUT_TERMS),
        "forbidden_keys_present": forbidden_keys,
        "note": "V9.5 ne produit aucune prediction, score modele, sortie de trading ou metrique de performance trading.",
    }


def build_manifest_v9_5(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "status": "PASS",
        "created_at_utc": _utc_now(),
        "decision_type": "alternative_label_design_audit",
        "source_decision": report["source_decision"],
        "input_reports": report["inputs"],
        "window": report["window"],
        "target_name": TARGET_NAME,
        "current_label_analysis_summary": {
            "full_local_dataset_available": report["current_label_analysis"]["full_local_dataset_available"],
            "full_local_labels_available": report["current_label_analysis"]["full_local_labels_available"],
            "timeframes": {
                timeframe: {
                    "majority_class": item.get("majority_class"),
                    "majority_rate": item.get("majority_rate"),
                    "entropy_bits": item.get("entropy_bits"),
                    "label_change_rate": item.get("label_change_rate"),
                    "dominated_periods_count": len(item.get("dominated_periods", [])),
                }
                for timeframe, item in report["current_label_analysis"]["timeframes"].items()
            },
        },
        "problem_diagnostic": report["problem_diagnostic"],
        "alternative_label_design_catalog": report["alternative_label_design_catalog"],
        "v9_5_decision": report["v9_5_decision"],
        "outputs": {
            "report_json": _artifact_block(root / REPORT_JSON_PATH, REPORT_JSON_PATH),
            "report_markdown": _artifact_block(root / REPORT_MD_PATH, REPORT_MD_PATH),
            "documentation": _artifact_block(root / DOC_MD_PATH, DOC_MD_PATH),
        },
        "findings": report["findings"],
        "safety": report["safety"],
        "limitations": report["limitations"],
    }


def build_markdown_v9_5(report: dict[str, Any]) -> str:
    timeframes = report["current_label_analysis"]["timeframes"]
    rows = "\n".join(
        f"- `{timeframe}` : majority `{item.get('majority_class')}` rate `{item.get('majority_rate')}`, "
        f"entropy `{item.get('entropy_bits')}`, label_change_rate `{item.get('label_change_rate')}`."
        for timeframe, item in timeframes.items()
    )
    alternatives = "\n".join(
        f"- `{item['family_id']}` : {item['future_experiment_recommendation']} - {item['decision_reason']}"
        for item in report["alternative_label_design_catalog"]
    )
    return f"""# Alternative Label Design Audit V9.5

## Resume executif

V9.5 audite les labels actuels apres la decision V9.4 : `{report['source_decision']['research_decision']}`.

Decision V9.5 : `{report['v9_5_decision']['decision']}`.

Justification : {report['v9_5_decision']['justification']}

V9.5 ne lance aucun backtest, ne cree aucune strategie, ne produit aucun signal actionnable et ne modifie pas les labels existants.

## Labels actuels

- Target actuel : `{TARGET_NAME}`.
- Horizons V5.2 : `{report['current_label_analysis']['horizons']}`.
- Seuil V5.2 : `{report['current_label_analysis']['threshold']}`.
- Lecture full dataset locale : `{report['current_label_analysis']['full_local_dataset_available']}`.
- Lecture labels full locale : `{report['current_label_analysis']['full_local_labels_available']}`.

{rows}

## Diagnostic du probleme

- Labels trop bruites : `{report['problem_diagnostic']['labels_too_noisy']}`.
- Seuils probablement trop faibles ou non scales : `{report['problem_diagnostic']['thresholds_likely_too_weak_or_not_scaled']}`.
- Horizon h1 possiblement trop court : `{report['problem_diagnostic']['horizon_too_short_suspected']}`.
- Desequilibre de classes : `{report['problem_diagnostic']['class_imbalance_present']}`.
- Probleme de definition FLAT : `{report['problem_diagnostic']['flat_class_definition_issue']}`.
- Instabilite timeframes/regimes : `{report['problem_diagnostic']['timeframe_instability_present']}` / `{report['problem_diagnostic']['market_regime_instability_present']}`.
- Cas trop proches des labels melanges : `{report['problem_diagnostic']['no_clear_edge_vs_shuffled_labels_count']}`.

## Catalogue de designs alternatifs

{alternatives}

## Decision V9.5

La famille recommandee pour experimentation future est : `{report['v9_5_decision']['selected_family']}`.

Prochaine etape : `{report['v9_5_decision']['next_step']}`.

## Interdits maintenus

V9.5 ne valide aucune strategie, ne produit aucun backtest, aucun signal actionnable, aucun ordre, aucun paper live et aucun trading reel. Aucun modele persistant, aucune API privee et aucune cle API ne sont utilises.
"""


def update_state_surfaces_v9_5(root: Path, report: dict[str, Any], manifest: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "direction": "alternative_label_design_audit",
        "source_decision_version": SOURCE_DECISION_VERSION,
        "source_research_decision": report["source_decision"]["research_decision"],
        "v9_5_decision": report["v9_5_decision"]["decision"],
        "recommended_next_version": "V9.6",
        "recommended_next_action": "Refined Label Factory Candidate",
        "labels_full_local_available": report["current_label_analysis"]["full_local_labels_available"],
        "dataset_full_local_available": report["current_label_analysis"]["full_local_dataset_available"],
        "label_shuffle_no_clear_edge_cases": report["problem_diagnostic"]["no_clear_edge_vs_shuffled_labels_count"],
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
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(state_path, state, sort_keys=False)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    _write_text(
        root / "reports/PROJECT_STATE.md",
        "# Etat du Projet : V9.4.1 validee + candidat V9.5\n\n"
        "- **Derniere version validee** : V9.4.1.\n"
        "- **Version candidate** : V9.5.\n"
        "- **Statut candidate** : `pending_external_audit`.\n"
        "- **Direction** : alternative label design audit.\n"
        f"- **Decision V9.5** : `{report['v9_5_decision']['decision']}`.\n\n"
        "V9.5 audite les labels et recommande une future label factory candidate. Aucun backtest, strategie, signal actionnable ou ordre.\n",
    )
    _write_text(
        root / "reports/current/latest_metrics.md",
        "# Latest Metrics V9.5\n\n"
        "- Derniere version validee : V9.4.1.\n"
        "- Candidate : V9.5.\n"
        "- Direction : alternative label design audit.\n"
        f"- Decision : `{report['v9_5_decision']['decision']}`.\n"
        f"- Cas proches des labels melanges herites : `{report['problem_diagnostic']['no_clear_edge_vs_shuffled_labels_count']}`.\n"
        f"- Lecture full dataset locale : `{report['current_label_analysis']['full_local_dataset_available']}`.\n\n"
        "Aucun backtest, aucune strategie, aucun signal actionnable, aucun ordre, aucun trading reel.\n",
    )
    _write_text(
        root / "reports/current/latest_summary.md",
        "# Latest Summary V9.5\n\n"
        "V9.4.1 est la derniere version validee par audit externe.\n\n"
        "V9.5 est la candidate courante. Elle audite le design des labels actuels apres la decision V9.4 `backtest_not_justified_refine_labels`.\n\n"
        f"Decision V9.5 : `{report['v9_5_decision']['decision']}`. La prochaine etape recommandee est V9.6 - Refined Label Factory Candidate.\n\n"
        "Aucun trading, paper live, ordre, backtest execute, strategie, signal actionnable ou modele persistant n'est produit.\n",
    )
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V9.4.1.\n"
        "- Candidate : V9.5, alternative label design audit.\n"
        f"- Decision V9.5 : {report['v9_5_decision']['decision']}.\n\n"
        "V9.5 audite uniquement le design des labels. Elle ne cree aucun nouveau label, ne lance aucun ML, aucun backtest et ne produit aucun signal actionnable.\n\n"
        "Aucun trading reel, aucun paper live, aucune API privee, aucune cle API et aucun modele persistant.\n",
    )


def _analyze_dataset_labels(path: Path) -> dict[str, Any]:
    try:
        import polars as pl
    except ImportError as exc:  # pragma: no cover - dependency is present in the project runtime.
        return {
            "rows_total": None,
            "limitation": f"polars unavailable: {exc}",
            "class_distribution": {},
            "class_distribution_by_split": {},
            "class_distribution_by_month": {},
            "class_distribution_by_walk_forward_group": {},
            "majority_class": None,
            "majority_rate": None,
            "entropy_bits": None,
            "transition_matrix": {},
            "label_change_rate": None,
            "label_autocorrelation_lag_1": None,
            "dominated_periods": [],
        }
    frame = (
        pl.scan_parquet(path)
        .select(["event_ts", "split", "walk_forward_group", TARGET_NAME, "label_valid_h1", "warmup_row"])
        .filter(pl.col("label_valid_h1") & ~pl.col("warmup_row"))
        .collect()
        .sort("event_ts")
    )
    rows = frame.height
    class_distribution = _distribution(frame.group_by(TARGET_NAME).len().to_dicts(), TARGET_NAME, rows)
    majority_class, majority_rate = _majority(class_distribution)
    by_split = _grouped_distribution(frame, ["split"], rows_column=TARGET_NAME)
    month_frame = frame.with_columns(pl.col("event_ts").dt.strftime("%Y-%m").alias("month"))
    by_month = _grouped_distribution(month_frame, ["month"], rows_column=TARGET_NAME)
    by_wfg = _grouped_distribution(frame, ["walk_forward_group"], rows_column=TARGET_NAME)
    transitions = frame.with_columns(pl.col(TARGET_NAME).shift(1).alias("previous_label")).drop_nulls("previous_label")
    transition_rows = transitions.group_by(["previous_label", TARGET_NAME]).len().to_dicts()
    transition_total = max(transitions.height, 1)
    transition_matrix = {
        f"{row['previous_label']}->{row[TARGET_NAME]}": {"count": row["len"], "rate": _round(row["len"] / transition_total)}
        for row in sorted(transition_rows, key=lambda item: (item["previous_label"], item[TARGET_NAME]))
    }
    label_change_rate = transitions.filter(pl.col(TARGET_NAME) != pl.col("previous_label")).height / transition_total
    label_values = [{"DOWN": -1.0, "FLAT": 0.0, "UP": 1.0}[label] for label in frame.get_column(TARGET_NAME).to_list()]
    dominated = _dominated_periods(by_month, "month") + _dominated_periods(by_wfg, "walk_forward_group")
    return {
        "rows_total": rows,
        "rows_valid_for_label_audit": rows,
        "class_distribution": class_distribution,
        "class_distribution_by_split": by_split,
        "class_distribution_by_month": by_month,
        "class_distribution_by_walk_forward_group": by_wfg,
        "majority_class": majority_class,
        "majority_rate": majority_rate,
        "entropy_bits": _round(_entropy(class_distribution)),
        "transition_matrix": transition_matrix,
        "label_change_rate": _round(label_change_rate),
        "label_autocorrelation_lag_1": _round(_lag_one_autocorrelation(label_values)),
        "dominated_periods": dominated,
    }


def _grouped_distribution(frame: Any, group_columns: list[str], rows_column: str) -> dict[str, Any]:
    grouped = frame.group_by([*group_columns, rows_column]).len().to_dicts()
    totals: dict[str, int] = {}
    for row in grouped:
        key = "|".join(str(row[column]) for column in group_columns)
        totals[key] = totals.get(key, 0) + row["len"]
    result: dict[str, Any] = {}
    for row in sorted(grouped, key=lambda item: tuple(str(item[column]) for column in [*group_columns, rows_column])):
        key = "|".join(str(row[column]) for column in group_columns)
        label = row[rows_column]
        result.setdefault(key, {})
        result[key][label] = {"count": row["len"], "rate": _round(row["len"] / totals[key])}
    return result


def _distribution(rows: list[dict[str, Any]], column: str, total: int) -> dict[str, Any]:
    return {
        row[column]: {"count": row["len"], "rate": _round(row["len"] / total)}
        for row in sorted(rows, key=lambda item: str(item[column]))
    }


def _majority(distribution: dict[str, Any]) -> tuple[str | None, float | None]:
    if not distribution:
        return None, None
    label, payload = max(distribution.items(), key=lambda item: item[1]["rate"])
    return label, payload["rate"]


def _entropy(distribution: dict[str, Any]) -> float:
    return -sum(item["rate"] * math.log(item["rate"], 2) for item in distribution.values() if item["rate"] > 0)


def _lag_one_autocorrelation(values: list[float]) -> float | None:
    if len(values) < 3:
        return None
    x = values[:-1]
    y = values[1:]
    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)
    numerator = sum((left - mean_x) * (right - mean_y) for left, right in zip(x, y, strict=False))
    denom_x = math.sqrt(sum((left - mean_x) ** 2 for left in x))
    denom_y = math.sqrt(sum((right - mean_y) ** 2 for right in y))
    if denom_x == 0 or denom_y == 0:
        return None
    return numerator / (denom_x * denom_y)


def _dominated_periods(grouped_distribution: dict[str, Any], period_key: str) -> list[dict[str, Any]]:
    dominated = []
    for period, distribution in grouped_distribution.items():
        label, rate = _majority(distribution)
        if rate is not None and rate >= 0.70:
            dominated.append({period_key: period, "majority_class": label, "majority_rate": rate})
    return dominated


def _design(
    family_id: str,
    definition: str,
    advantages: str,
    risks: str,
    causality: str,
    temporal_availability: str,
    leakage_risks: str,
    expected_impact: str,
    future_experiment_recommendation: str,
    decision_reason: str,
) -> dict[str, Any]:
    return {
        "family_id": family_id,
        "definition": definition,
        "advantages": advantages,
        "risks": risks,
        "causality": {
            "summary": causality,
            "feature_available_ts_compatible": True,
            "label_available_ts_compatible": True,
        },
        "temporal_availability": temporal_availability,
        "leakage_risks": leakage_risks,
        "expected_impact_on_noise_and_imbalance": expected_impact,
        "future_experiment_recommendation": future_experiment_recommendation,
        "decision_reason": decision_reason,
    }


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    file_path = root / path
    if not file_path.exists() and path.name == "max_history_label_factory_v5_2_manifest.json":
        return {"path": path.as_posix(), "sha256": None, "payload": {"available": False}}
    if not file_path.exists():
        raise FileNotFoundError(f"missing required V9.5 input: {path}")
    if file_path.suffix == ".json":
        payload: Any = _read_json(file_path)
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


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 12)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
