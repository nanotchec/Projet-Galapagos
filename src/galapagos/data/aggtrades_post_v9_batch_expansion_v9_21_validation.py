from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_batch_expansion_v9_21 import (
    ALLOWED_DECISIONS,
    BASE_SAFETY_FLAGS,
    FINDINGS,
    MANIFEST_PATH,
    MAX_BATCH_DOWNLOADS,
    BATCH_END,
    BATCH_START,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SILVER_COLUMNS_V9_18,
    SOURCE_VERSION,
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


def validate_aggtrades_post_v9_batch_expansion_v9_21(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.exists():
        errors.append(f"missing V9.21 report: {REPORT_JSON_PATH}")
        return errors
    if not manifest_path.exists():
        errors.append(f"missing V9.21 manifest: {MANIFEST_PATH}")
        return errors
    if not markdown_path.exists():
        errors.append(f"missing V9.21 markdown: {REPORT_MD_PATH}")
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_21(report))
    errors.extend(validate_manifest_payload_v9_21(manifest, report))
    errors.extend(validate_markdown_v9_21(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_artifacts_v9_21(root))
    return errors


def validate_report_payload_v9_21(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.21 report version mismatch")
    if report.get("source_version") != SOURCE_VERSION:
        errors.append("V9.21 source_version mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.21 status must be PASS")
    if report.get("mode") not in {"dry-run", "collect", "validate-only"}:
        errors.append("V9.21 mode is invalid")
    decision = report.get("v9_21_decision", {})
    if decision.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.21 decision is not allowed")
    if "backtest" in str(decision.get("next_recommendation", "")).casefold():
        errors.append("V9.21 next recommendation must not be a backtest")
    errors.extend(validate_source_design_v9_21(report.get("source_public_target", {})))
    errors.extend(validate_batch_scope_v9_21(report))
    errors.extend(validate_outputs_absent_v9_21(report))
    errors.extend(validate_safety_flags_v9_21(report))
    if report.get("findings") != FINDINGS:
        errors.append("V9.21 findings mismatch")
    if report.get("silver_schema_columns") != SILVER_COLUMNS_V9_18:
        errors.append("V9.21 silver schema columns mismatch")
    if not report.get("anti_leakage_plan", {}).get("rules"):
        errors.append("V9.21 anti-leakage rules are missing")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.21 report must not contain sidecar or ZIP hash fields")
    return errors


def validate_source_design_v9_21(source: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if source.get("host") != "data.binance.vision":
        errors.append("V9.21 source host must be data.binance.vision")
    if source.get("market_type") != "spot" or source.get("symbol") != "BTCUSDT":
        errors.append("V9.21 source must be BTCUSDT spot")
    for key in ["account_required", "api_key_required", "private_endpoint_required", "exchange_auth_required", "websocket_live_required"]:
        if source.get(key) is not False:
            errors.append(f"V9.21 source must keep {key}=false")
    template = source.get("download_url_template", "")
    if not template.startswith("https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/"):
        errors.append("V9.21 download template must use the public Binance archive")
    return errors


def validate_batch_scope_v9_21(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    batch = report.get("batch_window", {})
    global_window = report.get("global_target_window", {})
    summary = report.get("batch_validation", {}).get("summary", {})
    if batch.get("start") != BATCH_START or batch.get("end") != BATCH_END:
        errors.append("V9.21 batch window mismatch")
    if batch.get("days_requested", 0) > MAX_BATCH_DOWNLOADS:
        errors.append("V9.21 batch must not exceed 60 requested days")
    if batch.get("max_downloads") is None and report.get("mode") == "collect":
        errors.append("V9.21 collect mode must record max_downloads")
    max_downloads = batch.get("max_downloads")
    if report.get("mode") == "collect" and isinstance(max_downloads, int) and max_downloads > MAX_BATCH_DOWNLOADS:
        errors.append("V9.21 max_downloads must not exceed 60")
    if global_window.get("days_expected") != 772:
        errors.append("V9.21 global target window must contain 772 days")
    if global_window.get("complete_collection_reached") is not False or report.get("complete_collection_reached") is not False:
        errors.append("V9.21 must not mark full collection complete")
    if summary.get("days_requested") != batch.get("days_requested"):
        errors.append("V9.21 batch summary day count mismatch")
    if report.get("mode") == "collect" and summary.get("days_attempted", 0) > MAX_BATCH_DOWNLOADS:
        errors.append("V9.21 collect attempted too many days")
    if report.get("mode") == "collect" and report.get("collection_executed") is not True:
        errors.append("V9.21 collect must set collection_executed=true")
    if summary.get("future_full_coverage_complete") is not False:
        errors.append("V9.21 batch summary must not claim full future coverage")
    if report.get("mode") == "collect" and summary.get("days_requested") != 60:
        errors.append("V9.21 collect batch must request exactly 60 days")
    if report.get("mode") == "collect" and batch.get("max_downloads") != 60:
        errors.append("V9.21 collect batch must record max_downloads=60")
    if summary.get("complete_collection_reached") is not False:
        errors.append("V9.21 batch summary must keep complete_collection_reached=false")
    return errors


def validate_outputs_absent_v9_21(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["features_created", "labels_created", "dataset_created", "ml_executed", "walk_forward_executed", "backtest_executed"]:
        if report.get(key) is not False:
            errors.append(f"V9.21 must keep {key}=false")
    return errors


def validate_safety_flags_v9_21(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    flags = report.get("safety_flags", {})
    for key, expected in BASE_SAFETY_FLAGS.items():
        if key in {"network_used", "new_data_downloaded", "ingestion_executed", "no_new_data_download", "no_ingestion_executed"}:
            continue
        if flags.get(key) is not expected:
            errors.append(f"V9.21 safety flag mismatch: {key}")
    if report.get("collection_executed") is True:
        if flags.get("network_scope") != "public_archive_read_only":
            errors.append("V9.21 collect must use public_archive_read_only network scope")
        if flags.get("new_data_download_scope") != "public_historical_aggtrades_batch_expansion_only":
            errors.append("V9.21 collect must limit download scope to public_historical_aggtrades_batch_expansion_only")
        if flags.get("ingestion_scope") != "public_aggtrades_bronze_silver_batch_expansion_only":
            errors.append("V9.21 collect must limit ingestion scope to public_aggtrades_bronze_silver_batch_expansion_only")
    if flags.get("api_key_used") is not False or flags.get("private_endpoint_used") is not False:
        errors.append("V9.21 must confirm no API key and no private endpoint")
    if flags.get("exchange_auth_used") is not False or flags.get("websocket_live_used") is not False:
        errors.append("V9.21 must confirm no exchange auth and no websocket live")
    return errors


def validate_manifest_payload_v9_21(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.21 manifest version mismatch")
    if manifest.get("status") != report.get("status"):
        errors.append("V9.21 manifest status mismatch")
    if manifest.get("mode") != report.get("mode"):
        errors.append("V9.21 manifest mode mismatch")
    summary = report.get("batch_validation", {}).get("summary", {})
    for key in ["days_requested", "days_attempted", "days_downloaded", "days_normalized", "days_skipped_existing", "days_complete", "days_failed", "days_quarantined", "total_rows"]:
        if manifest.get(key) != summary.get(key):
            errors.append(f"V9.21 manifest {key} mismatch")
    if manifest.get("collection_executed") != report.get("collection_executed"):
        errors.append("V9.21 manifest collection_executed mismatch")
    if manifest.get("network_used") != report.get("network_used"):
        errors.append("V9.21 manifest network_used mismatch")
    if manifest.get("api_key_used") is not False or manifest.get("private_endpoint_used") is not False:
        errors.append("V9.21 manifest must confirm no API key and no private endpoint")
    if manifest.get("v9_21_decision", {}).get("decision") != report.get("v9_21_decision", {}).get("decision"):
        errors.append("V9.21 manifest decision mismatch")
    if manifest.get("findings") != report.get("findings"):
        errors.append("V9.21 manifest findings mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.21 manifest safety flags mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.21 manifest must not contain sidecar or ZIP hash fields")
    return errors


def validate_markdown_v9_21(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            errors.append(f"V9.21 markdown contains forbidden claim: {claim}")
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.21 markdown contains forbidden metric term: {forbidden}")
    for phrase in [
        "aucun trading",
        "aucun paper live",
        "aucun ordre",
        "aucun backtest",
        "aucun walk-forward",
        "aucune strategie",
        "aucun signal actionnable",
        "aucune api privee",
        "aucune cle api",
        "aucun client exchange authentifie",
        "aucun websocket live",
        "aucun sidecar",
        "aucune empreinte zip",
    ]:
        if phrase not in lowered:
            errors.append(f"V9.21 markdown missing safety phrase: {phrase}")
    for phrase in ["aggtrades", "binance", "batch", "jours demandes", "jours valides"]:
        if phrase not in lowered:
            errors.append(f"V9.21 markdown missing batch phrase: {phrase}")
    return errors


def validate_no_forbidden_artifacts_v9_21(root: Path) -> list[str]:
    errors: list[str] = []
    forbidden_paths = [
        root / "data/research/v9_21",
        root / "reports/backtests",
        root / "reports/strategies",
        root / "orders",
        root / "execution",
        root / "models",
        root / "checkpoints",
    ]
    for path in forbidden_paths:
        if path.exists():
            errors.append(f"forbidden V9.21 artifact exists: {path}")
    for path in root.glob("projet-galapagos-v9.21-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.21 sidecar present: {path}")
    for path in root.rglob("*v9_21*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.name in FORBIDDEN_FILENAMES:
            errors.append(f"forbidden V9.21 file present: {path}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden V9.21 file suffix present: {path}")
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
