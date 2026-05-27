from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_pilot_collection_v9_19 import (
    ALLOWED_DECISIONS,
    BASE_SAFETY_FLAGS,
    FINDINGS,
    MANIFEST_PATH,
    MAX_PILOT_DOWNLOADS,
    PILOT_END,
    PILOT_START,
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


def validate_aggtrades_post_v9_pilot_collection_v9_19(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.exists():
        errors.append(f"missing V9.19 report: {REPORT_JSON_PATH}")
        return errors
    if not manifest_path.exists():
        errors.append(f"missing V9.19 manifest: {MANIFEST_PATH}")
        return errors
    if not markdown_path.exists():
        errors.append(f"missing V9.19 markdown: {REPORT_MD_PATH}")
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_19(report))
    errors.extend(validate_manifest_payload_v9_19(manifest, report))
    errors.extend(validate_markdown_v9_19(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_artifacts_v9_19(root))
    return errors


def validate_report_payload_v9_19(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.19 report version mismatch")
    if report.get("source_version") != SOURCE_VERSION:
        errors.append("V9.19 source_version mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.19 status must be PASS")
    if report.get("mode") not in {"dry-run", "collect", "validate-only"}:
        errors.append("V9.19 mode is invalid")
    decision = report.get("v9_19_decision", {})
    if decision.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.19 decision is not allowed")
    if "backtest" in str(decision.get("next_recommendation", "")).casefold():
        errors.append("V9.19 next recommendation must not be a backtest")
    errors.extend(validate_source_design_v9_19(report.get("source_public_target", {})))
    errors.extend(validate_pilot_scope_v9_19(report))
    errors.extend(validate_outputs_absent_v9_19(report))
    errors.extend(validate_safety_flags_v9_19(report))
    if report.get("findings") != FINDINGS:
        errors.append("V9.19 findings mismatch")
    if report.get("silver_schema_columns") != SILVER_COLUMNS_V9_18:
        errors.append("V9.19 silver schema columns mismatch")
    if not report.get("anti_leakage_plan", {}).get("rules"):
        errors.append("V9.19 anti-leakage rules are missing")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.19 report must not contain sidecar or ZIP hash fields")
    return errors


def validate_source_design_v9_19(source: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if source.get("host") != "data.binance.vision":
        errors.append("V9.19 source host must be data.binance.vision")
    if source.get("market_type") != "spot" or source.get("symbol") != "BTCUSDT":
        errors.append("V9.19 source must be BTCUSDT spot")
    for key in ["account_required", "api_key_required", "private_endpoint_required", "exchange_auth_required", "websocket_live_required"]:
        if source.get(key) is not False:
            errors.append(f"V9.19 source must keep {key}=false")
    template = source.get("download_url_template", "")
    if not template.startswith("https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/"):
        errors.append("V9.19 download template must use the public Binance archive")
    return errors


def validate_pilot_scope_v9_19(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    pilot = report.get("pilot_window", {})
    global_window = report.get("global_target_window", {})
    summary = report.get("pilot_validation", {}).get("summary", {})
    if pilot.get("start") != PILOT_START or pilot.get("end") != PILOT_END:
        errors.append("V9.19 pilot window mismatch")
    if pilot.get("days_requested", 0) > MAX_PILOT_DOWNLOADS:
        errors.append("V9.19 pilot must not exceed 7 requested days")
    if pilot.get("max_downloads") is None and report.get("mode") == "collect":
        errors.append("V9.19 collect mode must record max_downloads")
    max_downloads = pilot.get("max_downloads")
    if report.get("mode") == "collect" and isinstance(max_downloads, int) and max_downloads > MAX_PILOT_DOWNLOADS:
        errors.append("V9.19 max_downloads must not exceed 7")
    if global_window.get("days_expected") != 772:
        errors.append("V9.19 global target window must contain 772 days")
    if global_window.get("complete_collection_reached") is not False or report.get("complete_collection_reached") is not False:
        errors.append("V9.19 must not mark full collection complete")
    if summary.get("days_requested") != pilot.get("days_requested"):
        errors.append("V9.19 pilot summary day count mismatch")
    if report.get("mode") == "collect" and summary.get("days_attempted", 0) > MAX_PILOT_DOWNLOADS:
        errors.append("V9.19 collect attempted too many days")
    if report.get("mode") == "collect" and report.get("collection_executed") is not True:
        errors.append("V9.19 collect must set collection_executed=true")
    if summary.get("future_full_coverage_complete") is not False:
        errors.append("V9.19 pilot summary must not claim full future coverage")
    return errors


def validate_outputs_absent_v9_19(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["features_created", "labels_created", "dataset_created", "ml_executed", "walk_forward_executed", "backtest_executed"]:
        if report.get(key) is not False:
            errors.append(f"V9.19 must keep {key}=false")
    return errors


def validate_safety_flags_v9_19(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    flags = report.get("safety_flags", {})
    for key, expected in BASE_SAFETY_FLAGS.items():
        if key in {"network_used", "new_data_downloaded", "ingestion_executed", "no_new_data_download", "no_ingestion_executed"}:
            continue
        if flags.get(key) is not expected:
            errors.append(f"V9.19 safety flag mismatch: {key}")
    if report.get("collection_executed") is True:
        if flags.get("network_scope") != "public_archive_read_only":
            errors.append("V9.19 collect must use public_archive_read_only network scope")
        if flags.get("new_data_download_scope") != "public_historical_aggtrades_pilot_only":
            errors.append("V9.19 collect must limit download scope to public_historical_aggtrades_pilot_only")
        if flags.get("ingestion_scope") != "public_aggtrades_bronze_silver_pilot_only":
            errors.append("V9.19 collect must limit ingestion scope to public_aggtrades_bronze_silver_pilot_only")
    if flags.get("api_key_used") is not False or flags.get("private_endpoint_used") is not False:
        errors.append("V9.19 must confirm no API key and no private endpoint")
    if flags.get("exchange_auth_used") is not False or flags.get("websocket_live_used") is not False:
        errors.append("V9.19 must confirm no exchange auth and no websocket live")
    return errors


def validate_manifest_payload_v9_19(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.19 manifest version mismatch")
    if manifest.get("status") != report.get("status"):
        errors.append("V9.19 manifest status mismatch")
    if manifest.get("mode") != report.get("mode"):
        errors.append("V9.19 manifest mode mismatch")
    summary = report.get("pilot_validation", {}).get("summary", {})
    for key in ["days_requested", "days_attempted", "days_downloaded", "days_normalized", "days_complete", "days_failed", "days_quarantined", "total_rows"]:
        if manifest.get(key) != summary.get(key):
            errors.append(f"V9.19 manifest {key} mismatch")
    if manifest.get("collection_executed") != report.get("collection_executed"):
        errors.append("V9.19 manifest collection_executed mismatch")
    if manifest.get("network_used") != report.get("network_used"):
        errors.append("V9.19 manifest network_used mismatch")
    if manifest.get("api_key_used") is not False or manifest.get("private_endpoint_used") is not False:
        errors.append("V9.19 manifest must confirm no API key and no private endpoint")
    if manifest.get("v9_19_decision", {}).get("decision") != report.get("v9_19_decision", {}).get("decision"):
        errors.append("V9.19 manifest decision mismatch")
    if manifest.get("findings") != report.get("findings"):
        errors.append("V9.19 manifest findings mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.19 manifest safety flags mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.19 manifest must not contain sidecar or ZIP hash fields")
    return errors


def validate_markdown_v9_19(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            errors.append(f"V9.19 markdown contains forbidden claim: {claim}")
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.19 markdown contains forbidden metric term: {forbidden}")
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
            errors.append(f"V9.19 markdown missing safety phrase: {phrase}")
    for phrase in ["aggtrades", "binance", "pilot", "jours demandes", "jours valides"]:
        if phrase not in lowered:
            errors.append(f"V9.19 markdown missing pilot phrase: {phrase}")
    return errors


def validate_no_forbidden_artifacts_v9_19(root: Path) -> list[str]:
    errors: list[str] = []
    forbidden_paths = [
        root / "data/research/v9_19",
        root / "reports/backtests",
        root / "reports/strategies",
        root / "orders",
        root / "execution",
        root / "models",
        root / "checkpoints",
    ]
    for path in forbidden_paths:
        if path.exists():
            errors.append(f"forbidden V9.19 artifact exists: {path}")
    for path in root.glob("projet-galapagos-v9.19-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.19 sidecar present: {path}")
    for path in root.rglob("*v9_19*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.name in FORBIDDEN_FILENAMES:
            errors.append(f"forbidden V9.19 file present: {path}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden V9.19 file suffix present: {path}")
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
