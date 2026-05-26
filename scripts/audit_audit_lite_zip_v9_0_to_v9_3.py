from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


REQUIRED_FILES = [
    "reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json",
    "reports/manifests/refined_ohlcv_trades_offline_supervised_dataset_v9_1_manifest.json",
    "reports/manifests/refined_ohlcv_trades_offline_ml_research_v9_2_manifest.json",
    "reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json",
    "reports/features/refined_ohlcv_trades_feature_store_v9_0.json",
    "reports/datasets/refined_ohlcv_trades_offline_supervised_dataset_v9_1.json",
    "reports/ml/refined_ohlcv_trades_offline_ml_research_v9_2.json",
    "reports/ml/refined_strict_walk_forward_validation_v9_3.json",
    "reports/audit_lite/v9_0_to_v9_3_artifact_inventory.json",
    "reports/audit_lite/v9_0_to_v9_3_parquet_summary.json",
    "reports/audit_lite/v9_0_to_v9_3_full_local_validation_attestation.json",
    "reports/current/latest_summary.md",
    "reports/PROJECT_STATE.json",
    "README.md",
    "pyproject.toml",
]

REQUIRED_SAMPLES = [
    "data/audit_lite/v9_0_to_v9_3/features/timeframe=1m/features_sample.parquet",
    "data/audit_lite/v9_0_to_v9_3/datasets/timeframe=1m/dataset_sample.parquet",
    "data/audit_lite/v9_0_to_v9_3/ml_scores/timeframe=1m/ml-scores_sample.parquet",
    "data/audit_lite/v9_0_to_v9_3/walk_forward_scores/timeframe=1m/walk_forward_scores_sample.parquet",
    "data/audit_lite/v9_0_to_v9_3/folds/timeframe=1m/folds_sample.parquet",
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    zip_path = Path(args.zip_path).resolve()
    errors = audit_zip(zip_path)
    result = {"zip": str(zip_path), "passed": not errors, "errors": errors}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


def audit_zip(zip_path: Path) -> list[str]:
    errors: list[str] = []
    if not zip_path.exists():
        return [f"missing zip: {zip_path}"]
    if not zipfile.is_zipfile(zip_path):
        return [f"not a valid zip: {zip_path}"]
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_audit_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            names = sorted(archive.namelist())
            archive.extractall(extract_root)
        missing = [path for path in [*REQUIRED_FILES, *REQUIRED_SAMPLES] if path not in names]
        if missing:
            errors.append(f"missing required files: {missing}")
        forbidden = [
            name
            for name in names
            if _is_forbidden(name)
        ]
        if forbidden:
            errors.append(f"forbidden files present: {forbidden[:20]}")
        manifest = _read_json(extract_root / "reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json")
        if manifest.get("selected_features_count", 0) <= 0:
            errors.append("V9.0 selected_features_count must be positive")
        v93 = _read_json(extract_root / "reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json")
        findings = v93.get("findings", {})
        for key in ["robust_edge_claimed", "strategy_validated", "backtest_performed", "actionable_signal_produced", "walk_forward_validated_for_trading"]:
            if findings.get(key) is not False:
                errors.append(f"V9.3 finding must be false: {key}")
        safety = v93.get("safety", {})
        for key in ["orders_enabled", "paper_live_enabled", "trading_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled"]:
            if safety.get(key) is not False:
                errors.append(f"safety flag must be false: {key}")
        attestation = _read_json(extract_root / "reports/audit_lite/v9_0_to_v9_3_full_local_validation_attestation.json")
        for key in ["no_trading", "no_backtest", "no_orders", "no_strategy", "no_persistent_model"]:
            if attestation.get(key) is not True:
                errors.append(f"attestation flag must be true: {key}")
    return errors


def _is_forbidden(name: str) -> bool:
    if any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return True
    parts = set(Path(name).parts)
    if parts & FORBIDDEN_PARTS:
        return True
    suffix = Path(name).suffix.casefold()
    return suffix in FORBIDDEN_SUFFIXES


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
