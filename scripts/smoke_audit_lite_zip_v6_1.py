from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd


VERSION = "V6.1"
SMOKE_JSON = Path("reports/audit_lite/zip_smoke_v6_1.json")
SMOKE_MD = Path("reports/audit_lite/zip_smoke_v6_1.md")
FORBIDDEN_SAFETY_TRUE = ["trading_enabled", "orders_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled", "ml_enabled"]
REQUIRED_SAFETY_TRUE = ["labels_enabled", "dataset_enabled"]


def smoke_zip(zip_path: Path) -> dict[str, Any]:
    start = time.perf_counter()
    errors: list[str] = []
    warnings: list[str] = []
    collect_only: dict[str, Any] = {"executed": False}
    if not zip_path.exists():
        return _result(zip_path, errors=[f"missing zip: {zip_path}"], warnings=warnings, start=start, collect_only=collect_only)
    with tempfile.TemporaryDirectory(prefix="galapagos_v6_1_smoke_") as tmp:
        target = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(target)
        errors.extend(_check_required_files(target))
        errors.extend(_check_forbidden_files(target))
        errors.extend(_check_imports(target))
        errors.extend(_check_reports(target))
        errors.extend(_check_samples(target))
        collect_only = _run_pytest_collect_only(target)
        if collect_only["returncode"] != 0:
            errors.append("pytest collect-only failed inside extracted ZIP")
    return _result(zip_path, errors=errors, warnings=warnings, start=start, collect_only=collect_only)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    result = smoke_zip(Path(args.zip_path).resolve())
    _write_reports(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


def _check_required_files(root: Path) -> list[str]:
    required = [
        "reports/manifests/advanced_ohlcv_offline_supervised_dataset_v6_1_manifest.json",
        "reports/datasets/advanced_ohlcv_offline_supervised_dataset_v6_1.json",
        "reports/datasets/advanced_ohlcv_offline_supervised_dataset_v6_1_datacard.md",
        "reports/audit_lite/v6_1_full_local_validation_attestation.json",
        "docs/advanced_ohlcv_offline_supervised_dataset_v6_1.md",
        "scripts/release_audit_lite_zip_v6_1.py",
        "scripts/audit_audit_lite_zip_v6_1.py",
        "scripts/smoke_audit_lite_zip_v6_1.py",
        "tests/datasets/test_advanced_ohlcv_offline_supervised_dataset_v6_1.py",
        "tests/validation/test_advanced_ohlcv_offline_supervised_dataset_v6_1_validator.py",
    ]
    for timeframe in ["1m", "5m", "15m", "1h"]:
        required.append(f"data/audit_lite/v6_1/datasets/timeframe={timeframe}/sample.parquet")
        required.append(f"data/audit_lite/v6_1/splits/timeframe={timeframe}/sample.parquet")
    return [f"missing smoke file: {relative}" for relative in required if not (root / relative).exists()]


def _check_forbidden_files(root: Path) -> list[str]:
    errors: list[str] = []
    allowed_parquet_prefixes = ("data/audit_lite/v6_1/datasets/", "data/audit_lite/v6_1/splits/")
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if _is_forbidden_pytest_collectible_script(relative):
            errors.append(f"forbidden pytest-collectible script found: {relative}")
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            errors.append(f"forbidden cache artifact found: {relative}")
        if relative.startswith(("data/raw/", "data/research/", "reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/", "checkpoints/")):
            errors.append(f"forbidden runtime artifact found: {relative}")
        if path.suffix.casefold() in {".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt"}:
            errors.append(f"forbidden persistent model artifact found: {relative}")
        if relative.endswith(".parquet") and not relative.startswith(allowed_parquet_prefixes):
            errors.append(f"forbidden non-sample parquet found: {relative}")
    return errors


def _is_forbidden_pytest_collectible_script(relative: str) -> bool:
    path = Path(relative)
    if len(path.parts) != 2 or path.parts[0] != "scripts" or path.suffix != ".py":
        return False
    name = path.name
    return name.startswith("test_") or name.endswith("_test.py")


def _check_imports(root: Path) -> list[str]:
    sys.path.insert(0, str(root / "src"))
    errors: list[str] = []
    for module in [
        "galapagos.datasets.advanced_ohlcv_window",
        "galapagos.datasets.advanced_ohlcv_window_quality",
        "galapagos.datasets.advanced_ohlcv_window_validation",
        "galapagos.datasets.advanced_ohlcv_window_datacard",
        "galapagos.datasets.schemas",
    ]:
        try:
            importlib.import_module(module)
        except Exception as exc:  # pragma: no cover - smoke diagnostic
            errors.append(f"import failed for {module}: {exc}")
    return errors


def _check_samples(root: Path) -> list[str]:
    errors: list[str] = []
    schema_module = importlib.import_module("galapagos.datasets.schemas")
    dataset_columns = schema_module.DATASET_COLUMNS_V6_1
    split_columns = schema_module.SPLIT_COLUMNS_V6_1
    forbidden_exact = {"prediction", "trading_signal", "order", "strategy", "pnl", "profit", "backtest", "model_score"}
    for timeframe in ["1m", "5m", "15m", "1h"]:
        dataset_path = root / "data" / "audit_lite" / "v6_1" / "datasets" / f"timeframe={timeframe}" / "sample.parquet"
        split_path = root / "data" / "audit_lite" / "v6_1" / "splits" / f"timeframe={timeframe}" / "sample.parquet"
        dataset = pd.read_parquet(dataset_path, engine="pyarrow")
        splits = pd.read_parquet(split_path, engine="pyarrow")
        if list(dataset.columns) != dataset_columns:
            errors.append(f"V6.1 dataset sample schema mismatch for {timeframe}")
        if list(splits.columns) != split_columns:
            errors.append(f"V6.1 split sample schema mismatch for {timeframe}")
        present = [column for column in dataset.columns if column.casefold() in forbidden_exact]
        if present:
            errors.append(f"forbidden sample columns for {timeframe}: {present}")
        if "macd_like_signal" not in dataset.columns:
            errors.append(f"V6.1 dataset sample missing macd_like_signal for {timeframe}")
    return errors


def _check_reports(root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = root / "reports/manifests/advanced_ohlcv_offline_supervised_dataset_v6_1_manifest.json"
    report_path = root / "reports/datasets/advanced_ohlcv_offline_supervised_dataset_v6_1.json"
    if manifest_path.exists() and report_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if manifest != report:
            errors.append("smoke V6.1 manifest/report mismatch")
        safety = manifest.get("safety", {})
        for key in FORBIDDEN_SAFETY_TRUE:
            if safety.get(key) is not False:
                errors.append(f"smoke V6.1 safety flag must be false: {key}")
        for key in REQUIRED_SAFETY_TRUE:
            if safety.get(key) is not True:
                errors.append(f"smoke V6.1 safety flag must be true: {key}")
        if manifest.get("advanced_feature_columns_count") != 158:
            errors.append("smoke V6.1 advanced_feature_columns_count mismatch")
    return errors


def _run_pytest_collect_only(root: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "executed": True,
        "command": "PYTHONPATH=src python -m pytest --collect-only -q",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def _result(zip_path: Path, *, errors: list[str], warnings: list[str], start: float, collect_only: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size if zip_path.exists() else 0,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "pytest_collect_only": collect_only,
        "smoke_duration_seconds": round(time.perf_counter() - start, 3),
    }


def _write_reports(result: dict[str, Any]) -> None:
    SMOKE_JSON.parent.mkdir(parents=True, exist_ok=True)
    SMOKE_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Smoke ZIP V6.1",
        "",
        f"- ZIP : `{result['zip_path']}`.",
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.",
        f"- Pytest collect-only : `{result['pytest_collect_only'].get('returncode') == 0}`.",
        f"- Duree : `{result['smoke_duration_seconds']}` secondes.",
        f"- Erreurs : `{len(result['errors'])}`.",
    ]
    SMOKE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
