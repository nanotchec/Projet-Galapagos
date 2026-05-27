from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


VERSION = "V9.14.1"
SOURCE_VERSION = "V9.14"
LAST_VALIDATED_VERSION = "V9.13"
CORRECTION_SCOPE = "data_source_inventory_and_branch_decision_correction"
REPORT_JSON_PATH = Path("reports/research_decisions/feature_label_separability_v9_14_1.json")
REPORT_MD_PATH = Path("reports/research_decisions/feature_label_separability_v9_14_1.md")
MANIFEST_PATH = Path("reports/manifests/feature_label_separability_v9_14_1_manifest.json")
DOC_PATH = Path("docs/feature_label_separability_v9_14_1.md")

ALLOWED_DECISIONS = {
    "feature_first_before_more_labels",
    "data_extension_first_before_more_labels",
    "extend_data_window_first",
    "label_redesign_binary_directional_candidate",
    "label_redesign_quantile_candidate",
    "stop_refined_label_branch",
    "inconclusive_need_manual_review",
}

REQUIRED_SOURCE_NAMES = [
    "ohlcv",
    "public_trades_aggTrades",
    "order_book_l2",
    "funding_rates",
    "open_interest",
    "liquidations",
    "long_short_ratios",
    "multi_exchange_multi_venue",
    "on_chain",
    "macro_news_sentiment",
    "other_derivatives",
]

INPUT_PATHS = {
    "v9_14_report": Path("reports/research_decisions/feature_label_separability_v9_14.json"),
    "v9_14_markdown": Path("reports/research_decisions/feature_label_separability_v9_14.md"),
    "v9_14_manifest": Path("reports/manifests/feature_label_separability_v9_14_manifest.json"),
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
    "project_state_md": Path("reports/PROJECT_STATE.md"),
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
    "api_key_used": False,
    "private_endpoint_used": False,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
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


def run_feature_label_separability_v9_14_1(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_feature_label_separability_report_v9_14_1(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_14_1(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    manifest = build_manifest_v9_14_1(report)
    _write_json(root / MANIFEST_PATH, manifest)
    update_state_surfaces_v9_14_1(root, report)
    return report


def build_feature_label_separability_report_v9_14_1(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    payloads = {name: item["payload"] for name, item in inputs.items()}
    v9_14 = payloads.get("v9_14_report", {})
    data_inventory = build_data_source_inventory_v9_14_1(root)
    label_summary = summarize_label_diagnostics_v9_14_1(v9_14)
    ml_summary = summarize_ml_diagnostics_v9_14_1(v9_14)
    separability_summary = summarize_separability_v9_14_1(v9_14)
    hypotheses = classify_hypotheses_v9_14_1(label_summary, ml_summary, separability_summary, data_inventory)
    decision = decide_v9_14_1(v9_14, hypotheses, data_inventory, ml_summary, separability_summary)
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "correction_scope": CORRECTION_SCOPE,
        "status": "PASS",
        "created_at_utc": _utc_now(),
        "previous_v9_14_decision": v9_14.get("v9_14_decision", {}).get("decision"),
        "corrected_decision": decision["decision"],
        "confidence": decision["confidence"],
        "decision_rationale": decision,
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "label_diagnostic_summary": label_summary,
        "ml_diagnostic_summary": ml_summary,
        "feature_label_separability_summary": separability_summary,
        "data_source_inventory": data_inventory,
        "data_extension_recommendation": build_data_extension_recommendation_v9_14_1(data_inventory, decision),
        "hypothesis_ranking": hypotheses,
        "next_recommendation": decision["next_recommendation"],
        "blockers": [],
        "warnings": [
            "La decision V9.14 precedente ne couvrait pas assez explicitement les sources data au-dela de OHLCV + aggTrades.",
            "Les sources derivatives/macro detectees restent hors chaine V9 validee et demandent une version separee de readiness avant integration.",
        ],
        "limitations": [
            "V9.14.1 corrige uniquement l'inventaire data-extension et la decision de branche de V9.14.",
            "V9.14.1 ne cree aucun nouveau label, dataset, score ML, walk-forward, backtest, strategie, signal actionnable ou ordre.",
            "La presence d'une source n'est affirmee que lorsqu'un chemin local ou un rapport local la prouve.",
        ],
        "findings": dict(FINDINGS),
        "safety": dict(SAFETY),
        "safety_flags": dict(SAFETY_FLAGS),
    }


def build_data_source_inventory_v9_14_1(root: Path) -> list[dict[str, Any]]:
    entries = [
        _inventory_entry(
            root,
            source_name="ohlcv",
            candidates=[
                "reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json",
                "reports/features/refined_ohlcv_trades_feature_store_v9_0.json",
                "reports/manifests/ohlcv_resampling_v2_4_manifest.json",
                "data/research/v9_0/features/refined_ohlcv_trades",
            ],
            used=True,
            known_quality="good",
            known_coverage="Fenetre validee 2023-03-25 a 2024-03-24 sur 1m, 5m, 15m et 1h.",
            known_frequency="1m, 5m, 15m, 1h.",
            causality="good",
            availability="good",
            leakage="low",
            complexity="low",
            value="medium",
            priority="not_recommended_now",
            notes="Source deja integree dans la chaine V9 validee; elle ne repond pas seule au besoin de data-extension.",
        ),
        _inventory_entry(
            root,
            source_name="public_trades_aggTrades",
            candidates=[
                "reports/manifests/public_trades_1y_window_v8_2_manifest.json",
                "reports/data_quality/public_trades_1y_window_v8_2.json",
                "reports/manifests/ohlcv_trades_1y_feature_store_v8_3_manifest.json",
                "reports/features/ohlcv_trades_1y_feature_store_v8_3.json",
                "data/research/v8_2/trades/aggTrades",
            ],
            used=True,
            known_quality="good",
            known_coverage="aggTrades publics BTCUSDT spot sur la fenetre 2023-03-25 a 2024-03-24.",
            known_frequency="trade aggregation disponible puis features par timeframe.",
            causality="good",
            availability="good",
            leakage="low",
            complexity="low",
            value="medium",
            priority="not_recommended_now",
            notes="Source deja utilisee par les features refined V9.0; un raffinement feature reste possible mais ce n'est pas une nouvelle source.",
        ),
        _inventory_entry(
            root,
            source_name="order_book_l2",
            candidates=[],
            used=False,
            known_quality="not_available",
            known_coverage="Aucune trace locale validee de snapshots L2/order book full.",
            known_frequency="inconnue.",
            causality="medium",
            availability="unknown",
            leakage="medium",
            complexity="high",
            value="high",
            priority="missing_or_unknown",
            notes="Potentiellement utile, mais aucune presence locale ne doit etre supposee sans fichier ou rapport probant.",
        ),
        _inventory_entry(
            root,
            source_name="funding_rates",
            candidates=[
                "src/galapagos/data/derivatives/binance_futures.py",
                "src/galapagos/data/derivatives/bybit_v5.py",
                "reports/research/derivatives_coverage_v1_14.json",
                "reports/research/derivatives_data_quality_v1_14.json",
                "reports/research/derivatives_features_v1_14.json",
                "reports/research/derivatives_readiness_v1_12_2.json",
                "data/silver/derivatives",
                "data/gold/derivatives_features/BTCUSDT/4h",
            ],
            used=False,
            known_quality="partial",
            known_coverage="Rapports V1.14 indiquent donnees derivatives partielles, dont funding Binance/Bybit; features gold 4h presentes.",
            known_frequency="principalement 4h dans les artefacts locaux inspectes.",
            causality="good",
            availability="medium",
            leakage="low",
            complexity="medium",
            value="high",
            priority="priority_1_candidate",
            notes="Meilleure source data-extension deja amorcee localement, mais non integree a la chaine V9 validee.",
        ),
        _inventory_entry(
            root,
            source_name="open_interest",
            candidates=[
                "src/galapagos/data/derivatives/features.py",
                "reports/research/derivatives_coverage_v1_14.json",
                "reports/research/derivatives_data_quality_v1_14.json",
                "reports/research/derivatives_features_v1_14.json",
                "data/silver/derivatives",
                "data/gold/derivatives_features/BTCUSDT/4h",
            ],
            used=False,
            known_quality="partial",
            known_coverage="Open interest mentionne dans les rapports derivatives; couverture partielle selon V1.14.",
            known_frequency="4h ou snapshots publics selon source.",
            causality="good",
            availability="medium",
            leakage="low",
            complexity="medium",
            value="high",
            priority="priority_1_candidate",
            notes="Complement naturel pour tester si les regimes derivatives expliquent la faible separabilite OHLCV+aggTrades.",
        ),
        _inventory_entry(
            root,
            source_name="liquidations",
            candidates=[],
            used=False,
            known_quality="not_available",
            known_coverage="Aucun fichier local de liquidations identifie.",
            known_frequency="inconnue.",
            causality="medium",
            availability="poor",
            leakage="medium",
            complexity="high",
            value="medium",
            priority="missing_or_unknown",
            notes="A ne pas prioriser tant qu'une source publique historique sans secret n'est pas prouvee.",
        ),
        _inventory_entry(
            root,
            source_name="long_short_ratios",
            candidates=[
                "src/galapagos/data/derivatives/features.py",
                "reports/research/derivatives_coverage_v1_14.json",
                "reports/research/derivatives_data_quality_v1_14.json",
                "reports/research/derivatives_features_v1_14.json",
                "data/silver/derivatives",
                "data/gold/derivatives_features/BTCUSDT/4h",
            ],
            used=False,
            known_quality="partial",
            known_coverage="Ratios long/short presents dans les rapports derivatives, avec limitations de couverture.",
            known_frequency="4h dans les features derivatives locales.",
            causality="medium",
            availability="medium",
            leakage="medium",
            complexity="medium",
            value="medium",
            priority="priority_2_candidate",
            notes="Utile apres funding/open interest, a condition de clarifier publication time et couverture historique.",
        ),
        _inventory_entry(
            root,
            source_name="multi_exchange_multi_venue",
            candidates=[
                "src/galapagos/data/derivatives/bybit_v5.py",
                "reports/research/derivatives_fetch_bybit_v1_14.json",
                "reports/research/derivatives_fetch_binance_v1_14.json",
                "data/silver/derivatives/bybit",
                "data/silver/derivatives/binance",
                "data/silver/ohlcv/kraken",
            ],
            used=False,
            known_quality="partial",
            known_coverage="Binance/Bybit derivatives et traces OHLCV Kraken existent hors chaine V9 validee.",
            known_frequency="4h principalement pour les artefacts derivatives; OHLCV Kraken 30m/4h visible localement.",
            causality="medium",
            availability="medium",
            leakage="medium",
            complexity="high",
            value="medium",
            priority="priority_2_candidate",
            notes="Candidat secondaire apres consolidation d'une premiere source derivatives causale.",
        ),
        _inventory_entry(
            root,
            source_name="on_chain",
            candidates=[],
            used=False,
            known_quality="not_available",
            known_coverage="Aucun module, rapport ou data path on-chain local probant.",
            known_frequency="inconnue.",
            causality="unknown",
            availability="unknown",
            leakage="unknown",
            complexity="high",
            value="unknown",
            priority="missing_or_unknown",
            notes="Non recommande maintenant faute de preuve locale et de garde-fous d'acquisition.",
        ),
        _inventory_entry(
            root,
            source_name="macro_news_sentiment",
            candidates=[
                "src/galapagos/data/macro/fred_client.py",
                "src/galapagos/data/macro/macro_features.py",
                "reports/research/fred_macro_readiness_v1_12_2.json",
                "data/silver/macro",
                "data/gold/macro_features/4h",
            ],
            used=False,
            known_quality="partial",
            known_coverage="Macro FRED localement tracee; aucune source news/sentiment locale probante.",
            known_frequency="macro 4h apres alignement; news/sentiment absents.",
            causality="medium",
            availability="medium",
            leakage="medium",
            complexity="medium",
            value="medium",
            priority="later_candidate",
            notes="A evaluer plus tard; certaines acquisitions macro peuvent requerir une cle externe et doivent rester separees.",
        ),
        _inventory_entry(
            root,
            source_name="other_derivatives",
            candidates=[
                "src/galapagos/data/derivatives/features.py",
                "reports/research/derivatives_features_v1_14.json",
                "reports/research/derivatives_signal_quality_v1_14.json",
                "reports/research/with_without_derivatives_v1_14.json",
                "data/gold/derivatives_features/BTCUSDT/4h",
            ],
            used=False,
            known_quality="partial",
            known_coverage="Premium/taker ratio et autres features derivatives visibles dans les rapports/features V1.14.",
            known_frequency="4h dans les features locales.",
            causality="medium",
            availability="medium",
            leakage="medium",
            complexity="medium",
            value="medium",
            priority="priority_2_candidate",
            notes="A examiner apres funding/open interest pour eviter une integration trop large d'un coup.",
        ),
    ]
    return entries


def _inventory_entry(
    root: Path,
    *,
    source_name: str,
    candidates: list[str],
    used: bool,
    known_quality: str,
    known_coverage: str,
    known_frequency: str,
    causality: str,
    availability: str,
    leakage: str,
    complexity: str,
    value: str,
    priority: str,
    notes: str,
) -> dict[str, Any]:
    evidence = [candidate for candidate in candidates if (root / candidate).exists()]
    present = bool(evidence)
    return {
        "source_name": source_name,
        "present_in_repo": present,
        "used_in_validated_v9_chain": used,
        "evidence_paths": evidence,
        "known_quality": known_quality if present else ("not_available" if known_quality != "unknown" else "unknown"),
        "known_coverage": known_coverage,
        "known_frequency": known_frequency,
        "causality_feasibility": causality,
        "historical_availability": availability,
        "leakage_risk": leakage,
        "integration_complexity": complexity,
        "potential_value": value,
        "recommended_priority": priority if present or priority == "missing_or_unknown" else "missing_or_unknown",
        "notes": notes,
    }


def summarize_label_diagnostics_v9_14_1(v9_14_report: dict[str, Any]) -> dict[str, Any]:
    label = v9_14_report.get("label_diagnostic_v9_13", {})
    return {
        "target_name": v9_14_report.get("target_name"),
        "flat_low_timeframes": label.get("flat_low_timeframes", []),
        "flat_high_timeframes": label.get("flat_high_timeframes", []),
        "full_parquet_read_only_used_in_v9_14": label.get("full_parquet_read_only_used"),
        "interpretation": "Le h4 reduit certains desequilibres mais conserve un profil FLAT trop faible en 1m et trop eleve en 1h.",
    }


def summarize_ml_diagnostics_v9_14_1(v9_14_report: dict[str, Any]) -> dict[str, Any]:
    ml = v9_14_report.get("ml_diagnostic_v9_13", {})
    return {
        "clear_wins_vs_baselines": ml.get("learned_vs_baselines", {}).get("clear_wins_count"),
        "mean_delta_macro_f1_vs_best_baseline": ml.get("learned_vs_baselines", {}).get("mean_delta_macro_f1_vs_best_baseline"),
        "no_clear_edge_vs_shuffled_labels_count": ml.get("learned_vs_shuffled_labels", {}).get("no_clear_edge_vs_shuffled_labels_count"),
        "mean_delta_original_vs_shuffled": ml.get("learned_vs_shuffled_labels", {}).get("mean_delta_original_vs_shuffled"),
        "class_collapse_cases_count": ml.get("class_collapse_cases_count"),
        "walk_forward_not_repeated_in_v9_14": ml.get("walk_forward_not_repeated_in_v9_14"),
        "interpretation": "Le diagnostic ML V9.13 reste faible, proche des labels melanges et sans clear win baseline.",
    }


def summarize_separability_v9_14_1(v9_14_report: dict[str, Any]) -> dict[str, Any]:
    separability = v9_14_report.get("feature_label_separability", {})
    summary = separability.get("summary", {})
    return {
        "common_top_features_count": summary.get("common_top_features_count"),
        "unstable_top_features_count": summary.get("unstable_top_features_count"),
        "low_discrimination_features_count": summary.get("low_discrimination_features_count"),
        "common_top_features_between_timeframes": separability.get("common_top_features_between_timeframes", []),
        "unstable_top_features": separability.get("unstable_top_features", []),
        "model_training_performed": separability.get("model_training_performed"),
        "signal_produced": separability.get("signal_produced"),
        "interpretation": "Aucune top feature commune stable entre timeframes; la separabilite OHLCV+aggTrades reste faible.",
    }


def classify_hypotheses_v9_14_1(
    label_summary: dict[str, Any],
    ml_summary: dict[str, Any],
    separability_summary: dict[str, Any],
    inventory: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    no_clear = int(ml_summary.get("no_clear_edge_vs_shuffled_labels_count") or 0)
    clear_wins = int(ml_summary.get("clear_wins_vs_baselines") or 0)
    common_top = int(separability_summary.get("common_top_features_count") or 0)
    priority_data = [item["source_name"] for item in inventory if item["recommended_priority"] == "priority_1_candidate" and not item["used_in_validated_v9_chain"]]
    return [
        _hyp("H1", "label encore mal defini", "likely", [f"{no_clear} cas restent proches des labels melanges."], ["Le h4 corrige partiellement la distribution du label."], "medium", "Ne pas relancer de walk-forward; revoir les conditions de label seulement apres inventaire data."),
        _hyp("H2", "features actuelles insuffisantes", "likely", [f"clear wins baseline={clear_wins}.", f"top features communes={common_top}."], ["Des features OHLCV+aggTrades existent et sont techniquement propres."], "high", "Tester d'abord des sources complementaires ou une selection feature plus ciblee."),
        _hyp("H3", "horizon h4 pas adapte", "possible", ["Le h4 reste proche des labels melanges."], ["Il ameliore legerement la distance moyenne vs V9.8."], "medium", "Ne pas prioriser un nouvel horizon sans source data complementaire."),
        _hyp("H4", "multi-classe DOWN/FLAT/UP trop difficile", "possible", [f"FLAT faible sur {label_summary.get('flat_low_timeframes', [])} et eleve sur {label_summary.get('flat_high_timeframes', [])}."], ["Aucune classe ne depasse 70 % sur le candidat h4/k=1.25."], "medium", "Garder le binaire comme hypothese secondaire, pas decision principale."),
        _hyp("H5", "fenetre 2023-2024 trop limitee", "possible", ["Stabilite regime non prouvee sur une seule fenetre d'un an."], ["OHLCV/aggTrades V9 sont deja complets sur 366 jours."], "medium", "Extension de fenetre possible apres examen de disponibilite multi-annees."),
        _hyp("H6", "OHLCV+trades agreges ne contiennent pas assez d'information", "likely", [f"top features instables={separability_summary.get('unstable_top_features_count')}."], ["Les donnees trades publiques apportent deja des proxys de flux."], "high", "Prioriser data-extension derivatives/microstructure avant nouveau label complexe."),
        _hyp("H7", "besoin d'extension data/features avant nouveau label", "likely", [f"Sources priority_1 detectees: {priority_data}."], ["Ces sources ne sont pas encore integrees dans la chaine V9 validee."], "high", "Creer une version V9.15 de readiness data-extension."),
        _hyp("H8", "besoin d'arreter la branche refined labels", "possible", ["Plusieurs redesigns labels successifs restent faibles."], ["Des sources derivatives/macro existent encore hors chaine V9."], "medium", "Ne pas arreter avant un diagnostic data-extension strict."),
        _hyp("H9", "besoin d'un label binaire plus simple avant toute autre chose", "possible", ["Collapses de classes et instabilite FLAT indiquent une difficulte multi-classe."], ["Le probleme de separabilite des features reste dominant."], "medium", "Hypothese secondaire si data-extension ne reduit pas le bruit."),
        _hyp("H10", "besoin d'un label quantile-based plutot que seuil directionnel", "possible", ["Un label quantile pourrait regulariser les distributions."], ["Un label plus equilibre ne cree pas necessairement d'information predictive."], "medium", "A garder en reserve apres diagnostic des sources complementaires."),
        _hyp("H11", "besoin de microstructure / derivatives pour esperer une separabilite", "likely", [f"Sources complementaires prioritaires detectees: {priority_data}."], ["Order book L2 et liquidations ne sont pas prouves localement."], "high", "Decision corrigee orientee data-extension avant nouveaux labels."),
    ]


def _hyp(
    item_id: str,
    hypothesis: str,
    status: str,
    evidence_for: list[str],
    evidence_against: list[str],
    confidence: str,
    consequence: str,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "hypothesis": hypothesis,
        "status": status,
        "evidence_for": evidence_for,
        "evidence_against": evidence_against,
        "confidence": confidence,
        "consequence_next_version": consequence,
    }


def decide_v9_14_1(
    v9_14_report: dict[str, Any],
    hypotheses: list[dict[str, Any]],
    inventory: list[dict[str, Any]],
    ml_summary: dict[str, Any],
    separability_summary: dict[str, Any],
) -> dict[str, Any]:
    current_features_weak = int(ml_summary.get("clear_wins_vs_baselines") or 0) == 0 and int(separability_summary.get("common_top_features_count") or 0) == 0
    priority_sources = [
        item["source_name"]
        for item in inventory
        if item["recommended_priority"] == "priority_1_candidate" and item["present_in_repo"] is True and item["used_in_validated_v9_chain"] is False
    ]
    previous = v9_14_report.get("v9_14_decision", {}).get("decision")
    if current_features_weak and priority_sources:
        decision = "data_extension_first_before_more_labels"
        confidence = "medium_high"
        recommendation = "V9.15 Data Extension Readiness / Derivatives Feature Candidate."
        justification = "Les features OHLCV+aggTrades restent peu separables et le repo contient des sources derivatives partielles non utilisees par V9, notamment funding/open interest."
    elif current_features_weak:
        decision = "feature_first_before_more_labels"
        confidence = "medium"
        recommendation = "V9.15 Feature Separability / Feature Refinement Candidate."
        justification = "Les features actuelles sont faibles et aucune source complementaire exploitable n'est prouvee localement."
    else:
        decision = "inconclusive_need_manual_review"
        confidence = "low"
        recommendation = "Revue manuelle avant nouvelle branche."
        justification = "Les diagnostics ne suffisent pas a corriger la decision de branche avec confiance."
    return {
        "previous_decision": previous,
        "decision": decision,
        "confidence": confidence,
        "justification": justification,
        "priority_sources_considered": priority_sources,
        "next_recommendation": recommendation,
        "explicit_no_backtest_statement": "Aucun backtest n'est recommande ou execute par V9.14.1.",
        "explicit_no_trading_statement": "V9.14.1 n'autorise aucun trading, paper live, ordre, strategie ou signal actionnable.",
    }


def build_data_extension_recommendation_v9_14_1(inventory: list[dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    priority_1 = [item for item in inventory if item["recommended_priority"] == "priority_1_candidate"]
    priority_2 = [item for item in inventory if item["recommended_priority"] == "priority_2_candidate"]
    return {
        "recommended_decision": decision["decision"],
        "primary_sources": [item["source_name"] for item in priority_1],
        "secondary_sources": [item["source_name"] for item in priority_2],
        "not_available_or_unknown": [item["source_name"] for item in inventory if item["recommended_priority"] == "missing_or_unknown"],
        "next_version_candidate": decision["next_recommendation"],
        "no_backtest": True,
        "no_walk_forward": True,
        "notes": "La prochaine version doit rester readiness/audit data-extension, sans integration trading.",
    }


def build_manifest_v9_14_1(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "correction_scope": CORRECTION_SCOPE,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "previous_v9_14_decision": report["previous_v9_14_decision"],
        "corrected_decision": report["corrected_decision"],
        "confidence": report["confidence"],
        "data_source_inventory_count": len(report["data_source_inventory"]),
        "hypotheses_count": len(report["hypothesis_ranking"]),
        "inputs_used": report["inputs_used"],
        "findings": report["findings"],
        "safety": report["safety"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_14_1(report: dict[str, Any]) -> str:
    lines = [
        "# V9.14.1 - Data Source Inventory & Branch Decision Correction",
        "",
        "## Resume executif",
        f"- Version source : `{report['source_version']}`.",
        f"- Correction : `{report['correction_scope']}`.",
        f"- Ancienne decision V9.14 : `{report['previous_v9_14_decision']}`.",
        f"- Decision corrigee V9.14.1 : `{report['corrected_decision']}`.",
        f"- Justification : {report['decision_rationale']['justification']}",
        "- V9.14.1 ne relance aucun ML lourd, aucun walk-forward et aucun backtest.",
        "- Aucun trading, aucun paper live, aucun ordre, aucune strategie, aucun signal actionnable.",
        "",
        "## Inventaire data-extension",
    ]
    for item in report["data_source_inventory"]:
        lines.append(
            f"- `{item['source_name']}` : present=`{item['present_in_repo']}`, "
            f"utilise_V9=`{item['used_in_validated_v9_chain']}`, priorite=`{item['recommended_priority']}`. "
            f"{item['notes']}"
        )
    lines.extend(["", "## Hypotheses H1-H11"])
    for item in report["hypothesis_ranking"]:
        lines.append(f"- `{item['id']}` {item['hypothesis']} : `{item['status']}` ({item['confidence']}). {item['consequence_next_version']}")
    lines.extend(
        [
            "",
            "## Recommandation suivante",
            f"- {report['next_recommendation']}",
            "- La prochaine version doit auditer les sources derivatives/microstructure disponibles avant de redessiner encore les labels.",
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


def update_state_surfaces_v9_14_1(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "correction_scope": CORRECTION_SCOPE,
        "direction": "data_source_inventory_and_branch_decision_correction",
        "previous_v9_14_decision": report["previous_v9_14_decision"],
        "corrected_decision": report["corrected_decision"],
        "recommended_next_step": report["next_recommendation"],
        **SAFETY_FLAGS,
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    summary = (
        "# Synthese courante - V9.14.1\n\n"
        "- Derniere version validee : `V9.13`.\n"
        "- Candidate : `V9.14.1`.\n"
        "- Statut : `pending_external_audit`.\n"
        "- Source : `V9.14`.\n"
        "- Correction : inventaire data-extension et decision de branche.\n"
        f"- Ancienne decision V9.14 : `{report['previous_v9_14_decision']}`.\n"
        f"- Decision corrigee V9.14.1 : `{report['corrected_decision']}`.\n"
        f"- Recommandation : {report['next_recommendation']}\n"
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
        "- Candidate : V9.14.1, correction inventaire data-extension et decision de branche de V9.14.\n"
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
