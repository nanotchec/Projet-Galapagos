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
REQUIRED_FILES = [
    "scripts/_bootstrap.py",
    "scripts/release_audit_lite_zip_v9_0_to_v9_3_1.py",
    "scripts/audit_audit_lite_zip_v9_0_to_v9_3_1.py",
    "scripts/smoke_audit_lite_zip_v9_0_to_v9_3_1.py",
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
    "reports/audit_lite/v9_0_to_v9_3_full_local_validation_attestation.json",
    "reports/audit_lite/v9_0_to_v9_3_full_local_validation_attestation.md",
    "reports/audit_lite/v9_0_to_v9_3_artifact_inventory.json",
    "reports/audit_lite/v9_0_to_v9_3_artifact_inventory.md",
    "reports/audit_lite/v9_0_to_v9_3_parquet_summary.json",
    "reports/audit_lite/v9_0_to_v9_3_parquet_summary.md",
    "reports/audit_lite/zip_size_report_v9_0_to_v9_3.json",
    "reports/audit_lite/zip_size_report_v9_0_to_v9_3.md",
    "reports/manifests/max_history_label_factory_v5_2_manifest.json",
    "reports/manifests/ohlcv_trades_feature_audit_v8_9_manifest.json",
    "reports/features/ohlcv_trades_feature_selection_v8_9.json",
    "reports/features/ohlcv_trades_feature_audit_v8_9.json",
    "reports/manifests/ohlcv_trades_1y_feature_store_v8_3_manifest.json",
    "reports/features/ohlcv_trades_1y_feature_store_v8_3.json",
    "reports/manifests/ohlcv_trades_1y_offline_supervised_dataset_v8_4_manifest.json",
    "reports/manifests/ohlcv_trades_1y_offline_ml_research_v8_5_manifest.json",
    "reports/ml/ohlcv_trades_1y_offline_ml_research_v8_5.json",
    "reports/manifests/strict_walk_forward_validation_v8_7_manifest.json",
    "reports/ml/strict_walk_forward_validation_v8_7.json",
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
    "tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_1.py",
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
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".zip"}
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
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_3_1_audit_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            names = sorted(archive.namelist())
            archive.extractall(extract_root)
        required_samples = [
            pattern.format(timeframe=timeframe)
            for pattern in REQUIRED_SAMPLE_PATTERNS
            for timeframe in TIMEFRAMES
        ]
        missing = [path for path in [*REQUIRED_FILES, *required_samples] if path not in names]
        if missing:
            errors.append(f"missing required files: {missing}")
        forbidden = [name for name in names if _is_forbidden(name)]
        if forbidden:
            errors.append(f"forbidden files present: {forbidden[:20]}")
        errors.extend(_check_code_surfaces(names))
        errors.extend(_check_manifests(extract_root))
        errors.extend(_check_samples(extract_root, required_samples))
    return errors


def _check_code_surfaces(names: list[str]) -> list[str]:
    errors: list[str] = []
    for prefix in [
        "src/galapagos/features/",
        "src/galapagos/datasets/",
        "src/galapagos/ml/",
        "src/galapagos/validation/",
    ]:
        if not any(name.startswith(prefix) for name in names):
            errors.append(f"missing code surface: {prefix}")
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
        for key in ["orders_enabled", "paper_live_enabled", "trading_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled"]:
            if safety.get(key) is not False:
                errors.append(f"{name} safety flag must be false: {key}")
        for key, expected in expected_safety[name].items():
            if safety.get(key) is not expected:
                errors.append(f"{name} safety flag mismatch: {key}")
    findings = v93.get("findings", {})
    for key in [
        "robust_edge_claimed",
        "strategy_validated",
        "backtest_performed",
        "actionable_signal_produced",
        "walk_forward_validated_for_trading",
    ]:
        if key in findings and findings.get(key) is not False:
            errors.append(f"V9.3 finding must be false: {key}")
    attestation = _read_json(extract_root / "reports/audit_lite/v9_0_to_v9_3_full_local_validation_attestation.json")
    for key in ["no_trading", "no_backtest", "no_orders", "no_strategy", "no_persistent_model"]:
        if attestation.get(key) is not True:
            errors.append(f"attestation flag must be true: {key}")
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
    if any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return True
    parts = set(Path(name).parts)
    if parts & FORBIDDEN_PARTS:
        return True
    return Path(name).suffix.casefold() in FORBIDDEN_SUFFIXES


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_reports(result: dict[str, Any]) -> None:
    report_dir = Path("reports/audit_lite")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "zip_audit_v9_0_to_v9_3_1.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_audit_v9_0_to_v9_3_1.md").write_text(
        "# Audit ZIP audit-lite V9.0 -> V9.3.1\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
