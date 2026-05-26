from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


TIMEFRAMES = ["1m", "5m", "15m", "1h"]
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
    result = smoke_zip(zip_path)
    _write_reports(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


def smoke_zip(zip_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_3_1_smoke_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_root)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(extract_root / "src")
        sys.path.insert(0, str(extract_root / "src"))
        errors.extend(_import_required_modules(extract_root, env))
        try:
            errors.extend(_check_manifests_and_reports(extract_root))
            errors.extend(_check_sample_schemas(extract_root))
        finally:
            if str(extract_root / "src") in sys.path:
                sys.path.remove(str(extract_root / "src"))
        collect = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q"],
            cwd=extract_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if collect.returncode != 0:
            errors.append(f"pytest collect-only failed: {collect.stdout[-1000:]} {collect.stderr[-1000:]}")
    return {"zip": str(zip_path), "passed": not errors, "errors": errors}


def _import_required_modules(extract_root: Path, env: dict[str, str]) -> list[str]:
    errors: list[str] = []
    modules = [
        "galapagos.features.refined_ohlcv_trades",
        "galapagos.features.refined_ohlcv_trades_schemas",
        "galapagos.datasets.refined_ohlcv_trades_window",
        "galapagos.datasets.schemas",
        "galapagos.ml.refined_ohlcv_trades_window",
        "galapagos.ml.refined_strict_walk_forward",
        "galapagos.ml.schemas",
        "galapagos.validation.manifests",
    ]
    for module in modules:
        completed = subprocess.run(
            ["python", "-c", f"import {module}"],
            cwd=extract_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            errors.append(f"import failed for {module}: {completed.stderr.strip()}")
    return errors


def _check_manifests_and_reports(extract_root: Path) -> list[str]:
    errors: list[str] = []
    v90 = _read_json(extract_root / "reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json")
    v91 = _read_json(extract_root / "reports/manifests/refined_ohlcv_trades_offline_supervised_dataset_v9_1_manifest.json")
    v92 = _read_json(extract_root / "reports/manifests/refined_ohlcv_trades_offline_ml_research_v9_2_manifest.json")
    v93 = _read_json(extract_root / "reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json")
    if v90.get("selected_features_count") != 18:
        errors.append("V9.0 selected_features_count must be 18")
    if not v90.get("selected_features"):
        errors.append("V9.0 selected_features must be non-empty")
    for name, manifest in {"v9_0": v90, "v9_1": v91, "v9_2": v92, "v9_3": v93}.items():
        safety = manifest.get("safety", {})
        for key in ["orders_enabled", "paper_live_enabled", "trading_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled"]:
            if safety.get(key) is not False:
                errors.append(f"{name} safety flag must be false: {key}")
    findings = v93.get("findings", {})
    for key in ["robust_edge_claimed", "strategy_validated", "backtest_performed", "actionable_signal_produced", "walk_forward_validated_for_trading"]:
        if findings.get(key) is not False:
            errors.append(f"V9.3 finding must be false: {key}")
    return errors


def _check_sample_schemas(extract_root: Path) -> list[str]:
    from galapagos.datasets.schemas import DATASET_COLUMNS_V9_1
    from galapagos.features.refined_ohlcv_trades_schemas import REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0
    from galapagos.ml.schemas import ML_SCORE_COLUMNS_V9_2, ML_SCORE_COLUMNS_V9_3, WALK_FORWARD_FOLD_COLUMNS_V9_3

    errors: list[str] = []
    specs = [
        ("features", "features_sample.parquet", REFINED_OHLCV_TRADES_FEATURE_COLUMNS_V9_0),
        ("datasets", "dataset_sample.parquet", DATASET_COLUMNS_V9_1),
        ("ml_scores", "ml-scores_sample.parquet", ML_SCORE_COLUMNS_V9_2),
        ("walk_forward_scores", "walk_forward_scores_sample.parquet", ML_SCORE_COLUMNS_V9_3),
        ("folds", "folds_sample.parquet", WALK_FORWARD_FOLD_COLUMNS_V9_3),
    ]
    for folder, filename, expected_columns in specs:
        for timeframe in TIMEFRAMES:
            path = extract_root / "data/audit_lite/v9_0_to_v9_3" / folder / f"timeframe={timeframe}" / filename
            if not path.exists():
                errors.append(f"missing sample: {path.relative_to(extract_root).as_posix()}")
                continue
            frame = pd.read_parquet(path, engine="pyarrow")
            if frame.empty:
                errors.append(f"empty sample: {path.relative_to(extract_root).as_posix()}")
            if list(frame.columns) != expected_columns:
                errors.append(f"schema mismatch for {path.relative_to(extract_root).as_posix()}")
            forbidden = sorted(set(frame.columns) & FORBIDDEN_SAMPLE_COLUMNS)
            if forbidden:
                errors.append(f"forbidden columns in {path.relative_to(extract_root).as_posix()}: {forbidden}")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_reports(result: dict[str, Any]) -> None:
    report_dir = Path("reports/audit_lite")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "zip_smoke_v9_0_to_v9_3_1.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_smoke_v9_0_to_v9_3_1.md").write_text(
        "# Smoke audit-lite V9.0 -> V9.3.1\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n"
        "- Le smoke est sample-only et ne lance pas les tests full qui exigent les Parquet complets.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
