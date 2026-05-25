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


VERSION = "V7.8"
SMOKE_JSON = Path("reports/audit_lite/zip_smoke_v7_8.json")
SMOKE_MD = Path("reports/audit_lite/zip_smoke_v7_8.md")
SAMPLE_ENTRIES = {
    "data/audit_lite/v7_8/features/timeframe=1m/sample.parquet",
    "data/audit_lite/v7_8/features/timeframe=5m/sample.parquet",
    "data/audit_lite/v7_8/features/timeframe=15m/sample.parquet",
    "data/audit_lite/v7_8/features/timeframe=1h/sample.parquet",
}
FORBIDDEN_SAFETY_TRUE = ["trading_enabled", "orders_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled", "ml_enabled", "labels_enabled", "dataset_enabled"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    result = smoke_zip(Path(args.zip_path).resolve())
    _write_reports(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        raise SystemExit(1)


def smoke_zip(zip_path: Path) -> dict[str, Any]:
    start = time.perf_counter()
    errors: list[str] = []
    warnings: list[str] = []
    collect_only: dict[str, Any] = {"executed": False}
    if not zip_path.exists():
        return _result(zip_path, errors=[f"missing zip: {zip_path}"], warnings=warnings, start=start, collect_only=collect_only)
    with tempfile.TemporaryDirectory(prefix="galapagos_v7_8_smoke_") as tmp:
        target = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(target)
        errors.extend(_check_forbidden_files(target))
        sys.path.insert(0, str(target / "src"))
        errors.extend(_check_imports())
        errors.extend(_check_reports(target))
        errors.extend(_check_samples(target))
        collect_only = _run_pytest_collect_only(target)
        if collect_only["returncode"] != 0:
            errors.append("pytest collect-only failed inside extracted ZIP")
    return _result(zip_path, errors=errors, warnings=warnings, start=start, collect_only=collect_only)


def _check_imports() -> list[str]:
    errors: list[str] = []
    for module in [
        "galapagos.features.ohlcv_trades_90d",
        "galapagos.features.ohlcv_trades_90d_quality",
        "galapagos.features.ohlcv_trades_90d_schemas",
        "galapagos.features.ohlcv_trades_90d_validation",
    ]:
        try:
            importlib.import_module(module)
        except Exception as exc:
            errors.append(f"import failed for {module}: {exc}")
    return errors


def _check_reports(root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = root / "reports/manifests/ohlcv_trades_90d_feature_store_v7_8_manifest.json"
    report_path = root / "reports/features/ohlcv_trades_90d_feature_store_v7_8.json"
    for path in [manifest_path, report_path]:
        if not path.exists():
            errors.append(f"missing V7.8 report in ZIP: {path.relative_to(root).as_posix()}")
    if manifest_path.exists() and report_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if manifest != report:
            errors.append("smoke V7.8 manifest/report mismatch")
        if manifest.get("version") != VERSION or manifest.get("status") != "PASS":
            errors.append("smoke V7.8 manifest version/status mismatch")
        safety = manifest.get("safety", {})
        for key in FORBIDDEN_SAFETY_TRUE:
            if safety.get(key) is not False:
                errors.append(f"smoke V7.8 safety flag must be false: {key}")
    return errors


def _check_samples(root: Path) -> list[str]:
    errors: list[str] = []
    schema_module = importlib.import_module("galapagos.features.ohlcv_trades_90d_schemas")
    for sample_entry in SAMPLE_ENTRIES:
        path = root / sample_entry
        if not path.exists():
            errors.append(f"missing V7.8 feature sample: {sample_entry}")
            continue
        frame = pd.read_parquet(path, engine="pyarrow")
        if list(frame.columns) != schema_module.OHLCV_TRADES_FEATURE_COLUMNS_V7_8:
            errors.append(f"V7.8 feature sample schema mismatch: {sample_entry}")
        if len(frame) == 0:
            errors.append(f"V7.8 feature sample is empty: {sample_entry}")
        forbidden_exact = {"future_return", "future_close", "label", "target", "prediction", "signal", "trading_signal", "order", "pnl", "backtest"}
        present = [column for column in frame.columns if column.casefold() in forbidden_exact]
        if present:
            errors.append(f"forbidden sample columns in {sample_entry}: {present}")
    return errors


def _check_forbidden_files(root: Path) -> list[str]:
    errors: list[str] = []
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
        if path.suffix.casefold() in {".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".zip"}:
            errors.append(f"forbidden binary artifact found: {relative}")
        if path.suffix == ".parquet" and relative not in SAMPLE_ENTRIES:
            errors.append(f"forbidden full parquet found: {relative}")
    return errors


def _is_forbidden_pytest_collectible_script(relative: str) -> bool:
    path = Path(relative)
    if len(path.parts) != 2 or path.parts[0] != "scripts" or path.suffix != ".py":
        return False
    return path.name.startswith("test_") or path.name.endswith("_test.py")


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
        "# Smoke ZIP V7.8",
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
