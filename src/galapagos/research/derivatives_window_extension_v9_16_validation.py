from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from galapagos.research.derivatives_window_extension_v9_16 import (
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


def validate_derivatives_window_extension_v9_16(root: Path = Path(".")) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    report_path = root / REPORT_JSON_PATH
    manifest_path = root / MANIFEST_PATH
    markdown_path = root / REPORT_MD_PATH
    if not report_path.exists():
        errors.append(f"missing V9.16 report: {REPORT_JSON_PATH}")
        return errors
    if not manifest_path.exists():
        errors.append(f"missing V9.16 manifest: {MANIFEST_PATH}")
        return errors
    if not markdown_path.exists():
        errors.append(f"missing V9.16 markdown: {REPORT_MD_PATH}")
        return errors
    report = _read_json(report_path)
    manifest = _read_json(manifest_path)
    errors.extend(validate_report_payload_v9_16(report))
    errors.extend(validate_manifest_payload_v9_16(manifest, report))
    errors.extend(validate_markdown_v9_16(markdown_path.read_text(encoding="utf-8")))
    errors.extend(validate_no_forbidden_artifacts_v9_16(root))
    return errors


def validate_report_payload_v9_16(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.16 report version mismatch")
    if report.get("source_version") != "V9.15":
        errors.append("V9.16 source_version mismatch")
    if report.get("status") != "PASS":
        errors.append("V9.16 status must be PASS")
    decision = report.get("v9_16_decision", {})
    if decision.get("decision") not in ALLOWED_DECISIONS:
        errors.append("V9.16 decision is not allowed")
    if "backtest" in str(decision.get("decision", "")).casefold():
        errors.append("V9.16 decision must not recommend a backtest")
    inventory = report.get("data_sources_inventory", [])
    candidates = report.get("candidate_windows", [])
    if len(inventory) < 5:
        errors.append("V9.16 must inventory OHLCV, aggTrades, funding, open interest and other derivatives")
    source_names = {item.get("source_name") for item in inventory}
    for required in {"OHLCV", "trades_aggTrades", "funding_rates", "open_interest", "other_derivatives_local"}:
        if required not in source_names:
            errors.append(f"V9.16 source missing from inventory: {required}")
    if len(candidates) < 4:
        errors.append("V9.16 must evaluate four candidate windows")
    errors.extend(validate_candidate_windows_v9_16(candidates))
    compatibility = report.get("compatibility_analysis", {})
    if compatibility.get("enough_for_future_walk_forward") is not False:
        errors.append("V9.16 must not mark future walk-forward as ready")
    if compatibility.get("funding_only_more_realistic_than_oi_plus_funding") is not True:
        errors.append("V9.16 must identify funding-only as more realistic than OI+funding")
    if report.get("features_created") is not False or report.get("dataset_created") is not False:
        errors.append("V9.16 must not create features or datasets")
    if report.get("ml_executed") is not False or report.get("walk_forward_executed") is not False or report.get("backtest_executed") is not False:
        errors.append("V9.16 must not execute ML, walk-forward or backtest")
    if report.get("findings") != FINDINGS:
        errors.append("V9.16 findings mismatch")
    for key, expected in SAFETY.items():
        if report.get("safety", {}).get(key) is not expected:
            errors.append(f"V9.16 safety mismatch: {key}")
    for key, expected in SAFETY_FLAGS.items():
        if report.get("safety_flags", {}).get(key) is not expected:
            errors.append(f"V9.16 safety flag mismatch: {key}")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.16 report must not contain sidecar or ZIP hash fields")
    return errors


def validate_candidate_windows_v9_16(candidates: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    by_name = {item.get("candidate_window_name"): item for item in candidates}
    required = {
        "funding_only_with_ohlcv_trades",
        "funding_and_open_interest_with_ohlcv_trades",
        "derivatives_4h_native",
        "multi_year_ohlcv_trades_without_derivatives",
    }
    for name in required:
        if name not in by_name:
            errors.append(f"V9.16 candidate window missing: {name}")
    funding = by_name.get("funding_only_with_ohlcv_trades", {})
    funding_oi = by_name.get("funding_and_open_interest_with_ohlcv_trades", {})
    if funding.get("recommendation_status") == "viable_candidate":
        errors.append("V9.16 funding-only candidate must not be viable while aggTrades end before funding starts")
    if funding_oi.get("recommendation_status") == "viable_candidate":
        errors.append("V9.16 funding+OI candidate must not be viable with current local coverage")
    for item in candidates:
        if item.get("duration_days", 0) < 0:
            errors.append(f"V9.16 candidate has negative duration: {item.get('candidate_window_name')}")
        if item.get("requires_new_feature_store") and item.get("compatible_with_existing_v9_features"):
            errors.append(f"V9.16 candidate cannot both require new features and reuse existing V9 features: {item.get('candidate_window_name')}")
    return errors


def validate_manifest_payload_v9_16(manifest: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("version") != VERSION:
        errors.append("V9.16 manifest version mismatch")
    if manifest.get("status") != report.get("status"):
        errors.append("V9.16 manifest status mismatch")
    if manifest.get("v9_16_decision", {}).get("decision") != report.get("v9_16_decision", {}).get("decision"):
        errors.append("V9.16 manifest decision mismatch")
    if manifest.get("candidate_windows_count") != len(report.get("candidate_windows", [])):
        errors.append("V9.16 manifest candidate window count mismatch")
    if manifest.get("data_sources_count") != len(report.get("data_sources_inventory", [])):
        errors.append("V9.16 manifest data source count mismatch")
    for key in ["features_created", "dataset_created", "ml_executed", "walk_forward_executed", "backtest_executed"]:
        if manifest.get(key) is not False:
            errors.append(f"V9.16 manifest must keep {key}=false")
    if manifest.get("findings") != report.get("findings"):
        errors.append("V9.16 manifest findings mismatch")
    if manifest.get("safety_flags") != report.get("safety_flags"):
        errors.append("V9.16 manifest safety flags mismatch")
    if _contains_forbidden_zip_field(manifest):
        errors.append("V9.16 manifest must not contain sidecar or ZIP hash fields")
    return errors


def validate_markdown_v9_16(text: str) -> list[str]:
    lowered = text.casefold()
    errors: list[str] = []
    for claim in FORBIDDEN_CLAIMS:
        if claim in lowered:
            errors.append(f"V9.16 markdown contains forbidden claim: {claim}")
    for phrase in ["aucun backtest", "aucun trading", "aucun ordre", "aucune strategie", "aucun signal actionnable", "aucun walk-forward"]:
        if phrase not in lowered:
            errors.append(f"V9.16 markdown missing safety phrase: {phrase}")
    for forbidden in FORBIDDEN_TERMS:
        if forbidden in lowered:
            errors.append(f"V9.16 markdown contains forbidden metric term: {forbidden}")
    for phrase in ["funding-only", "funding + oi", "derivatives 4h native"]:
        if phrase not in lowered:
            errors.append(f"V9.16 markdown missing candidate phrase: {phrase}")
    if "aucun reseau" not in lowered or "aucun telechargement" not in lowered:
        errors.append("V9.16 markdown must confirm no network and no download")
    return errors


def validate_no_forbidden_artifacts_v9_16(root: Path) -> list[str]:
    errors: list[str] = []
    for path in [
        root / "data/research/v9_16",
        root / "reports/backtests",
        root / "reports/strategies",
        root / "orders",
        root / "execution",
        root / "models",
        root / "checkpoints",
    ]:
        if path.exists():
            errors.append(f"forbidden V9.16 artifact exists: {path}")
    for path in root.glob("projet-galapagos-v9.16-audit-lite.zip.sha256.*"):
        errors.append(f"forbidden V9.16 sidecar present: {path}")
    for path in root.rglob("*v9_16*"):
        if "__pycache__" in path.parts or ".pytest_cache" in path.parts:
            continue
        if path.name in FORBIDDEN_FILENAMES:
            errors.append(f"forbidden V9.16 file present: {path}")
        if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden V9.16 file suffix present: {path}")
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
