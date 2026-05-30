from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_39_datacard import build_dataset_datacard_v9_39
from galapagos.datasets.ohlcv_aggtrades_5y_dataset_v9_39_schemas import (
    ALLOWED_DECISIONS,
    DATACARD_MD_PATH,
    DIRECTION,
    DOC_PATH,
    EXPECTED_FEATURE_ROWS,
    FEATURE_COLUMNS_COUNT,
    FINDINGS,
    INPUT_PATHS,
    LABEL_CANDIDATE_REPORTS,
    LAST_VALIDATED_VERSION,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY_FLAGS,
    SOURCE_VERSION,
    SPLIT_POLICY,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    TIMEFRAMES,
    TOTAL_DAYS,
    VERSION,
)


def run_ohlcv_aggtrades_5y_dataset_v9_39(root: Path = Path(".")) -> dict[str, Any]:
    root = root.resolve()
    report = build_dataset_readiness_report_v9_39(root)
    _write_json(root / REPORT_JSON_PATH, report)
    markdown = build_markdown_v9_39(report)
    _write_text(root / REPORT_MD_PATH, markdown)
    _write_text(root / DATACARD_MD_PATH, build_dataset_datacard_v9_39(report))
    _write_text(root / DOC_PATH, markdown)
    _write_json(root / MANIFEST_PATH, build_manifest_v9_39(report))
    update_state_surfaces_v9_39(root, report)
    return report


def build_dataset_readiness_report_v9_39(root: Path) -> dict[str, Any]:
    started = time.monotonic()
    inputs = {name: _load_input(root, path) for name, path in INPUT_PATHS.items()}
    feature_readiness = assess_feature_store_readiness_v9_39(inputs)
    label_readiness = assess_label_readiness_v9_39(root)
    compatible_labels = [item for item in label_readiness["candidates"] if item["compatible_with_5y_window"] and item["label_design_status"] == "compatible"]
    dataset_created = False
    target_name = compatible_labels[0]["target_name"] if compatible_labels else None
    decision = decide_v9_39(feature_readiness, label_readiness, dataset_created)
    row_counts = {timeframe: 0 for timeframe in TIMEFRAMES}
    label_distribution: dict[str, Any] = {}
    split_distribution: dict[str, Any] = {}
    leakage_guard = {
        "status": "NOT_APPLICABLE_DATASET_NOT_CREATED",
        "feature_available_ts_lte_decision_ts": feature_readiness["feature_available_ts_lte_decision_ts"],
        "label_available_ts_gt_decision_ts": None,
        "no_future_leak": True,
        "reason": "dataset_blocked_before_join because no compatible 5Y labels were available",
    }
    forbidden_scan = {
        "status": "PASS",
        "forbidden_columns": [],
        "scope": "planned_schema_and_report_only",
    }
    quality_status = "BLOCKED" if decision == "ohlcv_aggtrades_5y_dataset_blocked_by_missing_labels" else "FAIL"
    coverage_status = "feature_store_ready_labels_missing" if feature_readiness["ready"] else "feature_store_not_ready"
    warnings = build_warnings_v9_39(label_readiness)
    limitations = [
        "V9.39 ne cree pas de dataset Parquet lorsque les labels 5Y compatibles manquent.",
        "Les labels historiques V9.6/V9.12/V9.13 peuvent servir a des diagnostics, mais ne couvrent pas la fenetre 5Y complete.",
        "Aucun ML, walk-forward, backtest, strategie, signal ou ordre n'est execute.",
    ]
    report = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": "PASS",
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "decision": decision,
        "target_window": {"start": TARGET_WINDOW_START, "end": TARGET_WINDOW_END, "days_expected": TOTAL_DAYS},
        "timeframes": list(TIMEFRAMES),
        "feature_store_source": {
            "source_feature_store_version": "V9.37",
            "source_feature_validation_version": SOURCE_VERSION,
            "feature_columns_count": FEATURE_COLUMNS_COUNT,
            "expected_rows": EXPECTED_FEATURE_ROWS,
            "readiness": feature_readiness,
        },
        "label_readiness": label_readiness,
        "dataset_design": {
            "dataset_schema_version": "not_materialized_missing_5y_labels",
            "target_name": target_name,
            "split_policy": SPLIT_POLICY,
            "dataset_creation_policy": "create_only_when_5y_compatible_labels_exist",
        },
        "dataset_created": dataset_created,
        "dataset_paths": {},
        "target_name": target_name,
        "row_counts": row_counts,
        "label_distribution": label_distribution,
        "split_distribution": split_distribution,
        "monthly_distribution": {},
        "null_summary": {},
        "leakage_guard": leakage_guard,
        "forbidden_column_scan": forbidden_scan,
        "quality_status": quality_status,
        "coverage_status": coverage_status,
        "warnings": warnings,
        "limitations": limitations,
        "next_recommendation": next_recommendation_v9_39(decision),
        "runtime_seconds": round(time.monotonic() - started, 3),
        "labels_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        "ingestion_executed": False,
        "findings": dict(FINDINGS),
        "safety_flags": dict(SAFETY_FLAGS),
    }
    if report["decision"] not in ALLOWED_DECISIONS:
        raise RuntimeError(f"invalid V9.39 decision: {report['decision']}")
    return report


def assess_feature_store_readiness_v9_39(inputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    report = inputs["v9_38_validation"].get("payload", {})
    errors: list[str] = []
    if not inputs["v9_38_validation"].get("available"):
        errors.append("missing V9.38 feature store validation report")
    if report.get("decision") != "ohlcv_aggtrades_5y_feature_store_validated_with_non_blocking_warnings":
        errors.append("V9.38 decision is not the expected validated-with-warnings decision")
    if report.get("quality_status") != "PASS":
        errors.append("V9.38 quality_status is not PASS")
    if report.get("coverage_status") != "target_5y_feature_window_complete":
        errors.append("V9.38 coverage_status is not complete")
    if report.get("schema_status") != "PASS" or report.get("leakage_guard_status") != "PASS":
        errors.append("V9.38 schema or leakage guard is not PASS")
    rows = report.get("actual_rows", {})
    if rows != EXPECTED_FEATURE_ROWS:
        errors.append(f"V9.38 row_counts mismatch: {rows}")
    return {
        "ready": not errors,
        "errors": errors,
        "feature_available_ts_lte_decision_ts": report.get("leakage_guard", {}).get("feature_available_ts_lte_decision_ts", True),
        "coverage_status": report.get("coverage_status"),
        "quality_status": report.get("quality_status"),
        "schema_status": report.get("schema_status"),
        "leakage_guard_status": report.get("leakage_guard_status"),
        "row_counts": rows,
    }


def assess_label_readiness_v9_39(root: Path) -> dict[str, Any]:
    candidates = [assess_label_candidate_v9_39(root, name, path) for name, path in LABEL_CANDIDATE_REPORTS.items()]
    compatible = [item for item in candidates if item["compatible_with_5y_window"] and item["label_design_status"] == "compatible"]
    return {
        "status": "READY" if compatible else "MISSING_5Y_COMPATIBLE_LABELS",
        "compatible_label_count": len(compatible),
        "candidates": candidates,
        "selected_label": compatible[0] if compatible else None,
        "missing_reason": None if compatible else "Aucun rapport ou parquet label local ne couvre strictement 2021-05-05 -> 2026-05-05 sur tous les timeframes requis.",
    }


def assess_label_candidate_v9_39(root: Path, name: str, path: Path) -> dict[str, Any]:
    full = root / path
    if not full.exists():
        return candidate_block_v9_39(name, path, available=False)
    payload = _read_json(full)
    window = extract_window_v9_39(payload)
    outputs = payload.get("outputs") or payload.get("input_labels") or {}
    quality = payload.get("quality", {})
    target_name = payload.get("target_name") or payload.get("recommended_candidate", {}).get("target_name")
    compatible_timeframes = sorted(set(outputs) & set(TIMEFRAMES)) if isinstance(outputs, dict) else []
    label_schema_known = bool(payload.get("label_schema_version") or payload.get("dataset_schema_version") or "label_columns" in payload or "dataset_columns" in payload)
    label_available_ts_present = has_column_hint_v9_39(payload, "label_available_ts")
    label_available_ts_gt_decision_ts = bool(payload.get("leakage_guard", {}).get("label_available_ts_gt_decision_ts", True))
    compatible_window = window["coverage_start"] is not None and window["coverage_end"] is not None and window["coverage_start"] <= TARGET_WINDOW_START and window["coverage_end"] >= TARGET_WINDOW_END
    compatible = compatible_window and set(compatible_timeframes) == set(TIMEFRAMES) and label_available_ts_present and label_available_ts_gt_decision_ts and label_schema_known
    warnings = historical_label_warnings_v9_39(name, payload, window)
    return candidate_block_v9_39(
        name,
        path,
        available=True,
        source_version=payload.get("version"),
        coverage_start=window["coverage_start"],
        coverage_end=window["coverage_end"],
        compatible_with_5y_window=compatible,
        compatible_timeframes=compatible_timeframes,
        label_available_ts_present=label_available_ts_present,
        label_available_ts_gt_decision_ts=label_available_ts_gt_decision_ts,
        label_schema_known=label_schema_known,
        target_name=target_name,
        label_design_status="compatible" if compatible else "not_5y_compatible",
        known_warnings=warnings,
        quality_status=payload.get("status") or ("PASS" if quality else None),
    )


def candidate_block_v9_39(
    name: str,
    path: Path,
    *,
    available: bool,
    source_version: str | None = None,
    coverage_start: str | None = None,
    coverage_end: str | None = None,
    compatible_with_5y_window: bool = False,
    compatible_timeframes: list[str] | None = None,
    label_available_ts_present: bool = False,
    label_available_ts_gt_decision_ts: bool = False,
    label_schema_known: bool = False,
    target_name: str | None = None,
    label_design_status: str = "missing",
    known_warnings: list[str] | None = None,
    quality_status: str | None = None,
) -> dict[str, Any]:
    return {
        "label_name": name,
        "path": path.as_posix(),
        "available": available,
        "source_version": source_version,
        "coverage_start": coverage_start,
        "coverage_end": coverage_end,
        "compatible_with_5y_window": compatible_with_5y_window,
        "compatible_timeframes": compatible_timeframes or [],
        "label_available_ts_present": label_available_ts_present,
        "label_available_ts_gt_decision_ts": label_available_ts_gt_decision_ts,
        "label_schema_known": label_schema_known,
        "target_name": target_name,
        "label_design_status": label_design_status,
        "known_warnings": known_warnings or [],
        "quality_status": quality_status,
    }


def extract_window_v9_39(payload: dict[str, Any]) -> dict[str, str | None]:
    window = payload.get("window", {}) if isinstance(payload.get("window"), dict) else {}
    start = window.get("window_start") or window.get("start") or payload.get("window_start")
    end = window.get("window_end") or window.get("end") or payload.get("window_end")
    if not start or not end:
        manifest = payload.get("input_dataset_manifest", {})
        start = start or manifest.get("window_start")
        end = end or manifest.get("window_end")
    if not start or not end:
        outputs = payload.get("outputs", {})
        if isinstance(outputs, dict):
            paths = [str(item.get("path", "")) for item in outputs.values() if isinstance(item, dict)]
            for raw in paths:
                maybe = parse_window_from_path_v9_39(raw)
                start = start or maybe[0]
                end = end or maybe[1]
    return {"coverage_start": start, "coverage_end": end}


def parse_window_from_path_v9_39(raw: str) -> tuple[str | None, str | None]:
    marker = "window="
    if marker not in raw:
        return None, None
    window = raw.split(marker, 1)[1].split("/", 1)[0]
    if "_" not in window:
        return None, None
    start, end = window.split("_", 1)
    return start or None, end or None


def has_column_hint_v9_39(payload: dict[str, Any], column: str) -> bool:
    for key in ["label_columns", "dataset_columns"]:
        values = payload.get(key)
        if isinstance(values, list) and column in values:
            return True
    quality = payload.get("quality", {})
    if isinstance(quality, dict):
        return column in json.dumps(quality)
    return False


def historical_label_warnings_v9_39(name: str, payload: dict[str, Any], window: dict[str, str | None]) -> list[str]:
    warnings: list[str] = []
    if window["coverage_start"] != TARGET_WINDOW_START or window["coverage_end"] != TARGET_WINDOW_END:
        warnings.append(f"window mismatch: {window['coverage_start']} -> {window['coverage_end']}")
    if name in {"volnorm_v9_6", "horizon_event_v9_12", "h4_dataset_v9_13", "v9_11_failure_analysis"}:
        warnings.append("label design historique avec faiblesses scientifiques documentees; diagnostic only, pas une strategie ni un signal")
    decision = payload.get("v9_12_decision", {}).get("decision") or payload.get("decision")
    if isinstance(decision, str) and "requires_review" in decision:
        warnings.append("design requires review")
    return warnings


def decide_v9_39(feature_readiness: dict[str, Any], label_readiness: dict[str, Any], dataset_created: bool) -> str:
    if not feature_readiness["ready"]:
        return "ohlcv_aggtrades_5y_dataset_blocked_by_feature_quality"
    if label_readiness["status"] != "READY":
        return "ohlcv_aggtrades_5y_dataset_blocked_by_missing_labels"
    if dataset_created:
        return "ohlcv_aggtrades_5y_dataset_created_with_warnings"
    return "ohlcv_aggtrades_5y_dataset_partial"


def next_recommendation_v9_39(decision: str) -> str:
    if decision in {"ohlcv_aggtrades_5y_dataset_created", "ohlcv_aggtrades_5y_dataset_created_with_warnings"}:
        return "V9.40 - OHLCV + AggTrades 5Y Dataset Validation"
    if decision == "ohlcv_aggtrades_5y_dataset_blocked_by_missing_labels":
        return "V9.40 - OHLCV + AggTrades 5Y Label Factory"
    return "V9.40 - Dataset Correction"


def build_warnings_v9_39(label_readiness: dict[str, Any]) -> list[str]:
    warnings = ["Dataset non cree car aucun label 5Y compatible n'est disponible localement."]
    for candidate in label_readiness["candidates"]:
        warnings.extend(f"{candidate['label_name']}: {warning}" for warning in candidate.get("known_warnings", []))
    return warnings


def build_manifest_v9_39(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "status": report["status"],
        "created_at_utc": _utc_now(),
        "direction": DIRECTION,
        "report_path": REPORT_JSON_PATH.as_posix(),
        "markdown_path": REPORT_MD_PATH.as_posix(),
        "datacard_path": DATACARD_MD_PATH.as_posix(),
        "decision": report["decision"],
        "next_recommendation": report["next_recommendation"],
        "dataset_created": report["dataset_created"],
        "target_name": report["target_name"],
        "row_counts": report["row_counts"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "label_readiness_status": report["label_readiness"]["status"],
        "findings": report["findings"],
        "safety_flags": report["safety_flags"],
    }


def build_markdown_v9_39(report: dict[str, Any]) -> str:
    lines = [
        "# V9.39 - OHLCV + AggTrades 5Y Dataset",
        "",
        "## Resume",
        f"- Decision V9.39 : `{report['decision']}`.",
        f"- Recommandation suivante : `{report['next_recommendation']}`.",
        f"- Dataset cree : `{report['dataset_created']}`.",
        f"- Label readiness : `{report['label_readiness']['status']}`.",
        f"- Target utilise : `{report['target_name']}`.",
        f"- Qualite : `{report['quality_status']}`.",
        f"- Couverture : `{report['coverage_status']}`.",
        "",
        "## Labels",
    ]
    for candidate in report["label_readiness"]["candidates"]:
        lines.append(
            f"- `{candidate['label_name']}` : disponible `{candidate['available']}`, fenetre `{candidate['coverage_start']} -> {candidate['coverage_end']}`, compatible 5Y `{candidate['compatible_with_5y_window']}`, target `{candidate['target_name']}`."
        )
    lines.extend(
        [
            "",
            "## Garde-fous",
            "- Aucun ML, walk-forward, backtest, strategie, signal actionnable ou ordre.",
            "- Aucun reseau, aucun telechargement, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.",
        ]
    )
    return "\n".join(lines) + "\n"


def update_state_surfaces_v9_39(root: Path, report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "direction": DIRECTION,
        "v9_39_decision": report["decision"],
        "recommended_next_step": report["next_recommendation"],
        "dataset_created": report["dataset_created"],
        "target_name": report["target_name"],
        "row_counts": report["row_counts"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "label_readiness_status": report["label_readiness"]["status"],
        "labels_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "network_used": False,
        "new_data_downloaded": False,
        **report["safety_flags"],
    }
    state_path = root / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(root / "reports/current/latest_metrics.json", metrics)
    text = (
        "# Synthese courante - V9.39\n\n"
        f"- Derniere version validee : `{LAST_VALIDATED_VERSION}`.\n"
        f"- Candidate : `{VERSION}`.\n"
        "- Statut : `pending_external_audit`.\n"
        f"- Direction : `{DIRECTION}`.\n"
        f"- Decision V9.39 : `{report['decision']}`.\n"
        f"- Dataset cree : `{report['dataset_created']}`.\n"
        f"- Label readiness : `{report['label_readiness']['status']}`.\n"
        f"- Recommandation : {report['next_recommendation']}.\n"
        "- Aucun ML, walk-forward, backtest, strategie, signal actionnable ou ordre.\n"
        "- Aucun reseau, telechargement, suppression destructive, sidecar ou empreinte ZIP.\n"
    )
    _write_text(root / "reports/PROJECT_STATE.md", text)
    _write_text(root / "reports/current/latest_summary.md", text)
    _write_text(root / "reports/current/latest_metrics.md", text)
    _write_text(
        root / "README.md",
        "# Projet Galapagos\n\n"
        f"- Derniere version validee : {LAST_VALIDATED_VERSION}.\n"
        f"- Candidate : {VERSION}, readiness dataset OHLCV + aggTrades 5Y.\n"
        f"- Decision : {report['decision']}.\n"
        "- Aucun trading, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n",
    )


def _load_input(root: Path, path: Path) -> dict[str, Any]:
    full = root / path
    if not full.exists():
        return {"path": path.as_posix(), "available": False, "payload": {}}
    payload: Any = _read_json(full) if path.suffix == ".json" else {"text": full.read_text(encoding="utf-8")}
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
