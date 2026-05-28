from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_completion_campaign_v9_25 import (
    ALLOWED_DECISIONS,
    BASE_SAFETY_FLAGS,
    DOC_PATH,
    FINDINGS,
    INTERNAL_BATCHES,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SILVER_COLUMNS_V9_18,
    SOURCE_VERSION,
    TARGET_WINDOW_END,
    TARGET_WINDOW_START,
    VERSION,
)


FORBIDDEN_CLAIMS = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "profitability confirmed",
]
FORBIDDEN_TERMS = ["sharpe", "drawdown", "equity curve", "profit factor", "pnl"]
FORBIDDEN_FILENAMES = {"Icon", "Icon\r", ".DS_Store", ".env"}
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pem", ".key", ".sha256.json", ".sha256.txt"}


def validate_aggtrades_post_v9_completion_campaign_v9_25(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    doc_path = root / DOC_PATH
    if not report_path.exists():
        return [f"missing V9.25 report: {REPORT_JSON_PATH}"]
    if not manifest_path.exists():
        errors.append(f"missing V9.25 manifest: {MANIFEST_PATH}")
    if not markdown_path.exists():
        errors.append(f"missing V9.25 markdown: {REPORT_MD_PATH}")
    if not doc_path.exists():
        errors.append(f"missing V9.25 doc: {DOC_PATH}")
    if errors:
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_25(report, root))
    errors.extend(validate_manifest_payload_v9_25(manifest, report))
    errors.extend(validate_markdown_v9_25(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_artifacts_v9_25(root))
    return errors


def validate_report_payload_v9_25(report: dict[str, Any], root: Path = Path(".")) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.25 report version mismatch")
    if report.get("source_version") != SOURCE_VERSION:
        errors.append("V9.25 source_version mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.25 status must be PASS")
    if report.get("direction") != "aggtrades_post_v9_remaining_window_completion_campaign":
        errors.append("V9.25 direction mismatch")
    decision = report.get("v9_25_decision", {})
    if decision.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.25 decision is not allowed")
    if "backtest" in str(decision.get("next_recommendation", "")).casefold():
        errors.append("V9.25 next recommendation must not be a backtest")
    errors.extend(validate_source_design_v9_25(report.get("source_public_target", {})))
    errors.extend(validate_campaign_summary_v9_25(report, root))
    errors.extend(validate_outputs_absent_v9_25(report))
    errors.extend(validate_safety_flags_v9_25(report))
    if report.get("findings") != FINDINGS:
        errors.append("V9.25 findings mismatch")
    if report.get("silver_schema_columns") != SILVER_COLUMNS_V9_18:
        errors.append("V9.25 silver schema columns mismatch")
    if not report.get("anti_leakage_plan", {}).get("rules"):
        errors.append("V9.25 anti-leakage plan is missing")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.25 report must not contain sidecar or ZIP hash fields")
    return errors


def validate_source_design_v9_25(source: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if source.get("host") != "data.binance.vision":
        errors.append("V9.25 source host must be data.binance.vision")
    if source.get("market_type") != "spot" or source.get("symbol") != "BTCUSDT":
        errors.append("V9.25 source must remain BTCUSDT spot")
    for key in ["account_required", "api_key_required", "private_endpoint_required", "exchange_auth_required", "websocket_live_required"]:
        if source.get(key) is not False:
            errors.append(f"V9.25 source must keep {key}=false")
    if not str(source.get("download_url_template", "")).startswith("https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/"):
        errors.append("V9.25 download template must use data.binance.vision public archive")
    return errors


def validate_campaign_summary_v9_25(report: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    summary = report.get("campaign_summary", {})
    if summary.get("target_window_start") != TARGET_WINDOW_START or summary.get("target_window_end") != TARGET_WINDOW_END:
        errors.append("V9.25 target window mismatch")
    if summary.get("batches_planned") != len(INTERNAL_BATCHES):
        errors.append("V9.25 planned batch count mismatch")
    if summary.get("days_requested_total", 0) > 514:
        errors.append("V9.25 must not request more than the 514 remaining days")
    if summary.get("days_attempted_total", 0) > 514:
        errors.append("V9.25 must not attempt more than the 514 remaining days")
    if summary.get("batches_executed", 0) > len(INTERNAL_BATCHES):
        errors.append("V9.25 executed too many internal batches")
    if summary.get("complete_collection_reached") is True:
        if summary.get("local_file_coverage_start") != TARGET_WINDOW_START or summary.get("local_file_coverage_end") != TARGET_WINDOW_END:
            errors.append("V9.25 complete collection must match local target coverage")
        if summary.get("reported_cumulative_coverage_start") != TARGET_WINDOW_START or summary.get("reported_cumulative_coverage_end") != TARGET_WINDOW_END:
            errors.append("V9.25 complete collection must match reported target coverage")
        if summary.get("batches_complete") != len(INTERNAL_BATCHES):
            errors.append("V9.25 complete collection requires all internal batches complete")
        if summary.get("days_complete_total") != 514:
            errors.append("V9.25 complete collection requires 514 newly validated days")
    if not isinstance(summary.get("aggregate_trade_id_gap_warnings"), list):
        errors.append("V9.25 aggregate_trade_id warnings must be a list")
    if not isinstance(summary.get("timestamp_gap_warnings"), list):
        errors.append("V9.25 timestamp warnings must be a list")
    if summary.get("days_failed_total", 0) < 0 or summary.get("days_quarantined_total", 0) < 0:
        errors.append("V9.25 day failure counters must be non-negative")
    batch_paths = report.get("batch_report_paths", [])
    if len(batch_paths) != len(INTERNAL_BATCHES):
        errors.append("V9.25 batch_report_paths must include every planned internal batch report")
    for raw_path in batch_paths:
        if not (root / raw_path).is_file():
            errors.append(f"V9.25 missing internal batch report: {raw_path}")
    return errors


def validate_outputs_absent_v9_25(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["features_created", "labels_created", "dataset_created", "ml_executed", "walk_forward_executed", "backtest_executed"]:
        if report.get(key) is not False:
            errors.append(f"V9.25 must keep {key}=false")
    return errors


def validate_safety_flags_v9_25(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    flags = report.get("safety_flags", {})
    for key, expected in BASE_SAFETY_FLAGS.items():
        if key in {"network_used", "new_data_downloaded", "ingestion_executed", "no_new_data_download", "no_ingestion_executed"}:
            continue
        if flags.get(key) is not expected:
            errors.append(f"V9.25 safety flag mismatch: {key}")
    if report.get("collection_executed") is True:
        if flags.get("network_scope") != "public_archive_read_only":
            errors.append("V9.25 collect must use public_archive_read_only")
        if flags.get("new_data_download_scope") != "public_historical_aggtrades_remaining_window_only":
            errors.append("V9.25 collect must limit downloads to the remaining aggTrades window")
        if flags.get("ingestion_scope") != "public_aggtrades_bronze_silver_completion_campaign_only":
            errors.append("V9.25 collect must limit ingestion to bronze/silver aggTrades campaign")
    for key in ["api_key_used", "private_endpoint_used", "exchange_auth_used", "websocket_live_used"]:
        if flags.get(key) is not False:
            errors.append(f"V9.25 must confirm {key}=false")
    return errors


def validate_manifest_payload_v9_25(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.25 manifest version mismatch")
    if manifest.get("status") != report.get("status"):
        errors.append("V9.25 manifest status mismatch")
    summary = report.get("campaign_summary", {})
    for key in [
        "batches_planned",
        "batches_executed",
        "batches_complete",
        "batches_failed",
        "days_requested_total",
        "days_attempted_total",
        "days_downloaded_total",
        "days_normalized_total",
        "days_complete_total",
        "days_failed_total",
        "days_quarantined_total",
        "total_rows_new",
        "total_rows_cumulative",
        "raw_bytes_new",
        "silver_bytes_new",
        "raw_bytes_cumulative",
        "silver_bytes_cumulative",
        "complete_collection_reached",
        "future_full_coverage_complete",
    ]:
        if manifest.get(key) != summary.get(key):
            errors.append(f"V9.25 manifest {key} mismatch")
    if manifest.get("decision") != report.get("decision"):
        errors.append("V9.25 manifest decision mismatch")
    if manifest.get("findings") != report.get("findings"):
        errors.append("V9.25 manifest findings mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.25 manifest safety flags mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.25 manifest must not contain sidecar or ZIP hash fields")
    return errors


def validate_markdown_v9_25(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            errors.append(f"V9.25 markdown contains forbidden claim: {claim}")
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.25 markdown contains forbidden metric term: {forbidden}")
    for phrase in [
        "aucun trading",
        "aucun paper live",
        "aucun ordre",
        "aucun backtest",
        "aucun walk-forward",
        "aucune strategie",
        "aucun signal actionnable",
        "aucun modele persistant",
        "aucune api privee",
        "aucune cle api",
        "aucun client exchange authentifie",
        "aucun websocket live",
        "aucun sidecar",
        "aucune empreinte zip",
    ]:
        if phrase not in lowered:
            errors.append(f"V9.25 markdown missing safety phrase: {phrase}")
    for phrase in ["aggtrades", "binance", "lots internes", "jours", "couverture"]:
        if phrase not in lowered:
            errors.append(f"V9.25 markdown missing campaign phrase: {phrase}")
    return errors


def validate_no_forbidden_artifacts_v9_25(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.glob("projet-galapagos-v9.25-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.25 sidecar present: {path}")
    for path in root.rglob("*v9_25*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.name in FORBIDDEN_FILENAMES:
            errors.append(f"forbidden V9.25 file present: {path}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden V9.25 file suffix present: {path}")
    return errors


def _contains_forbidden_zip_field(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            text = str(key).casefold()
            if text == "zip_sha256" or text.startswith("sidecar_"):
                return True
            if _contains_forbidden_zip_field(value):
                return True
    if isinstance(payload, list):
        return any(_contains_forbidden_zip_field(item) for item in payload)
    return False


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
