from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.public_market.provenance import sha256_file, utc_now_iso


VERSION_V9_10 = "V9.10"
MANIFEST_PATH_V9_10 = Path("reports/manifests/refined_volnorm_research_decision_gate_v9_10_manifest.json")
REPORT_JSON_PATH_V9_10 = Path("reports/research_decisions/refined_volnorm_research_decision_gate_v9_10.json")
REPORT_MD_PATH_V9_10 = Path("reports/research_decisions/refined_volnorm_research_decision_gate_v9_10.md")
DOC_PATH_V9_10 = Path("docs/refined_volnorm_research_decision_gate_v9_10.md")
INPUTS_V9_10 = {
    "labels_v9_6": Path("reports/labels/refined_volatility_normalized_labels_v9_6.json"),
    "dataset_v9_7": Path("reports/datasets/refined_volnorm_labels_dataset_v9_7.json"),
    "ml_v9_8": Path("reports/ml/refined_volnorm_labels_offline_ml_v9_8.json"),
    "scores_v9_8": Path("reports/ml/refined_volnorm_labels_offline_scores_v9_8.json"),
    "walk_forward_v9_9": Path("reports/ml/refined_volnorm_strict_walk_forward_v9_9.json"),
    "walk_forward_scores_v9_9": Path("reports/ml/refined_volnorm_strict_walk_forward_scores_v9_9.json"),
    "decision_v9_4": Path("reports/research_decisions/refined_research_decision_gate_v9_4.json"),
    "audit_v9_5": Path("reports/research_decisions/alternative_label_design_audit_v9_5.json"),
}
ALLOWED_DECISIONS_V9_10 = {
    "backtest_not_justified_refine_labels_again",
    "backtest_not_justified_refine_features",
    "backtest_not_justified_extend_data",
    "limited_research_backtest_candidate",
    "stop_refined_branch",
}
FINDINGS_V9_10 = {
    "robust_edge_claimed": False,
    "strategy_validated": False,
    "backtest_performed": False,
    "actionable_signal_produced": False,
    "walk_forward_validated_for_trading": False,
    "trading_allowed": False,
    "paper_live_allowed": False,
    "real_trading_allowed": False,
}
SAFETY_FLAGS_V9_10 = {
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
    "persistent_model_created": False,
}


def run_refined_volnorm_research_decision_gate_v9_10(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    inputs = {name: _load_input(root, path) for name, path in INPUTS_V9_10.items()}
    report = build_decision_gate_v9_10(inputs)
    _write_json(root / REPORT_JSON_PATH_V9_10, report)
    _write_json(root / MANIFEST_PATH_V9_10, build_manifest_v9_10(root, report, inputs))
    markdown = build_markdown_v9_10(report)
    _write_text(root / REPORT_MD_PATH_V9_10, markdown)
    _write_text(root / DOC_PATH_V9_10, markdown)
    update_state_surfaces_v9_10(root, report)
    return report


def build_decision_gate_v9_10(inputs: dict[str, Any]) -> dict[str, Any]:
    labels = inputs["labels_v9_6"]["payload"]
    dataset = inputs["dataset_v9_7"]["payload"]
    ml = inputs["ml_v9_8"]["payload"]
    wf = inputs["walk_forward_v9_9"]["payload"]
    label_assessment = assess_labels_v9_10(labels)
    ml_assessment = assess_static_ml_v9_10(ml)
    wf_assessment = assess_walk_forward_v9_10(wf)
    leakage = {
        "labels": labels.get("leakage_guard", {}),
        "ml": ml.get("feature_leakage_scan", {}),
        "walk_forward": wf.get("feature_leakage_scan", {}),
        "passed": labels.get("leakage_guard", {}).get("passed") is True
        and ml.get("feature_leakage_scan", {}).get("passed") is True
        and wf.get("feature_leakage_scan", {}).get("passed") is True,
    }
    forbidden_metrics = {
        "ml": ml.get("metric_forbidden_scan", {}),
        "walk_forward": wf.get("metric_forbidden_scan", {}),
        "passed": ml.get("metric_forbidden_scan", {}).get("passed") is True and wf.get("metric_forbidden_scan", {}).get("passed") is True,
    }
    decision = choose_research_decision_v9_10(label_assessment, ml_assessment, wf_assessment, leakage, forbidden_metrics)
    return {
        "version": VERSION_V9_10,
        "status": "PASS",
        "decision_gate_type": "research_only",
        "created_at_utc": utc_now_iso(),
        "inputs": {name: {"path": item["path"], "sha256": item["sha256"]} for name, item in inputs.items()},
        "label_quality_assessment": label_assessment,
        "dataset_assessment": {"decision": dataset.get("decision"), "status": dataset.get("status"), "target_name": dataset.get("target_name")},
        "static_split_assessment_v9_8": ml_assessment,
        "walk_forward_assessment_v9_9": wf_assessment,
        "comparison_v9_8_vs_v9_9": compare_static_vs_walk_forward_v9_10(ml, wf),
        "comparison_to_prior_conclusions": {
            "v9_4_decision": inputs["decision_v9_4"]["payload"].get("research_decision"),
            "v9_5_decision": inputs["audit_v9_5"]["payload"].get("v9_5_decision", {}).get("decision"),
            "interpretation": "La comparaison reste descriptive; aucune conclusion trading n'est produite.",
        },
        "leakage_assessment": leakage,
        "metric_forbidden_scan": forbidden_metrics,
        "research_decision": decision["decision"],
        "decision_justification": decision["justification"],
        "evidence": decision["evidence"],
        "warnings": decision["warnings"],
        "confidence": decision["confidence"],
        "next_step_recommendation": decision["next_step_recommendation"],
        "explicit_no_trading_statement": "V9.10 ne fait aucun backtest et n'autorise aucun trading, paper live, ordre, strategie ou signal actionnable.",
        "findings": dict(FINDINGS_V9_10),
        "safety": dict(SAFETY_FLAGS_V9_10),
        "limitations": [
            "V9.10 est un decision gate de recherche uniquement.",
            "V9.10 ne lance aucun backtest, ne produit aucune strategie, aucun signal actionnable et aucun ordre.",
            "Toute suite eventuelle doit etre une version separee et auditee.",
        ],
    }


def assess_labels_v9_10(labels: dict[str, Any]) -> dict[str, Any]:
    over_70 = []
    flat_1m = None
    for timeframe, quality in labels.get("quality", {}).items():
        if quality.get("majority_rate", 0.0) > 0.70:
            over_70.append(timeframe)
        if timeframe == "1m":
            flat_1m = quality.get("class_distribution", {}).get("FLAT", {}).get("rate")
    return {
        "decision": labels.get("decision"),
        "selected_multiplier": labels.get("selected_volatility_threshold_multiplier"),
        "class_majority_over_70_timeframes": over_70,
        "flat_rate_1m": flat_1m,
        "label_quality_passed": labels.get("status") == "PASS" and not over_70,
    }


def assess_static_ml_v9_10(ml: dict[str, Any]) -> dict[str, Any]:
    no_clear = [key for key, value in ml.get("label_shuffle_falsification", {}).items() if value.get("no_clear_edge_vs_shuffled_labels")]
    learned = [value for value in ml.get("metrics", {}).values() if value.get("model_name") in {"logistic_regression", "decision_tree_depth_2"} and value.get("split") in {"validation", "test"}]
    best_macro_f1 = max((item.get("macro_f1", 0.0) for item in learned), default=0.0)
    return {
        "decision": ml.get("decision"),
        "no_clear_edge_vs_shuffled_labels_count": len(no_clear),
        "best_learned_validation_test_macro_f1": best_macro_f1,
        "learned_models_clearly_useful": best_macro_f1 >= 0.45 and not no_clear,
    }


def assess_walk_forward_v9_10(wf: dict[str, Any]) -> dict[str, Any]:
    no_clear = [key for key, value in wf.get("label_shuffle_falsification", {}).items() if value.get("no_clear_edge_vs_shuffled_labels")]
    warnings = wf.get("findings", {}).get("warnings", [])
    weak_folds = []
    unstable = []
    for key, value in wf.get("aggregate_metrics", {}).items():
        weak_folds.extend(value.get("weak_folds", []) or [])
        unstable.extend(value.get("unstable_folds", []) or [])
    return {
        "decision": wf.get("decision"),
        "no_clear_edge_vs_shuffled_labels_count": len(no_clear),
        "weak_folds_count": len(weak_folds),
        "unstable_folds_count": len(unstable),
        "warnings_count": len(warnings),
        "walk_forward_clean_enough_for_backtest_candidate": len(no_clear) == 0 and len(weak_folds) == 0 and len(unstable) == 0 and len(warnings) == 0,
    }


def compare_static_vs_walk_forward_v9_10(ml: dict[str, Any], wf: dict[str, Any]) -> dict[str, Any]:
    return {
        "static_split_decision": ml.get("decision"),
        "walk_forward_decision": wf.get("decision"),
        "coherent": "close_to_shuffled" not in str(wf.get("decision")) or "close_to_shuffled" in str(ml.get("decision")),
        "warning": "V9.8 static split et V9.9 walk-forward strict ne sont pas des designs equivalants.",
    }


def choose_research_decision_v9_10(label_assessment: dict[str, Any], ml_assessment: dict[str, Any], wf_assessment: dict[str, Any], leakage: dict[str, Any], forbidden_metrics: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    if not leakage.get("passed"):
        return _decision("stop_refined_branch", "Fuite potentielle detectee.", ["leakage_failed"], warnings, "low", "Corriger le leakage avant toute suite.")
    if not forbidden_metrics.get("passed"):
        return _decision("stop_refined_branch", "Metrique trading interdite detectee.", ["forbidden_metric_failed"], warnings, "low", "Retirer toute metrique interdite.")
    if wf_assessment["no_clear_edge_vs_shuffled_labels_count"] > 0:
        warnings.append("Des cas walk-forward restent trop proches des labels melanges.")
        return _decision("backtest_not_justified_refine_labels_again", "Les labels volatility-normalized ne sont pas encore proprement falsifies.", [wf_assessment, ml_assessment, label_assessment], warnings, "medium", "Revoir le design des labels ou les seuils avant toute idee de backtest.")
    if not wf_assessment["walk_forward_clean_enough_for_backtest_candidate"]:
        warnings.append("Instabilite ou faiblesse residuelle en walk-forward.")
        return _decision("backtest_not_justified_refine_features", "La validation walk-forward reste instable.", [wf_assessment, ml_assessment], warnings, "medium", "Revenir aux features ou a la robustesse avant un backtest.")
    if not ml_assessment["learned_models_clearly_useful"]:
        warnings.append("Les modeles appris ne depassent pas clairement les baselines.")
        return _decision("backtest_not_justified_extend_data", "Le signal descriptif reste faible sur un an.", [ml_assessment, wf_assessment], warnings, "medium", "Etendre les donnees avant toute evaluation plus couteuse.")
    return _decision("limited_research_backtest_candidate", "Les criteres stricts descriptifs sont satisfaits, mais aucun backtest n'est lance en V9.10.", [label_assessment, ml_assessment, wf_assessment], warnings, "low", "Soumettre cette hypothese a audit externe avant une version de backtest research separee.")


def _decision(decision: str, justification: str, evidence: Any, warnings: list[str], confidence: str, next_step: str) -> dict[str, Any]:
    return {
        "decision": decision,
        "justification": justification,
        "evidence": evidence,
        "warnings": warnings,
        "confidence": confidence,
        "next_step_recommendation": next_step,
    }


def build_manifest_v9_10(root: Path, report: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION_V9_10,
        "status": report["status"],
        "created_at_utc": report["created_at_utc"],
        "decision_gate_type": report["decision_gate_type"],
        "research_decision": report["research_decision"],
        "inputs": report["inputs"],
        "report_path": REPORT_JSON_PATH_V9_10.as_posix(),
        "report_sha256": sha256_file(root / REPORT_JSON_PATH_V9_10) if (root / REPORT_JSON_PATH_V9_10).exists() else None,
        "findings": report["findings"],
        "safety": report["safety"],
        "limitations": report["limitations"],
    }


def build_markdown_v9_10(report: dict[str, Any]) -> str:
    return (
        "# V9.10 - Research decision gate v2\n\n"
        f"- Decision : `{report['research_decision']}`.\n"
        f"- Justification : {report['decision_justification']}\n"
        f"- Confiance : `{report['confidence']}`.\n"
        f"- Recommandation : {report['next_step_recommendation']}\n\n"
        "V9.10 ne lance aucun backtest, ne valide aucune strategie, ne produit aucun signal actionnable, aucun ordre, aucun paper live et aucun trading reel.\n"
    )


def update_state_surfaces_v9_10(root: Path, report: dict[str, Any]) -> None:
    project_state = _read_json(root / "reports/PROJECT_STATE.json") if (root / "reports/PROJECT_STATE.json").exists() else {}
    project_state.update(
        {
            "last_validated_version": "V9.5",
            "candidate_version": "V9.6_to_V9.10",
            "candidate_status": "pending_external_audit",
            "direction": "refined_volatility_normalized_labels_research_chain",
            "research_decision_v9_10": report["research_decision"],
            "trading_enabled": False,
            "paper_live_enabled": False,
            "orders_enabled": False,
            "backtest_performed": False,
            "strategy_enabled": False,
            "actionable_signal_produced": False,
            "persistent_model_created": False,
            "api_key_used": False,
            "private_endpoint_used": False,
            "zip_fingerprints_enabled": False,
            "sidecars_enabled": False,
        }
    )
    _write_json(root / "reports/PROJECT_STATE.json", project_state)
    latest = {
        "last_validated_version": "V9.5",
        "candidate_version": "V9.6_to_V9.10",
        "candidate_status": "pending_external_audit",
        "direction": "refined_volatility_normalized_labels_research_chain",
        "research_decision_v9_10": report["research_decision"],
        "no_trading": True,
        "no_backtest_performed": True,
        "no_orders": True,
        "no_strategy": True,
        "no_actionable_signal": True,
        "no_sidecars": True,
        "no_zip_fingerprints": True,
    }
    _write_json(root / "reports/current/latest_metrics.json", latest)
    latest_md = "# Synthese courante - V9.6_to_V9.10\n\n"
    latest_md += f"- Derniere version validee : `V9.5`.\n- Candidate : `V9.6_to_V9.10`.\n- Decision V9.10 : `{report['research_decision']}`.\n"
    latest_md += "- Aucun trading, aucun ordre, aucun backtest, aucune strategie, aucun signal actionnable.\n- Aucun sidecar et aucune empreinte ZIP.\n"
    _write_text(root / "reports/current/latest_summary.md", latest_md)
    _write_text(root / "reports/current/latest_metrics.md", latest_md)
    _write_text(root / "reports/PROJECT_STATE.md", latest_md)


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    return {"path": path.as_posix(), "sha256": sha256_file(full), "payload": _read_json(full)}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
