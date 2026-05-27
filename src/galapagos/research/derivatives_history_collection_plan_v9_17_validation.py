from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.derivatives_history_collection_plan_v9_17 import (
    ALLOWED_DECISIONS,
    FINDINGS,
    MANIFEST_PATH,
    REPORT_JSON_PATH,
    REPORT_MD_PATH,
    SAFETY,
    SAFETY_FLAGS,
    VERSION,
)


FORBIDDEN_CLAIMS = [
    "strategy validated",
    "tradable edge confirmed",
    "live trading ready",
    "profitability confirmed",
]
FORBIDDEN_TERMS = ["pnl", "sharpe", "drawdown", "equity curve", "profit factor"]
FORBIDDEN_FILENAMES = {"Icon", "Icon\r", ".DS_Store", ".env"}
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pem", ".key", ".sha256.json", ".sha256.txt"}


def validate_derivatives_history_collection_plan_v9_17(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.exists():
        errors.append(f"missing V9.17 report: {REPORT_JSON_PATH}")
        return errors
    if not manifest_path.exists():
        errors.append(f"missing V9.17 manifest: {MANIFEST_PATH}")
        return errors
    if not markdown_path.exists():
        errors.append(f"missing V9.17 markdown: {REPORT_MD_PATH}")
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_17(report))
    errors.extend(validate_manifest_payload_v9_17(manifest, report))
    errors.extend(validate_markdown_v9_17(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_artifacts_v9_17(root))
    return errors


def validate_report_payload_v9_17(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.17 report version mismatch")
    if report.get("source_version") != "V9.16":
        errors.append("V9.17 source_version mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.17 status must be PASS")
    decision = report.get("v9_17_decision", {})
    if decision.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.17 decision is not allowed")
    if "backtest" in str(decision.get("decision", "")).casefold():
        errors.append("V9.17 decision must not recommend a backtest")
    if decision.get("collection_executed") is not False:
        errors.append("V9.17 decision must mark collection_executed=false")
    if report.get("collection_executed") is not False:
        errors.append("V9.17 must not execute collection")
    for key in ["features_created", "dataset_created", "ml_executed", "walk_forward_executed", "backtest_executed"]:
        if report.get(key) is not False:
            errors.append(f"V9.17 must keep {key}=false")
    source_candidates = report.get("source_collection_candidates", [])
    target_windows = report.get("candidate_target_windows", [])
    if len(source_candidates) < 5:
        errors.append("V9.17 must define at least five source collection candidates")
    if len(target_windows) < 4:
        errors.append("V9.17 must define four target windows")
    errors.extend(validate_source_candidates_v9_17(source_candidates))
    errors.extend(validate_target_windows_v9_17(target_windows))
    if not report.get("storage_plan", {}).get("bronze_raw"):
        errors.append("V9.17 storage plan must define bronze_raw")
    if not report.get("quality_validation_plan"):
        errors.append("V9.17 quality validation plan is missing")
    if not report.get("anti_leakage_plan", {}).get("timestamp_rules"):
        errors.append("V9.17 anti leakage timestamp rules are missing")
    if report.get("findings") != FINDINGS:
        errors.append("V9.17 findings mismatch")
    for key, expected in SAFETY.items():
        if report.get("safety", {}).get(key) is not expected:
            errors.append(f"V9.17 safety mismatch: {key}")
    for key, expected in SAFETY_FLAGS.items():
        if report.get("safety_flags", {}).get(key) is not expected:
            errors.append(f"V9.17 safety flag mismatch: {key}")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.17 report must not contain sidecar or ZIP hash fields")
    return errors


def validate_source_candidates_v9_17(candidates: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    by_name = {item.get("source_name"): item for item in candidates}
    required = {
        "aggTrades_public_trades_post_v9",
        "funding_rates_historical",
        "open_interest_history",
        "derivatives_ohlcv_futures_klines_4h",
        "liquidations_long_short_ratios",
    }
    for name in required:
        if name not in by_name:
            errors.append(f"V9.17 source candidate missing: {name}")
    aggtrades = by_name.get("aggTrades_public_trades_post_v9", {})
    if aggtrades.get("integration_priority") != "priority_1":
        errors.append("V9.17 aggTrades post-V9 must be priority_1")
    if aggtrades.get("needs_api_key") is not False:
        errors.append("V9.17 aggTrades collection plan must not require an API key")
    if aggtrades.get("network_required_future_collection") is not True:
        errors.append("V9.17 aggTrades future collection should explicitly require future network, not current network")
    for item in candidates:
        if item.get("needs_api_key") is True:
            errors.append(f"V9.17 candidate must not require API key: {item.get('source_name')}")
        if not item.get("quality_checks_required"):
            errors.append(f"V9.17 candidate missing quality checks: {item.get('source_name')}")
        if "available_ts" not in item.get("expected_causal_timestamp_fields", []):
            errors.append(f"V9.17 candidate missing available_ts: {item.get('source_name')}")
    return errors


def validate_target_windows_v9_17(windows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    by_name = {item.get("window_name"): item for item in windows}
    required = {"funding_first_post_v9", "v9_historical_with_added_funding", "funding_open_interest_recent", "derivatives_native_4h"}
    for name in required:
        if name not in by_name:
            errors.append(f"V9.17 target window missing: {name}")
    if by_name.get("funding_first_post_v9", {}).get("recommendation_status") != "priority_1_collection_plan":
        errors.append("V9.17 funding-first window must be priority 1")
    if by_name.get("funding_open_interest_recent", {}).get("recommendation_status") != "reject_too_short":
        errors.append("V9.17 recent funding+OI window must be rejected as too short")
    if by_name.get("funding_first_post_v9", {}).get("suitable_for_future_walk_forward") is not True:
        errors.append("V9.17 funding-first plan must be long enough for a future walk-forward candidate after collection")
    return errors


def validate_manifest_payload_v9_17(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.17 manifest version mismatch")
    if manifest.get("status") != report.get("status"):
        errors.append("V9.17 manifest status mismatch")
    if manifest.get("v9_17_decision", {}).get("decision") != report.get("v9_17_decision", {}).get("decision"):
        errors.append("V9.17 manifest decision mismatch")
    if manifest.get("source_collection_candidates_count") != len(report.get("source_collection_candidates", [])):
        errors.append("V9.17 manifest source candidate count mismatch")
    if manifest.get("candidate_target_windows_count") != len(report.get("candidate_target_windows", [])):
        errors.append("V9.17 manifest target window count mismatch")
    for key in ["collection_executed", "features_created", "dataset_created", "ml_executed", "walk_forward_executed", "backtest_executed"]:
        if manifest.get(key) is not False:
            errors.append(f"V9.17 manifest must keep {key}=false")
    if manifest.get("findings") != report.get("findings"):
        errors.append("V9.17 manifest findings mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.17 manifest safety flags mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.17 manifest must not contain sidecar or ZIP hash fields")
    return errors


def validate_markdown_v9_17(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            errors.append(f"V9.17 markdown contains forbidden claim: {claim}")
    for phrase in ["aucun backtest", "aucun trading", "aucun ordre", "aucune strategie", "aucun signal actionnable", "aucun walk-forward"]:
        if phrase not in lowered:
            errors.append(f"V9.17 markdown missing safety phrase: {phrase}")
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.17 markdown contains forbidden metric term: {forbidden}")
    for phrase in ["aggtrades", "funding", "open interest", "bronze", "silver", "research"]:
        if phrase not in lowered:
            errors.append(f"V9.17 markdown missing planning phrase: {phrase}")
    if "aucun reseau" not in lowered or "aucun telechargement" not in lowered or "aucune ingestion" not in lowered:
        errors.append("V9.17 markdown must confirm no network, no download and no ingestion")
    return errors


def validate_no_forbidden_artifacts_v9_17(root: Path) -> list[str]:
    errors: list[str] = []
    for path in [
        root / "data/research/v9_17",
        root / "reports/backtests",
        root / "reports/strategies",
        root / "orders",
        root / "execution",
        root / "models",
        root / "checkpoints",
    ]:
        if path.exists():
            errors.append(f"forbidden V9.17 artifact exists: {path}")
    for path in root.glob("projet-galapagos-v9.17-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.17 sidecar present: {path}")
    for path in root.rglob("*v9_17*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.name in FORBIDDEN_FILENAMES:
            errors.append(f"forbidden V9.17 file present: {path}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden V9.17 file suffix present: {path}")
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
