from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.16"
ZIP_NAME = "projet-galapagos-v9.16-audit-lite.zip"

REQUIRED_FILES = [
    "scripts/_bootstrap.py",
    "scripts/run_derivatives_window_extension_v9_16.py",
    "scripts/validate_derivatives_window_extension_v9_16.py",
    "scripts/release_audit_lite_zip_v9_16.py",
    "scripts/audit_audit_lite_zip_v9_16.py",
    "scripts/smoke_audit_lite_zip_v9_16.py",
    "src/galapagos/research/derivatives_window_extension_v9_16.py",
    "src/galapagos/research/derivatives_window_extension_v9_16_validation.py",
    "tests/research/test_derivatives_window_extension_v9_16.py",
    "tests/validation/test_derivatives_window_extension_v9_16_validator.py",
    "reports/manifests/derivatives_window_extension_v9_16_manifest.json",
    "reports/research_decisions/derivatives_window_extension_v9_16.json",
    "reports/research_decisions/derivatives_window_extension_v9_16.md",
    "docs/derivatives_window_extension_v9_16.md",
    "reports/audit_lite/v9_16_command_results.json",
    "reports/audit_lite/v9_16_full_local_validation_attestation.json",
    "reports/audit_lite/v9_16_artifact_inventory.json",
    "reports/audit_lite/zip_size_report_v9_16.json",
    "reports/audit_lite/zip_audit_v9_16.json",
    "reports/audit_lite/zip_smoke_v9_16.json",
    "reports/research_decisions/derivatives_data_extension_readiness_v9_15.json",
    "reports/manifests/derivatives_data_extension_readiness_v9_15_manifest.json",
    "reports/research_decisions/feature_label_separability_v9_14_1.json",
    "reports/manifests/feature_label_separability_v9_14_1_manifest.json",
    "reports/research/derivatives_coverage_v1_14.json",
    "reports/research/derivatives_data_quality_v1_14.json",
    "reports/research/derivatives_features_v1_14.json",
    "reports/research/derivatives_coverage_expansion_v1_14.json",
    "reports/manifests/max_history_public_market_data_v5_0_manifest.json",
    "reports/manifests/public_trades_1y_window_v8_2_manifest.json",
    "reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_metrics.json",
    "reports/current/latest_summary.md",
    "README.md",
    "pyproject.toml",
]

FORBIDDEN_PREFIXES = ["data/research/", "data/silver/", "data/gold/", "reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/", "checkpoints/", ".git/", ".venv/"]
FORBIDDEN_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_NAMES = {".DS_Store", ".env", "Icon", "Icon\r"}
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".zip", ".pem", ".key"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    zip_path = Path(args.zip_path).resolve()
    result = {"version": VERSION, "zip": str(zip_path), "passed": False, "errors": audit_zip(zip_path)}
    result["passed"] = not result["errors"]
    _write_reports(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


def audit_zip(zip_path: Path) -> list[str]:
    if not zip_path.exists():
        return [f"missing zip: {zip_path}"]
    if not zipfile.is_zipfile(zip_path):
        return [f"not a valid zip: {zip_path}"]
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_16_audit_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            names = sorted(archive.namelist())
            archive.extractall(extract_root)
        missing = [path for path in REQUIRED_FILES if path not in names]
        if missing:
            errors.append(f"missing required files: {missing}")
        forbidden = [name for name in names if _is_forbidden(name)]
        if forbidden:
            errors.append(f"forbidden files present: {forbidden[:50]}")
        errors.extend(_check_inventory(extract_root, names, zip_path))
        errors.extend(_check_reports(extract_root))
        errors.extend(_check_state(extract_root))
    return errors


def _check_inventory(extract_root: Path, names: list[str], zip_path: Path) -> list[str]:
    errors: list[str] = []
    inventory = _read_json(extract_root / "reports/audit_lite/v9_16_artifact_inventory.json")
    size_report = _read_json(extract_root / "reports/audit_lite/zip_size_report_v9_16.json")
    if inventory.get("zip_name") != ZIP_NAME:
        errors.append("inventory zip_name mismatch")
    if inventory.get("files_count") != len(names) or sorted(inventory.get("files", [])) != names:
        errors.append("inventory files do not match ZIP content")
    # ZIP byte size is an embedded estimate only; it is not authoritative.
    for payload_name, payload in {"inventory": inventory, "size_report": size_report}.items():
        if not isinstance(payload.get("zip_bytes_estimate"), int) or payload.get("zip_bytes_estimate", 0) <= 0:
            errors.append(f"{payload_name} must contain a positive zip_bytes_estimate")
        if payload.get("zip_bytes_is_authoritative") is not False:
            errors.append(f"{payload_name} must mark zip_bytes_is_authoritative=false")
    for payload in [inventory, size_report]:
        if _contains_forbidden_zip_field(payload):
            errors.append("forbidden hash or sidecar field present")
        if payload.get("sidecars_created") is not False or payload.get("zip_fingerprints_created") is not False:
            errors.append("sidecars/fingerprints flags must be false")
    for key, value in inventory.get("forbidden_absences_verified", {}).items():
        if value is not True:
            errors.append(f"forbidden absence failed: {key}")
    return errors


def _check_reports(extract_root: Path) -> list[str]:
    errors: list[str] = []
    report = _read_json(extract_root / "reports/research_decisions/derivatives_window_extension_v9_16.json")
    attestation = _read_json(extract_root / "reports/audit_lite/v9_16_full_local_validation_attestation.json")
    if report.get("v9_16_decision", {}).get("decision") != "data_extension_should_collect_more_history":
        errors.append("V9.16 decision mismatch")
    if report.get("features_created") is not False or report.get("dataset_created") is not False:
        errors.append("V9.16 must not create features or datasets in this ZIP")
    if report.get("ml_executed") is not False or report.get("walk_forward_executed") is not False or report.get("backtest_executed") is not False:
        errors.append("V9.16 must not execute ML, walk-forward or backtest")
    candidate_names = {item.get("candidate_window_name"): item for item in report.get("candidate_windows", [])}
    if candidate_names.get("funding_only_with_ohlcv_trades", {}).get("recommendation_status") == "viable_candidate":
        errors.append("funding-only candidate must not be viable without aggTrades overlap")
    if candidate_names.get("funding_and_open_interest_with_ohlcv_trades", {}).get("recommendation_status") == "viable_candidate":
        errors.append("funding+OI candidate must not be viable with current coverage")
    source_names = {item.get("source_name") for item in report.get("data_sources_inventory", [])}
    for required in {"OHLCV", "trades_aggTrades", "funding_rates", "open_interest", "other_derivatives_local"}:
        if required not in source_names:
            errors.append(f"missing data source inventory entry: {required}")
    for key in ["robust_edge_claimed", "strategy_validated", "backtest_performed", "actionable_signal_produced", "walk_forward_validated_for_trading"]:
        if report.get("findings", {}).get(key) is not False:
            errors.append(f"finding must be false: {key}")
    for key in ["no_trading", "no_paper_live", "no_orders", "no_backtest", "no_walk_forward", "no_strategy", "no_actionable_signal", "no_persistent_model", "no_sidecars", "no_zip_fingerprints", "no_new_data_download"]:
        if attestation.get(key) is not True:
            errors.append(f"attestation must confirm {key}=true")
    for key in ["api_key_used", "private_endpoint_used", "network_used"]:
        if attestation.get(key) is not False:
            errors.append(f"attestation must confirm {key}=false")
    if _contains_forbidden_zip_field(report):
        errors.append("V9.16 report contains forbidden ZIP hash or sidecar field")
    return errors


def _check_state(extract_root: Path) -> list[str]:
    errors: list[str] = []
    state = _read_json(extract_root / "reports/PROJECT_STATE.json")
    metrics = _read_json(extract_root / "reports/current/latest_metrics.json")
    for name, payload in {"PROJECT_STATE": state, "latest_metrics": metrics}.items():
        if payload.get("last_validated_version") != "V9.15":
            errors.append(f"{name} last_validated_version mismatch")
        if payload.get("candidate_version") != VERSION:
            errors.append(f"{name} candidate_version mismatch")
        if payload.get("candidate_status") != "pending_external_audit":
            errors.append(f"{name} candidate_status mismatch")
        if payload.get("network_used") is not False or payload.get("no_new_data_download") is not True:
            errors.append(f"{name} must confirm no network and no download")
        if payload.get("no_sidecars") is not True or payload.get("no_zip_fingerprints") is not True:
            errors.append(f"{name} must confirm no sidecars and no ZIP fingerprints")
        if payload.get("no_walk_forward") is not True:
            errors.append(f"{name} must confirm no walk-forward")
        if "recommended_next_version" in payload or "recommended_next_action" in payload:
            errors.append(f"{name} contains stale unversioned recommendation fields")
    return errors


def _contains_forbidden_zip_field(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            text = str(key).casefold()
            if text == "zip_sha256" or text.startswith("sidecar_"):
                return True
            if _contains_forbidden_zip_field(value):
                return True
    elif isinstance(payload, list):
        return any(_contains_forbidden_zip_field(item) for item in payload)
    return False


def _is_forbidden(name: str) -> bool:
    path = Path(name)
    if name.endswith(".sha256.json") or name.endswith(".sha256.txt"):
        return True
    if any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return True
    if path.name in FORBIDDEN_NAMES:
        return True
    if set(path.parts) & FORBIDDEN_PARTS:
        return True
    return path.suffix.casefold() in FORBIDDEN_SUFFIXES


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_reports(result: dict[str, Any]) -> None:
    report_dir = Path("reports/audit_lite")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "zip_audit_v9_16.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_audit_v9_16.md").write_text(f"# Audit ZIP V9.16\n\n- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n- Erreurs : `{result['errors']}`.\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
