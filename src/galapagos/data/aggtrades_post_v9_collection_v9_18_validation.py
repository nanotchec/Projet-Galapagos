from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.data.aggtrades_post_v9_collection_v9_18 import (
    ALLOWED_DECISIONS,
    BASE_SAFETY_FLAGS,
    FINDINGS,
    FUNDING_FIRST_END,
    FUNDING_FIRST_START,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SILVER_COLUMNS_V9_18,
    TARGET_END,
    TARGET_START,
    VERSION,
)


FORBIDDEN_CLAIMS = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "profitability confirmed",
]
FORBIDDEN_TERMS = ["sharpe", "drawdown", "equity curve", "profit factor"]
FORBIDDEN_FILENAMES = {"Icon", "Icon\r", ".DS_Store", ".env"}
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pem", ".key", ".sha256.json", ".sha256.txt"}


def validate_aggtrades_post_v9_collection_v9_18(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.exists():
        errors.append(f"missing V9.18 report: {REPORT_JSON_PATH}")
        return errors
    if not manifest_path.exists():
        errors.append(f"missing V9.18 manifest: {MANIFEST_PATH}")
        return errors
    if not markdown_path.exists():
        errors.append(f"missing V9.18 markdown: {REPORT_MD_PATH}")
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_18(report))
    errors.extend(validate_manifest_payload_v9_18(manifest, report))
    errors.extend(validate_markdown_v9_18(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_artifacts_v9_18(root, report))
    return errors


def validate_report_payload_v9_18(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.18 report version mismatch")
    if report.get("source_version") != "V9.17":
        errors.append("V9.18 source_version mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.18 status must be PASS for the audited dry-run pack")
    if report.get("mode") not in {"dry-run", "collect", "validate-only"}:
        errors.append("V9.18 mode is invalid")
    decision = report.get("v9_18_decision", {})
    if decision.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.18 decision is not allowed")
    if "backtest" in str(decision.get("next_recommendation", "")).casefold():
        errors.append("V9.18 next recommendation must not be a backtest")
    errors.extend(validate_source_design_v9_18(report.get("source_public_target", {})))
    errors.extend(validate_coverage_v9_18(report))
    errors.extend(validate_outputs_absent_v9_18(report))
    errors.extend(validate_safety_flags_v9_18(report))
    if report.get("findings") != FINDINGS:
        errors.append("V9.18 findings mismatch")
    if report.get("silver_schema_columns") != SILVER_COLUMNS_V9_18:
        errors.append("V9.18 silver schema columns mismatch")
    if not report.get("quality_validation_plan"):
        errors.append("V9.18 quality validation plan is missing")
    if not report.get("anti_leakage_plan", {}).get("rules"):
        errors.append("V9.18 anti-leakage rules are missing")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.18 report must not contain sidecar or ZIP hash fields")
    return errors


def validate_source_design_v9_18(source: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if source.get("host") != "data.binance.vision":
        errors.append("V9.18 source host must be data.binance.vision")
    if source.get("market_type") != "spot" or source.get("symbol") != "BTCUSDT":
        errors.append("V9.18 source must be BTCUSDT spot")
    for key in ["account_required", "api_key_required", "private_endpoint_required", "exchange_auth_required", "websocket_live_required"]:
        if source.get(key) is not False:
            errors.append(f"V9.18 source must keep {key}=false")
    template = source.get("download_url_template", "")
    if not template.startswith("https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/"):
        errors.append("V9.18 download template must use the public Binance archive")
    return errors


def validate_coverage_v9_18(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    target = report.get("target_window", {})
    funding = report.get("future_funding_first_window", {})
    coverage = report.get("coverage_summary", {})
    if target.get("start") != TARGET_START or target.get("end") != TARGET_END:
        errors.append("V9.18 target window mismatch")
    if funding.get("start") != FUNDING_FIRST_START or funding.get("end") != FUNDING_FIRST_END:
        errors.append("V9.18 funding-first window mismatch")
    if target.get("days_expected") != 772 or coverage.get("days_expected") != 772:
        errors.append("V9.18 target window must contain 772 expected days")
    if funding.get("days_expected") != 731:
        errors.append("V9.18 funding-first window must contain 731 expected days")
    if coverage.get("days_already_present", 0) + coverage.get("days_missing", 0) + coverage.get("days_partial", 0) + coverage.get("days_quarantined", 0) != coverage.get("days_expected"):
        errors.append("V9.18 day counts must sum to expected days")
    if report.get("mode") == "dry-run" and report.get("collection_executed") is not False:
        errors.append("V9.18 dry-run must keep collection_executed=false")
    if report.get("mode") == "dry-run" and report.get("v9_18_decision", {}).get("decision") != "aggtrades_post_v9_collection_pack_ready_dry_run_only":
        errors.append("V9.18 dry-run decision mismatch")
    return errors


def validate_outputs_absent_v9_18(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["features_created", "labels_created", "dataset_created", "ml_executed", "walk_forward_executed", "backtest_executed"]:
        if report.get(key) is not False:
            errors.append(f"V9.18 must keep {key}=false")
    if report.get("collection_executed") is False:
        for key in ["network_used", "new_data_downloaded", "ingestion_executed"]:
            if report.get(key) is not False:
                errors.append(f"V9.18 dry-run must keep {key}=false")
    return errors


def validate_safety_flags_v9_18(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    flags = report.get("safety_flags", {})
    for key, expected in BASE_SAFETY_FLAGS.items():
        if flags.get(key) is not expected:
            errors.append(f"V9.18 safety flag mismatch: {key}")
    if report.get("collection_executed") is False:
        for key in ["network_used", "no_new_data_download", "no_ingestion_executed"]:
            expected = False if key == "network_used" else True
            if flags.get(key) is not expected:
                errors.append(f"V9.18 dry-run safety flag mismatch: {key}")
    if report.get("collection_executed") is True:
        if flags.get("network_scope") != "public_archive_read_only":
            errors.append("V9.18 collect mode must use public_archive_read_only network scope")
    return errors


def validate_manifest_payload_v9_18(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.18 manifest version mismatch")
    if manifest.get("status") != report.get("status"):
        errors.append("V9.18 manifest status mismatch")
    if manifest.get("mode") != report.get("mode"):
        errors.append("V9.18 manifest mode mismatch")
    if manifest.get("days_expected") != report.get("coverage_summary", {}).get("days_expected"):
        errors.append("V9.18 manifest days_expected mismatch")
    if manifest.get("days_missing") != report.get("coverage_summary", {}).get("days_missing"):
        errors.append("V9.18 manifest days_missing mismatch")
    if manifest.get("collection_executed") != report.get("collection_executed"):
        errors.append("V9.18 manifest collection_executed mismatch")
    if manifest.get("network_used") != report.get("network_used"):
        errors.append("V9.18 manifest network_used mismatch")
    if manifest.get("api_key_used") is not False or manifest.get("private_endpoint_used") is not False:
        errors.append("V9.18 manifest must confirm no API key and no private endpoint")
    if manifest.get("v9_18_decision", {}).get("decision") != report.get("v9_18_decision", {}).get("decision"):
        errors.append("V9.18 manifest decision mismatch")
    if manifest.get("findings") != report.get("findings"):
        errors.append("V9.18 manifest findings mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.18 manifest safety flags mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.18 manifest must not contain sidecar or ZIP hash fields")
    return errors


def validate_markdown_v9_18(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            errors.append(f"V9.18 markdown contains forbidden claim: {claim}")
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.18 markdown contains forbidden metric term: {forbidden}")
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
        "aucun websocket live",
        "aucun sidecar",
        "aucune empreinte zip",
    ]:
        if phrase not in lowered:
            errors.append(f"V9.18 markdown missing safety phrase: {phrase}")
    for phrase in ["aggtrades", "binance", "bronze", "silver", "jours attendus", "jours manquants"]:
        if phrase not in lowered:
            errors.append(f"V9.18 markdown missing collection phrase: {phrase}")
    return errors


def validate_no_forbidden_artifacts_v9_18(root: Path, report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    forbidden_paths = [
        root / "data/research/v9_18",
        root / "reports/backtests",
        root / "reports/strategies",
        root / "orders",
        root / "execution",
        root / "models",
        root / "checkpoints",
    ]
    if report.get("collection_executed") is False:
        forbidden_paths.extend(
            [
                root / "data/silver/public_trades/venue=binance/market_type=spot/symbol=BTCUSDT/date=2024-03-25",
                root / "data/quarantine/public_trades/venue=binance/market_type=spot/symbol=BTCUSDT",
            ]
        )
    for path in forbidden_paths:
        if path.exists():
            errors.append(f"forbidden V9.18 artifact exists: {path}")
    for path in root.glob("projet-galapagos-v9.18-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.18 sidecar present: {path}")
    for path in root.rglob("*v9_18*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.name in FORBIDDEN_FILENAMES:
            errors.append(f"forbidden V9.18 file present: {path}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden V9.18 file suffix present: {path}")
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
