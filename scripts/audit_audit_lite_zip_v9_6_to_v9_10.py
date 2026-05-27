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


VERSION_SCOPE = "V9.6_to_V9.10"
ZIP_NAME = "projet-galapagos-v9.6-to-v9.10-audit-lite.zip"
TIMEFRAMES = ["1m", "5m", "15m", "1h"]

REQUIRED_FILES = [
    "scripts/_bootstrap.py",
    "scripts/release_audit_lite_zip_v9_6_to_v9_10.py",
    "scripts/audit_audit_lite_zip_v9_6_to_v9_10.py",
    "scripts/smoke_audit_lite_zip_v9_6_to_v9_10.py",
    "scripts/run_refined_volatility_normalized_labels_v9_6.py",
    "scripts/validate_refined_volatility_normalized_labels_v9_6.py",
    "scripts/run_refined_volnorm_labels_dataset_v9_7.py",
    "scripts/validate_refined_volnorm_labels_dataset_v9_7.py",
    "scripts/run_refined_volnorm_labels_offline_ml_v9_8.py",
    "scripts/validate_refined_volnorm_labels_offline_ml_v9_8.py",
    "scripts/run_refined_volnorm_strict_walk_forward_v9_9.py",
    "scripts/validate_refined_volnorm_strict_walk_forward_v9_9.py",
    "scripts/run_refined_volnorm_research_decision_gate_v9_10.py",
    "scripts/validate_refined_volnorm_research_decision_gate_v9_10.py",
    "reports/manifests/refined_volatility_normalized_labels_v9_6_manifest.json",
    "reports/labels/refined_volatility_normalized_labels_v9_6.json",
    "reports/labels/refined_volatility_normalized_labels_v9_6.md",
    "reports/labels/refined_volatility_normalized_labels_v9_6_datacard.md",
    "reports/manifests/refined_volnorm_labels_dataset_v9_7_manifest.json",
    "reports/datasets/refined_volnorm_labels_dataset_v9_7.json",
    "reports/datasets/refined_volnorm_labels_dataset_v9_7.md",
    "reports/datasets/refined_volnorm_labels_dataset_v9_7_datacard.md",
    "reports/manifests/refined_volnorm_labels_offline_ml_v9_8_manifest.json",
    "reports/ml/refined_volnorm_labels_offline_ml_v9_8.json",
    "reports/ml/refined_volnorm_labels_offline_ml_v9_8.md",
    "reports/ml/refined_volnorm_labels_offline_scores_v9_8.json",
    "reports/ml/refined_volnorm_labels_offline_scores_v9_8.md",
    "reports/manifests/refined_volnorm_strict_walk_forward_v9_9_manifest.json",
    "reports/ml/refined_volnorm_strict_walk_forward_v9_9.json",
    "reports/ml/refined_volnorm_strict_walk_forward_v9_9.md",
    "reports/ml/refined_volnorm_strict_walk_forward_scores_v9_9.json",
    "reports/ml/refined_volnorm_strict_walk_forward_scores_v9_9.md",
    "reports/manifests/refined_volnorm_research_decision_gate_v9_10_manifest.json",
    "reports/research_decisions/refined_volnorm_research_decision_gate_v9_10.json",
    "reports/research_decisions/refined_volnorm_research_decision_gate_v9_10.md",
    "docs/refined_volatility_normalized_labels_v9_6.md",
    "docs/refined_volnorm_labels_dataset_v9_7.md",
    "docs/refined_volnorm_labels_offline_ml_v9_8.md",
    "docs/refined_volnorm_strict_walk_forward_v9_9.md",
    "docs/refined_volnorm_research_decision_gate_v9_10.md",
    "reports/audit_lite/v9_6_to_v9_10_command_results.json",
    "reports/audit_lite/v9_6_to_v9_10_command_results.md",
    "reports/audit_lite/v9_6_to_v9_10_full_local_validation_attestation.json",
    "reports/audit_lite/v9_6_to_v9_10_full_local_validation_attestation.md",
    "reports/audit_lite/v9_6_to_v9_10_artifact_inventory.json",
    "reports/audit_lite/v9_6_to_v9_10_artifact_inventory.md",
    "reports/audit_lite/v9_6_to_v9_10_parquet_summary.json",
    "reports/audit_lite/v9_6_to_v9_10_parquet_summary.md",
    "reports/audit_lite/zip_size_report_v9_6_to_v9_10.json",
    "reports/audit_lite/zip_size_report_v9_6_to_v9_10.md",
    "reports/audit_lite/zip_audit_v9_6_to_v9_10.json",
    "reports/audit_lite/zip_smoke_v9_6_to_v9_10.json",
    "reports/research_decisions/refined_research_decision_gate_v9_4.json",
    "reports/research_decisions/alternative_label_design_audit_v9_5.json",
    "reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json",
    "reports/manifests/refined_ohlcv_trades_offline_supervised_dataset_v9_1_manifest.json",
    "reports/manifests/refined_ohlcv_trades_offline_ml_research_v9_2_manifest.json",
    "reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json",
    "reports/PROJECT_STATE.json",
    "reports/PROJECT_STATE.md",
    "reports/current/latest_metrics.json",
    "reports/current/latest_metrics.md",
    "reports/current/latest_summary.md",
    "README.md",
    "pyproject.toml",
    "tests/labels/test_refined_volatility_normalized_labels_v9_6.py",
    "tests/validation/test_refined_volatility_normalized_labels_v9_6_validator.py",
    "tests/datasets/test_refined_volnorm_labels_dataset_v9_7.py",
    "tests/validation/test_refined_volnorm_labels_dataset_v9_7_validator.py",
    "tests/ml/test_refined_volnorm_labels_offline_ml_v9_8.py",
    "tests/validation/test_refined_volnorm_labels_offline_ml_v9_8_validator.py",
    "tests/ml/test_refined_volnorm_strict_walk_forward_v9_9.py",
    "tests/validation/test_refined_volnorm_strict_walk_forward_v9_9_validator.py",
    "tests/research/test_refined_volnorm_research_decision_gate_v9_10.py",
    "tests/validation/test_refined_volnorm_research_decision_gate_v9_10_validator.py",
]

REQUIRED_SAMPLE_PATTERNS = [
    "data/audit_lite/v9_6_to_v9_10/labels/timeframe={timeframe}/labels_sample.parquet",
    "data/audit_lite/v9_6_to_v9_10/datasets/timeframe={timeframe}/dataset_sample.parquet",
    "data/audit_lite/v9_6_to_v9_10/ml_scores/timeframe={timeframe}/ml-scores_sample.parquet",
    "data/audit_lite/v9_6_to_v9_10/walk_forward_scores/timeframe={timeframe}/walk_forward_scores_sample.parquet",
    "data/audit_lite/v9_6_to_v9_10/folds/timeframe={timeframe}/folds_sample.parquet",
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
    "model_score",
    "signal",
    "trading_signal",
    "order",
    "pnl",
    "sharpe",
    "drawdown",
    "equity_curve",
    "profit_factor",
    "backtest",
    "position_size",
    "strategy",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    zip_path = Path(args.zip_path).resolve()
    result = {"version_scope": VERSION_SCOPE, "zip": str(zip_path), "passed": False, "errors": audit_zip(zip_path)}
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
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_6_to_v9_10_audit_") as tmp:
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
        errors.extend(_check_state_surfaces(extract_root))
        errors.extend(_check_reports(extract_root))
        errors.extend(_check_samples(extract_root, required_samples))
    return errors


def _check_inventory(extract_root: Path, names: list[str], zip_path: Path) -> list[str]:
    errors: list[str] = []
    inventory = _read_json(extract_root / "reports/audit_lite/v9_6_to_v9_10_artifact_inventory.json")
    if inventory.get("version_scope") != VERSION_SCOPE:
        errors.append("inventory version_scope mismatch")
    if inventory.get("zip_name") != ZIP_NAME:
        errors.append("inventory zip_name mismatch")
    if inventory.get("files_count") != len(names):
        errors.append(f"inventory files_count mismatch: {inventory.get('files_count')} != {len(names)}")
    if sorted(inventory.get("files", [])) != names:
        errors.append("inventory files list does not match ZIP content exactly")
    if inventory.get("zip_bytes") != zip_path.stat().st_size:
        errors.append("inventory zip_bytes mismatch")
    if inventory.get("sidecars_created") is not False or inventory.get("zip_fingerprints_created") is not False:
        errors.append("inventory must confirm no sidecars and no ZIP fingerprints")
    if "zip_sha256" in inventory or any(key.startswith("sidecar_") for key in inventory):
        errors.append("inventory contains forbidden ZIP fingerprint or sidecar field")
    for key, value in inventory.get("forbidden_absences_verified", {}).items():
        if value is not True:
            errors.append(f"inventory forbidden absence failed: {key}")
    size_report = _read_json(extract_root / "reports/audit_lite/zip_size_report_v9_6_to_v9_10.json")
    if size_report.get("included_files") != len(names):
        errors.append("zip size report included_files mismatch")
    if size_report.get("zip_bytes") != zip_path.stat().st_size:
        errors.append("zip size report zip_bytes mismatch")
    if "zip_sha256" in size_report or any(key.startswith("sidecar_") for key in size_report):
        errors.append("zip size report contains forbidden ZIP fingerprint or sidecar field")
    return errors


def _check_state_surfaces(extract_root: Path) -> list[str]:
    errors: list[str] = []
    project_state = _read_json(extract_root / "reports/PROJECT_STATE.json")
    latest_metrics = _read_json(extract_root / "reports/current/latest_metrics.json")
    latest_summary = (extract_root / "reports/current/latest_summary.md").read_text(encoding="utf-8")
    for label, payload in {"PROJECT_STATE": project_state, "latest_metrics": latest_metrics}.items():
        if payload.get("last_validated_version") != "V9.5":
            errors.append(f"{label} last_validated_version mismatch")
        if payload.get("candidate_version") != VERSION_SCOPE:
            errors.append(f"{label} candidate_version mismatch")
        if payload.get("candidate_status") != "pending_external_audit":
            errors.append(f"{label} candidate_status mismatch")
        for key in ["trading_enabled", "orders_enabled", "backtest_performed", "strategy_enabled", "paper_live_enabled", "api_key_used", "private_endpoint_used"]:
            if payload.get(key) is not False:
                errors.append(f"{label} safety flag must be false: {key}")
        if payload.get("sidecars_created") is not False or payload.get("zip_fingerprints_created") is not False:
            errors.append(f"{label} must confirm no sidecars and no ZIP fingerprints")
    if VERSION_SCOPE not in latest_summary:
        errors.append("latest summary must mention V9.6_to_V9.10")
    return errors


def _check_reports(extract_root: Path) -> list[str]:
    errors: list[str] = []
    v96 = _read_json(extract_root / "reports/labels/refined_volatility_normalized_labels_v9_6.json")
    v97 = _read_json(extract_root / "reports/datasets/refined_volnorm_labels_dataset_v9_7.json")
    v98 = _read_json(extract_root / "reports/ml/refined_volnorm_labels_offline_ml_v9_8.json")
    v99 = _read_json(extract_root / "reports/ml/refined_volnorm_strict_walk_forward_v9_9.json")
    v910 = _read_json(extract_root / "reports/research_decisions/refined_volnorm_research_decision_gate_v9_10.json")
    attestation = _read_json(extract_root / "reports/audit_lite/v9_6_to_v9_10_full_local_validation_attestation.json")
    if v96.get("decision") != "label_factory_candidate_created_volatility_normalized":
        errors.append("V9.6 decision mismatch")
    if v97.get("decision") != "dataset_created_with_volnorm_labels":
        errors.append("V9.7 decision mismatch")
    if v98.get("decision") != "offline_ml_completed_but_close_to_shuffled_labels":
        errors.append("V9.8 decision mismatch")
    if v99.get("decision") != "strict_walk_forward_completed_but_close_to_shuffled_labels":
        errors.append("V9.9 decision mismatch")
    if v910.get("research_decision") != "backtest_not_justified_refine_labels_again":
        errors.append("V9.10 decision mismatch")
    for report_name, report in {"v9_6": v96, "v9_8": v98, "v9_9": v99, "v9_10": v910}.items():
        for key in ["robust_edge_claimed", "strategy_validated", "backtest_performed", "actionable_signal_produced", "walk_forward_validated_for_trading"]:
            if report.get("findings", {}).get(key) is not False:
                errors.append(f"{report_name} finding must be false: {key}")
        safety = report.get("safety", {})
        for key in ["api_key_used", "private_endpoint_used", "orders_enabled", "paper_live_enabled", "trading_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled"]:
            if safety.get(key) is not False:
                errors.append(f"{report_name} safety flag must be false: {key}")
    if v96.get("leakage_guard", {}).get("passed") is not True:
        errors.append("V9.6 leakage guard must pass")
    if v97.get("leakage_guard", {}).get("passed") is not True:
        errors.append("V9.7 leakage guard must pass")
    if v98.get("metric_forbidden_scan", {}).get("passed") is not True:
        errors.append("V9.8 metric forbidden scan must pass")
    if v99.get("metric_forbidden_scan", {}).get("passed") is not True:
        errors.append("V9.9 metric forbidden scan must pass")
    if v910.get("metric_forbidden_scan", {}).get("passed") is not True:
        errors.append("V9.10 metric forbidden scan must pass")
    for key in ["no_trading", "no_paper_live", "no_orders", "no_backtest", "no_strategy", "no_actionable_signal", "no_persistent_model"]:
        if attestation.get(key) is not True:
            errors.append(f"attestation must confirm {key}=true")
    for key in ["api_key_used", "private_endpoint_used", "sidecars_created", "zip_fingerprints_created"]:
        if attestation.get(key) is not False:
            errors.append(f"attestation must confirm {key}=false")
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
    (report_dir / "zip_audit_v9_6_to_v9_10.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_audit_v9_6_to_v9_10.md").write_text(
        "# Audit ZIP audit-lite V9.6 -> V9.10\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
