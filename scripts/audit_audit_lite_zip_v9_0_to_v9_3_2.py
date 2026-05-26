from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


TIMEFRAMES = ["1m", "5m", "15m", "1h"]
ZIP_NAME = "projet-galapagos-v9.0-to-v9.3.2-audit-lite.zip"
VERSION_SCOPE = "V9.0_to_V9.3.2"

REQUIRED_FILES = [
    "scripts/_bootstrap.py",
    "scripts/release_audit_lite_zip_v9_0_to_v9_3_2.py",
    "scripts/audit_audit_lite_zip_v9_0_to_v9_3_2.py",
    "scripts/smoke_audit_lite_zip_v9_0_to_v9_3_2.py",
    "reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json",
    "reports/features/refined_ohlcv_trades_feature_store_v9_0.json",
    "reports/features/refined_ohlcv_trades_feature_store_v9_0.md",
    "reports/manifests/refined_ohlcv_trades_offline_supervised_dataset_v9_1_manifest.json",
    "reports/datasets/refined_ohlcv_trades_offline_supervised_dataset_v9_1.json",
    "reports/datasets/refined_ohlcv_trades_offline_supervised_dataset_v9_1.md",
    "reports/datasets/refined_ohlcv_trades_offline_supervised_dataset_v9_1_datacard.md",
    "reports/manifests/refined_ohlcv_trades_offline_ml_research_v9_2_manifest.json",
    "reports/ml/refined_ohlcv_trades_offline_ml_research_v9_2.json",
    "reports/ml/refined_ohlcv_trades_offline_ml_research_v9_2.md",
    "reports/ml/refined_ohlcv_trades_offline_research_scores_v9_2.json",
    "reports/ml/refined_ohlcv_trades_offline_research_scores_v9_2.md",
    "reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json",
    "reports/ml/refined_strict_walk_forward_validation_v9_3.json",
    "reports/ml/refined_strict_walk_forward_validation_v9_3.md",
    "reports/ml/refined_strict_walk_forward_scores_v9_3.json",
    "reports/ml/refined_strict_walk_forward_scores_v9_3.md",
    "reports/audit_lite/v9_0_to_v9_3_2_artifact_inventory.json",
    "reports/audit_lite/v9_0_to_v9_3_2_artifact_inventory.md",
    "reports/audit_lite/v9_0_to_v9_3_2_full_local_validation_attestation.json",
    "reports/audit_lite/v9_0_to_v9_3_2_full_local_validation_attestation.md",
    "reports/audit_lite/v9_0_to_v9_3_2_parquet_summary.json",
    "reports/audit_lite/v9_0_to_v9_3_2_parquet_summary.md",
    "reports/audit_lite/zip_size_report_v9_0_to_v9_3_2.json",
    "reports/audit_lite/zip_size_report_v9_0_to_v9_3_2.md",
    "reports/manifests/max_history_label_factory_v5_2_manifest.json",
    "reports/manifests/ohlcv_trades_feature_audit_v8_9_manifest.json",
    "reports/features/ohlcv_trades_feature_selection_v8_9.json",
    "reports/features/ohlcv_trades_feature_audit_v8_9.json",
    "reports/manifests/ohlcv_trades_1y_feature_store_v8_3_manifest.json",
    "reports/features/ohlcv_trades_1y_feature_store_v8_3.json",
    "reports/manifests/ohlcv_trades_1y_offline_supervised_dataset_v8_4_manifest.json",
    "reports/manifests/ohlcv_trades_1y_offline_ml_research_v8_5_manifest.json",
    "reports/manifests/strict_walk_forward_validation_v8_7_manifest.json",
    "reports/research_decisions/v8_8_research_decision_gate.json",
    "docs/refined_ohlcv_trades_feature_store_v9_0.md",
    "docs/refined_ohlcv_trades_offline_supervised_dataset_v9_1.md",
    "docs/refined_ohlcv_trades_offline_ml_research_v9_2.md",
    "docs/refined_strict_walk_forward_validation_v9_3.md",
    "reports/PROJECT_STATE.json",
    "reports/PROJECT_STATE.md",
    "reports/current/latest_metrics.json",
    "reports/current/latest_metrics.md",
    "reports/current/latest_summary.md",
    "README.md",
    "pyproject.toml",
    "tests/features/test_refined_ohlcv_trades_features_v9_0.py",
    "tests/validation/test_refined_ohlcv_trades_feature_store_v9_0_validator.py",
    "tests/datasets/test_refined_ohlcv_trades_offline_supervised_dataset_v9_1.py",
    "tests/validation/test_refined_ohlcv_trades_offline_supervised_dataset_v9_1_validator.py",
    "tests/ml/test_refined_ohlcv_trades_offline_ml_research_v9_2.py",
    "tests/validation/test_refined_ohlcv_trades_offline_ml_research_v9_2_validator.py",
    "tests/ml/test_refined_strict_walk_forward_validation_v9_3.py",
    "tests/validation/test_refined_strict_walk_forward_validation_v9_3_validator.py",
    "tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_2.py",
]

REQUIRED_SAMPLE_PATTERNS = [
    "data/audit_lite/v9_0_to_v9_3/features/timeframe={timeframe}/features_sample.parquet",
    "data/audit_lite/v9_0_to_v9_3/datasets/timeframe={timeframe}/dataset_sample.parquet",
    "data/audit_lite/v9_0_to_v9_3/ml_scores/timeframe={timeframe}/ml-scores_sample.parquet",
    "data/audit_lite/v9_0_to_v9_3/walk_forward_scores/timeframe={timeframe}/walk_forward_scores_sample.parquet",
    "data/audit_lite/v9_0_to_v9_3/folds/timeframe={timeframe}/folds_sample.parquet",
]

FORBIDDEN_PREFIXES = [
    "data/research/",
    "reports/backtests/",
    "reports/strategies/",
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
    ".git/",
    ".venv/",
]
FORBIDDEN_PARTS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_NAMES = {".DS_Store", ".env"}
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".zip", ".pem", ".key"}
FORBIDDEN_SAMPLE_COLUMNS = {
    "prediction",
    "predicted",
    "model_score",
    "score_ml",
    "alpha",
    "signal",
    "trading_signal",
    "strategy",
    "order",
    "trade_decision",
    "position_size",
    "pnl",
    "profit",
    "backtest",
    "execution",
    "live",
    "paper_live",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    zip_path = Path(args.zip_path).resolve()
    result = {"zip": str(zip_path), "passed": False, "errors": audit_zip(zip_path)}
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
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_3_2_audit_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            names = sorted(archive.namelist())
            archive.extractall(extract_root)
        required_samples = [pattern.format(timeframe=tf) for pattern in REQUIRED_SAMPLE_PATTERNS for tf in TIMEFRAMES]
        missing = [path for path in [*REQUIRED_FILES, *required_samples] if path not in names]
        if missing:
            errors.append(f"missing required files: {missing}")
        forbidden = [name for name in names if _is_forbidden(name)]
        if forbidden:
            errors.append(f"forbidden files present: {forbidden[:50]}")
        errors.extend(_check_inventory(extract_root, names, zip_path))
        errors.extend(_check_surfaces(extract_root))
        errors.extend(_check_manifests(extract_root))
        errors.extend(_check_samples(extract_root, required_samples))
    return errors


def _check_inventory(extract_root: Path, names: list[str], zip_path: Path) -> list[str]:
    errors: list[str] = []
    inventory = _read_json(extract_root / "reports/audit_lite/v9_0_to_v9_3_2_artifact_inventory.json")
    if inventory.get("version_scope") != VERSION_SCOPE:
        errors.append("inventory version_scope mismatch")
    if inventory.get("zip_name") != ZIP_NAME:
        errors.append("inventory zip_name mismatch")
    inventory_files = sorted(inventory.get("files", []))
    if inventory.get("files_count") != len(names):
        errors.append(f"inventory files_count mismatch: {inventory.get('files_count')} != {len(names)}")
    if inventory_files != names:
        errors.append("inventory files list does not match ZIP content exactly")
    checks = inventory.get("forbidden_absences_verified", {})
    for key, value in checks.items():
        if value is not True:
            errors.append(f"inventory forbidden absence failed: {key}")
    if inventory.get("business_results_recomputed") is not False:
        errors.append("inventory must state business_results_recomputed=false")
    if inventory.get("business_results_modified") is not False:
        errors.append("inventory must state business_results_modified=false")
    size_report = _read_json(extract_root / "reports/audit_lite/zip_size_report_v9_0_to_v9_3_2.json")
    if size_report.get("version_scope") != VERSION_SCOPE:
        errors.append("zip size report version_scope mismatch")
    if size_report.get("zip_name") != ZIP_NAME:
        errors.append("zip size report zip_name mismatch")
    if size_report.get("included_files") != len(names):
        errors.append("zip size report included_files mismatch")
    if zip_path.name == ZIP_NAME and size_report.get("zip_bytes") not in {zip_path.stat().st_size, inventory.get("zip_bytes")}:
        errors.append("zip size report bytes is not coherent with archive size")
    return errors


def _check_surfaces(extract_root: Path) -> list[str]:
    errors: list[str] = []
    project_state = _read_json(extract_root / "reports/PROJECT_STATE.json")
    latest_metrics = _read_json(extract_root / "reports/current/latest_metrics.json")
    latest_summary = (extract_root / "reports/current/latest_summary.md").read_text(encoding="utf-8")
    for label, payload in {"PROJECT_STATE": project_state, "latest_metrics": latest_metrics}.items():
        if payload.get("last_validated_version") != "V8.9.1":
            errors.append(f"{label} last_validated_version mismatch")
        if payload.get("candidate_version") != VERSION_SCOPE:
            errors.append(f"{label} candidate_version mismatch")
        if payload.get("candidate_status") != "pending_external_audit":
            errors.append(f"{label} candidate_status mismatch")
        for key in ["trading_enabled", "orders_enabled", "backtest_enabled", "strategy_enabled", "paper_live_enabled"]:
            if payload.get(key) is not False:
                errors.append(f"{label} safety flag must be false: {key}")
    if VERSION_SCOPE not in latest_summary or "V9.4" not in latest_summary:
        errors.append("latest_summary must mention V9.0_to_V9.3.2 and no V9.4 before external audit")
    return errors


def _check_manifests(extract_root: Path) -> list[str]:
    errors: list[str] = []
    v90 = _read_json(extract_root / "reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json")
    v91 = _read_json(extract_root / "reports/manifests/refined_ohlcv_trades_offline_supervised_dataset_v9_1_manifest.json")
    v92 = _read_json(extract_root / "reports/manifests/refined_ohlcv_trades_offline_ml_research_v9_2_manifest.json")
    v93 = _read_json(extract_root / "reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json")
    if not v90.get("selected_features"):
        errors.append("V9.0 selected_features must be non-empty")
    expected_safety = {
        "v9_0": {"dataset_enabled": False, "ml_enabled": False},
        "v9_1": {"dataset_enabled": True, "ml_enabled": False},
        "v9_2": {"dataset_enabled": True, "ml_enabled": True},
        "v9_3": {"dataset_enabled": True, "ml_enabled": True},
    }
    for name, manifest in {"v9_0": v90, "v9_1": v91, "v9_2": v92, "v9_3": v93}.items():
        safety = manifest.get("safety", {})
        for key in ["orders_enabled", "paper_live_enabled", "trading_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled", "private_endpoint_used", "api_key_used"]:
            if safety.get(key) is not False:
                errors.append(f"{name} safety flag must be false: {key}")
        for key, expected in expected_safety[name].items():
            if safety.get(key) is not expected:
                errors.append(f"{name} safety flag mismatch: {key}")
    findings = v93.get("findings", {})
    for key in ["robust_edge_claimed", "strategy_validated", "backtest_performed", "actionable_signal_produced", "walk_forward_validated_for_trading"]:
        if findings.get(key) is not False:
            errors.append(f"V9.3 finding must be false: {key}")
    attestation = _read_json(extract_root / "reports/audit_lite/v9_0_to_v9_3_2_full_local_validation_attestation.json")
    expected_attestation = {
        "version_scope": VERSION_SCOPE,
        "source_version_scope": "V9.0_to_V9.3",
        "correction_scope": "packaging_audit_lite_external_audit_fix_only",
        "no_trading": True,
        "no_backtest": True,
        "no_orders": True,
        "no_strategy": True,
        "no_persistent_model": True,
        "api_key_used": False,
        "private_endpoint_used": False,
        "business_results_recomputed": False,
        "business_results_modified": False,
    }
    for key, expected in expected_attestation.items():
        if attestation.get(key) != expected:
            errors.append(f"attestation mismatch for {key}: {attestation.get(key)}")
    return errors


def _check_samples(extract_root: Path, sample_paths: list[str]) -> list[str]:
    errors: list[str] = []
    for sample_path in sample_paths:
        path = extract_root / sample_path
        if not path.exists():
            continue
        frame = pd.read_parquet(path, engine="pyarrow")
        if frame.empty:
            errors.append(f"sample must not be empty: {sample_path}")
        forbidden = sorted(set(frame.columns) & FORBIDDEN_SAMPLE_COLUMNS)
        if forbidden:
            errors.append(f"forbidden columns in sample {sample_path}: {forbidden}")
    return errors


def _is_forbidden(name: str) -> bool:
    path = Path(name)
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
    (report_dir / "zip_audit_v9_0_to_v9_3_2.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_audit_v9_0_to_v9_3_2.md").write_text(
        "# Audit ZIP audit-lite V9.0 -> V9.3.2\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
