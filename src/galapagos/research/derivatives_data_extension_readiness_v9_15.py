from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


VERSION = "V9.15"
LAST_VALIDATED_VERSION = "V9.14.1"
SOURCE_VERSION = "V9.14.1"
DIRECTION = "derivatives_data_extension_readiness"
REPORT_JSON_PATH = Path("reports/research_decisions/derivatives_data_extension_readiness_v9_15.json")
REPORT_MD_PATH = Path("reports/research_decisions/derivatives_data_extension_readiness_v9_15.md")
MANIFEST_PATH = Path("reports/manifests/derivatives_data_extension_readiness_v9_15_manifest.json")
DOC_PATH = Path("docs/derivatives_data_extension_readiness_v9_15.md")

V9_WINDOW = {
    "window_start": "2023-03-25T00:00:00Z",
    "window_end": "2024-03-24T23:59:59Z",
    "window_label": "2023-03-25_2024-03-24",
    "total_days": 366,
}
V9_TIMEFRAMES = ["1m", "5m", "15m", "1h"]
DERIVATIVES_REVIEW_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h"]

ALLOWED_DECISIONS = {
    "derivatives_readiness_ready_for_feature_candidate",
    "derivatives_readiness_partial_requires_alignment",
    "derivatives_readiness_not_compatible_with_v9_window",
    "derivatives_readiness_not_ready_missing_coverage",
    "derivatives_readiness_not_ready_quality_failed",
    "data_extension_should_start_with_derivatives_window_extension",
    "data_extension_should_start_with_new_collection_plan",
    "stop_data_extension_branch",
}

INPUT_PATHS = {
    "v9_14_1_decision": Path("reports/research_decisions/feature_label_separability_v9_14_1.json"),
    "v9_14_1_manifest": Path("reports/manifests/feature_label_separability_v9_14_1_manifest.json"),
    "derivatives_coverage_v1_14": Path("reports/research/derivatives_coverage_v1_14.json"),
    "derivatives_data_quality_v1_14": Path("reports/research/derivatives_data_quality_v1_14.json"),
    "derivatives_features_v1_14": Path("reports/research/derivatives_features_v1_14.json"),
    "fred_macro_readiness_v1_12_2": Path("reports/research/fred_macro_readiness_v1_12_2.json"),
    "latest_metrics": Path("reports/current/latest_metrics.json"),
    "latest_summary": Path("reports/current/latest_summary.md"),
    "project_state": Path("reports/PROJECT_STATE.json"),
    "project_state_md": Path("reports/PROJECT_STATE.md"),
}

SOURCE_PATHS = {
    "silver_derivatives": Path("data/silver/derivatives"),
    "gold_derivatives_features": Path("data/gold/derivatives_features/BTCUSDT/4h"),
    "derivatives_code": Path("src/galapagos/data/derivatives"),
    "build_derivatives_features_script": Path("scripts/build_derivatives_features.py"),
    "fetch_derivatives_history_script": Path("scripts/fetch_derivatives_history.py"),
    "audit_derivatives_coverage_script": Path("scripts/audit_derivatives_coverage.py"),
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
    "network_used": False,
    "no_new_data_download": True,
    "no_sidecars": True,
    "no_zip_fingerprints": True,
}

SAFETY = {
    "public_read_only": True,
    "authentication_used": False,
    "api_key_used": False,
    "private_endpoint_used": False,
    "network_used": False,
    "new_data_downloaded": False,
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


def run_derivatives_data_extension_readiness_v9_15(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_derivatives_data_extension_readiness_report_v9_15(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_15(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DOC_PATH, markdown)
    manifest = build_manifest_v9_15(report)
    _write_json(root / MANIFEST_PATH, manifest)
    update_state_surfaces_v9_15(root, report)
    return report


def build_derivatives_data_extension_readiness_report_v9_15(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    payloads = {name: item["payload"] for name, item in inputs.items()}
    source_inventory = inspect_local_derivatives_sources_v9_15(root)
    coverage = payloads.get("derivatives_coverage_v1_14", {})
    data_quality = payloads.get("derivatives_data_quality_v1_14", {})
    feature_report = payloads.get("derivatives_features_v1_14", {})
    funding = analyze_source_readiness_v9_15("funding_rates", coverage, data_quality, feature_report)
    open_interest = analyze_source_readiness_v9_15("open_interest", coverage, data_quality, feature_report)
    compatibility = analyze_v9_compatibility_v9_15(funding, open_interest, source_inventory)
    feature_candidate = decide_feature_candidate_v9_15(funding, open_interest, compatibility)
    decision = decide_readiness_v9_15(funding, open_interest, compatibility, feature_candidate)
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "inputs_used": {name: {"path": item["path"], "available": item["available"]} for name, item in inputs.items()},
        "v9_14_1_context": summarize_v9_14_1_context_v9_15(payloads.get("v9_14_1_decision", {})),
        "v9_window": dict(V9_WINDOW),
        "v9_timeframes": list(V9_TIMEFRAMES),
        "local_derivatives_source_inventory": source_inventory,
        "funding_readiness": funding,
        "open_interest_readiness": open_interest,
        "v9_chain_compatibility": compatibility,
        "feature_candidate": feature_candidate,
        "v9_15_decision": decision,
        "next_recommendation": decision["next_recommendation"],
        "features_candidate_created": feature_candidate["created"],
        "feature_candidate_outputs": feature_candidate["outputs"],
        "findings": dict(FINDINGS),
        "safety": dict(SAFETY),
        "safety_flags": dict(SAFETY_FLAGS),
        "warnings": [
            "Les rapports derivatives V1.14 indiquent une couverture partielle et majoritairement posterieure a la fenetre V9.",
            "V9.15 n'appelle aucune API et ne telecharge aucune nouvelle donnee; les constats sont limites aux artefacts locaux existants.",
        ],
        "limitations": [
            "V9.15 est un diagnostic readiness derivatives et ne cree aucun dataset supervise, aucun ML, aucun walk-forward, aucun backtest et aucun signal actionnable.",
            "Aucune feature candidate full n'est produite si la couverture funding/open interest ne recouvre pas la fenetre V9.",
            "Les rapports V1.14 mentionnent des collectes historiques precedentes; V9.15 ne les relance pas.",
        ],
    }


def summarize_v9_14_1_context_v9_15(v9_14_1: dict[str, Any]) -> dict[str, Any]:
    return {
        "corrected_decision": v9_14_1.get("corrected_decision"),
        "primary_sources": v9_14_1.get("data_extension_recommendation", {}).get("primary_sources", []),
        "source_decision_used": v9_14_1.get("version") == "V9.14.1",
    }


def inspect_local_derivatives_sources_v9_15(root: Path) -> dict[str, Any]:
    source_paths: dict[str, Any] = {}
    for name, path in SOURCE_PATHS.items():
        full = root / path
        files_count = 0
        if full.is_file():
            files_count = 1
        elif full.is_dir():
            files_count = sum(1 for item in full.rglob("*") if item.is_file())
        source_paths[name] = {
            "path": path.as_posix(),
            "exists": full.exists(),
            "is_dir": full.is_dir(),
            "files_count": files_count,
        }
    report_paths = sorted(path.as_posix() for path in (root / "reports/research").glob("*derivatives*.json"))
    raw_futures_dir = root / "data/raw/binance_public/futures_um/BTCUSDT/4h"
    raw_futures_zip_count = sum(1 for item in raw_futures_dir.glob("*.zip")) if raw_futures_dir.exists() else 0
    return {
        "source_paths": source_paths,
        "derivatives_report_count": len(report_paths),
        "derivatives_report_paths": report_paths,
        "raw_binance_futures_4h_zip_count": raw_futures_zip_count,
        "raw_binance_futures_4h_path": "data/raw/binance_public/futures_um/BTCUSDT/4h" if raw_futures_dir.exists() else None,
        "network_used_in_v9_15": False,
        "new_data_downloaded_in_v9_15": False,
    }


def analyze_source_readiness_v9_15(source_name: str, coverage: dict[str, Any], data_quality: dict[str, Any], feature_report: dict[str, Any]) -> dict[str, Any]:
    metric_name = "funding_rate" if source_name == "funding_rates" else "open_interest"
    checks = [item for item in coverage.get("checks", []) if item.get("metric_name") == metric_name]
    exchanges = sorted({item.get("source") for item in checks if item.get("source")})
    available_checks = [item for item in checks if item.get("status") == "available" and int(item.get("rows") or 0) > 0]
    start_values = [item.get("start_timestamp") for item in available_checks if item.get("start_timestamp")]
    end_values = [item.get("end_timestamp") for item in available_checks if item.get("end_timestamp")]
    overlap = [overlap_with_v9_window_v9_15(item.get("start_timestamp"), item.get("end_timestamp")) for item in available_checks]
    metric_missing = _source_missing_rates(source_name, data_quality)
    available_timestamp_evidence = "available_timestamp" in feature_report.get("columns", []) or "available_timestamp" in feature_report.get("output_columns", [])
    compatible_with_v9 = any(item["overlaps_v9_window"] for item in overlap)
    quality = "partial" if available_checks else "not_available"
    decision = "partial_requires_alignment" if compatible_with_v9 and available_checks else "not_ready_missing_coverage"
    return {
        "source_name": source_name,
        "metric_name": metric_name,
        "present_local": bool(checks),
        "evidence_paths": [
            "reports/research/derivatives_coverage_v1_14.json",
            "reports/research/derivatives_data_quality_v1_14.json",
            "reports/research/derivatives_features_v1_14.json",
        ],
        "exchanges_available": exchanges,
        "coverage_checks": [
            {
                "exchange": item.get("source"),
                "status": item.get("status"),
                "rows": int(item.get("rows") or 0),
                "coverage_start": item.get("start_timestamp"),
                "coverage_end": item.get("end_timestamp"),
                "missing_rate": item.get("missing_rate"),
                "freshness": item.get("freshness"),
                **overlap_with_v9_window_v9_15(item.get("start_timestamp"), item.get("end_timestamp")),
            }
            for item in checks
        ],
        "combined_coverage_start": min(start_values) if start_values else None,
        "combined_coverage_end": max(end_values) if end_values else None,
        "total_rows_available": sum(int(item.get("rows") or 0) for item in available_checks),
        "frequency": "8h native for funding where available; open interest source frequency varies and local feature report is 4h aligned.",
        "missing_rates": metric_missing,
        "freshness": sorted({item.get("freshness") for item in checks if item.get("freshness")}),
        "compatible_with_v9_window": compatible_with_v9,
        "compatible_timeframes": compatibility_by_timeframe_v9_15(compatible_with_v9, source_name),
        "causality": {
            "available_timestamp_or_equivalent_present": available_timestamp_evidence,
            "rule_required": "Use available_timestamp <= feature decision timestamp; never use metric timestamp alone when publication lag is ambiguous.",
            "causality_feasibility": "good" if available_timestamp_evidence else "medium",
        },
        "leakage_risk": "low_if_available_timestamp_enforced" if available_timestamp_evidence else "medium",
        "survivorship_or_revision_risk": "medium",
        "known_quality": quality,
        "readiness_decision": decision,
        "notes": "Coverage does not overlap the V9 window." if not compatible_with_v9 else "Coverage overlaps V9 but still requires strict as-of alignment.",
    }


def compatibility_by_timeframe_v9_15(compatible_with_v9: bool, source_name: str) -> dict[str, Any]:
    return {
        timeframe: {
            "compatible": False if not compatible_with_v9 else timeframe == "4h",
            "reason": (
                "No overlap with V9 window, so no timeframe can be integrated into current V9 datasets."
                if not compatible_with_v9
                else "4h is the native local derivative feature alignment; lower V9 timeframes would require causal as-of joins."
            ),
        }
        for timeframe in DERIVATIVES_REVIEW_TIMEFRAMES
    } | {"source_name": source_name}


def overlap_with_v9_window_v9_15(start: str | None, end: str | None) -> dict[str, Any]:
    if not start or not end:
        return {"overlaps_v9_window": False, "overlap_start": None, "overlap_end": None}
    start_dt = _parse_timestamp(start)
    end_dt = _parse_timestamp(end)
    v9_start = _parse_timestamp(V9_WINDOW["window_start"])
    v9_end = _parse_timestamp(V9_WINDOW["window_end"])
    if start_dt is None or end_dt is None:
        return {"overlaps_v9_window": False, "overlap_start": None, "overlap_end": None}
    overlap_start = max(start_dt, v9_start)
    overlap_end = min(end_dt, v9_end)
    overlaps = overlap_start <= overlap_end
    return {
        "overlaps_v9_window": overlaps,
        "overlap_start": overlap_start.isoformat().replace("+00:00", "Z") if overlaps else None,
        "overlap_end": overlap_end.isoformat().replace("+00:00", "Z") if overlaps else None,
    }


def _source_missing_rates(source_name: str, data_quality: dict[str, Any]) -> dict[str, Any]:
    missing = data_quality.get("missing_rates", {})
    if source_name == "funding_rates":
        keys = [key for key in missing if "funding" in key]
    else:
        keys = [key for key in missing if "open_interest" in key]
    return {key: missing[key] for key in sorted(keys)}


def analyze_v9_compatibility_v9_15(funding: dict[str, Any], open_interest: dict[str, Any], source_inventory: dict[str, Any]) -> dict[str, Any]:
    no_overlap = not funding["compatible_with_v9_window"] and not open_interest["compatible_with_v9_window"]
    return {
        "v9_window": dict(V9_WINDOW),
        "v9_timeframes": list(V9_TIMEFRAMES),
        "derivatives_native_or_reported_timeframe": "4h",
        "funding_overlaps_v9": funding["compatible_with_v9_window"],
        "open_interest_overlaps_v9": open_interest["compatible_with_v9_window"],
        "compatible_with_current_v9_chain": not no_overlap,
        "alignment_possible_now": not no_overlap,
        "alignment_requirements": [
            "Use as-of joins with available_timestamp <= decision_ts.",
            "Do not forward-fill across publication gaps without a maximum staleness rule.",
            "Keep derivatives features outside labels and outside any target columns.",
            "Audit sparse and quasi-constant columns after alignment.",
        ],
        "forward_fill_policy": "not_allowed_for_current_v9_window_because_coverage_does_not_overlap" if no_overlap else "allowed_only_with_explicit_max_staleness_and_available_timestamp_guard",
        "publication_latency_requirement": "available_timestamp must be carried through every future feature row.",
        "expected_post_alignment_coverage": "0 for current V9 window when relying on V1.14 funding/OI reports.",
        "sparse_or_constant_feature_risk": "high_for_current_v9_window",
        "impact_on_existing_v9_datasets": "Do not mutate existing V9 datasets; a future compatible derivatives window must be built separately.",
        "local_source_inventory_summary": {
            "silver_derivatives_files": source_inventory["source_paths"]["silver_derivatives"]["files_count"],
            "gold_derivatives_feature_files": source_inventory["source_paths"]["gold_derivatives_features"]["files_count"],
            "derivatives_reports": source_inventory["derivatives_report_count"],
            "raw_futures_4h_zips": source_inventory["raw_binance_futures_4h_zip_count"],
        },
    }


def decide_feature_candidate_v9_15(funding: dict[str, Any], open_interest: dict[str, Any], compatibility: dict[str, Any]) -> dict[str, Any]:
    if compatibility["compatible_with_current_v9_chain"]:
        return {
            "created": False,
            "reason": "Coverage overlap would still require a separate feature-store implementation; V9.15 is readiness-only by design.",
            "candidate_columns_considered": candidate_columns_v9_15(),
            "outputs": [],
        }
    return {
        "created": False,
        "reason": "No feature candidate was created because funding/OI coverage in local V1.14 reports does not overlap the V9 window.",
        "candidate_columns_considered": candidate_columns_v9_15(),
        "outputs": [],
    }


def candidate_columns_v9_15() -> list[str]:
    return [
        "funding_rate",
        "funding_rate_change",
        "funding_rate_zscore",
        "open_interest",
        "open_interest_change",
        "open_interest_zscore",
        "funding_open_interest_interaction",
        "derivatives_missingness_flags",
    ]


def decide_readiness_v9_15(
    funding: dict[str, Any],
    open_interest: dict[str, Any],
    compatibility: dict[str, Any],
    feature_candidate: dict[str, Any],
) -> dict[str, Any]:
    if not compatibility["compatible_with_current_v9_chain"]:
        decision = "derivatives_readiness_not_compatible_with_v9_window"
        recommendation = "V9.16 - Derivatives Window Extension Diagnostic."
        confidence = "high"
        justification = "Funding and open interest are present only partially in local reports and do not overlap the validated V9 window 2023-03-25 to 2024-03-24."
    elif funding["readiness_decision"] == "partial_requires_alignment" or open_interest["readiness_decision"] == "partial_requires_alignment":
        decision = "derivatives_readiness_partial_requires_alignment"
        recommendation = "V9.16 - Derivatives Data Alignment Correction."
        confidence = "medium"
        justification = "Local derivatives sources overlap enough for alignment work, but require strict available_timestamp guards."
    elif feature_candidate["created"]:
        decision = "derivatives_readiness_ready_for_feature_candidate"
        recommendation = "V9.16 - Derivatives Feature Store Candidate."
        confidence = "medium"
        justification = "A strictly causal candidate feature surface was produced and passed readiness checks."
    else:
        decision = "derivatives_readiness_not_ready_missing_coverage"
        recommendation = "V9.16 - Derivatives Window Extension Diagnostic."
        confidence = "medium"
        justification = "Local derivatives sources are insufficient for a feature candidate."
    return {
        "decision": decision,
        "confidence": confidence,
        "justification": justification,
        "next_recommendation": recommendation,
        "no_backtest": True,
        "no_walk_forward": True,
        "feature_candidate_created": feature_candidate["created"],
    }


def build_manifest_v9_15(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "v9_15_decision": report["v9_15_decision"],
        "features_candidate_created": report["features_candidate_created"],
        "funding_readiness_decision": report["funding_readiness"]["readiness_decision"],
        "open_interest_readiness_decision": report["open_interest_readiness"]["readiness_decision"],
        "compatible_with_current_v9_chain": report["v9_chain_compatibility"]["compatible_with_current_v9_chain"],
        "inputs_used": report["inputs_used"],
        "findings": report["findings"],
        "safety": report["safety"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_15(report: dict[str, Any]) -> str:
    funding = report["funding_readiness"]
    oi = report["open_interest_readiness"]
    decision = report["v9_15_decision"]
    lines = [
        "# V9.15 - Data Extension Readiness / Derivatives Feature Candidate",
        "",
        "## Resume executif",
        f"- Decision V9.15 : `{decision['decision']}`.",
        f"- Justification : {decision['justification']}",
        f"- Recommandation suivante : {decision['next_recommendation']}",
        f"- Feature candidate derivatives creee : `{report['features_candidate_created']}`.",
        "- V9.15 est un diagnostic readiness offline; aucune donnee nouvelle n'est telechargee.",
        "- Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucun walk-forward, aucune strategie, aucun signal actionnable.",
        "",
        "## Donnees derivatives locales",
        f"- Rapports derivatives detectes : `{report['local_derivatives_source_inventory']['derivatives_report_count']}`.",
        f"- Zips futures 4h locaux : `{report['local_derivatives_source_inventory']['raw_binance_futures_4h_zip_count']}`.",
        f"- Fichiers silver derivatives : `{report['local_derivatives_source_inventory']['source_paths']['silver_derivatives']['files_count']}`.",
        f"- Fichiers gold derivatives features : `{report['local_derivatives_source_inventory']['source_paths']['gold_derivatives_features']['files_count']}`.",
        "",
        "## Funding readiness",
        f"- Exchanges : `{funding['exchanges_available']}`.",
        f"- Lignes disponibles : `{funding['total_rows_available']}`.",
        f"- Couverture combinee : `{funding['combined_coverage_start']}` -> `{funding['combined_coverage_end']}`.",
        f"- Compatible fenetre V9 : `{funding['compatible_with_v9_window']}`.",
        f"- Decision readiness : `{funding['readiness_decision']}`.",
        "",
        "## Open interest readiness",
        f"- Exchanges : `{oi['exchanges_available']}`.",
        f"- Lignes disponibles : `{oi['total_rows_available']}`.",
        f"- Couverture combinee : `{oi['combined_coverage_start']}` -> `{oi['combined_coverage_end']}`.",
        f"- Compatible fenetre V9 : `{oi['compatible_with_v9_window']}`.",
        f"- Decision readiness : `{oi['readiness_decision']}`.",
        "",
        "## Compatibilite chaine V9",
        f"- Fenetre V9 : `{report['v9_window']['window_label']}`.",
        f"- Timeframes V9 : `{report['v9_timeframes']}`.",
        f"- Timeframe derivatives local rapporte : `{report['v9_chain_compatibility']['derivatives_native_or_reported_timeframe']}`.",
        f"- Compatible chaine V9 actuelle : `{report['v9_chain_compatibility']['compatible_with_current_v9_chain']}`.",
        f"- Couverture attendue apres alignement : {report['v9_chain_compatibility']['expected_post_alignment_coverage']}",
        "",
        "## Feature candidate",
        f"- Creee : `{report['feature_candidate']['created']}`.",
        f"- Raison : {report['feature_candidate']['reason']}",
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
        "- Aucun reseau et aucun telechargement de nouvelles donnees.",
        "- Aucun sidecar et aucune empreinte ZIP.",
    ]
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_15(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_15_decision": report["v9_15_decision"]["decision"],
        "recommended_next_step": report["next_recommendation"],
        "features_candidate_created": report["features_candidate_created"],
        "network_used": False,
        "no_new_data_download": True,
        **SAFETY_FLAGS,
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    for stale_key in ["recommended_next_version", "recommended_next_action"]:
        state.pop(stale_key, None)
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    summary = (
        "# Synthese courante - V9.15\n\n"
        "- Derniere version validee : `V9.14.1`.\n"
        "- Candidate : `V9.15`.\n"
        "- Statut : `pending_external_audit`.\n"
        "- Direction : readiness data-extension derivatives.\n"
        f"- Decision V9.15 : `{report['v9_15_decision']['decision']}`.\n"
        f"- Recommandation : {report['next_recommendation']}\n"
        f"- Feature candidate derivatives creee : `{report['features_candidate_created']}`.\n"
        "- Aucun trading, paper live, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun reseau, aucun telechargement de nouvelles donnees, aucun sidecar et aucune empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", summary)
    _write_text(root / "reports/current/latest_summary.md", summary)
    _write_text(root / "reports/current/latest_metrics.md", summary)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V9.14.1.\n"
        "- Candidate : V9.15, readiness data-extension derivatives.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun reseau, aucun telechargement de nouvelles donnees, aucun sidecar et aucune empreinte ZIP.\n",
    )


def _parse_timestamp(value: str) -> datetime | None:
    try:
        cleaned = value.replace("Z", "+00:00")
        if " " in cleaned and "T" not in cleaned:
            cleaned = cleaned.replace(" ", "T")
        return datetime.fromisoformat(cleaned).astimezone(UTC)
    except ValueError:
        return None


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
