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


VERSION = "V8.2"
SMOKE_JSON = Path("reports/audit_lite/zip_smoke_v8_2.json")
SMOKE_MD = Path("reports/audit_lite/zip_smoke_v8_2.md")
SAMPLE_ENTRY = "data/audit_lite/v8_2/trades/sample.parquet"
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
    with tempfile.TemporaryDirectory(prefix="galapagos_v8_2_smoke_") as tmp:
        target = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(target)
        errors.extend(_check_forbidden_files(target))
        sys.path.insert(0, str(target / "src"))
        errors.extend(_check_imports())
        errors.extend(_check_reports(target))
        errors.extend(_check_sample(target))
        collect_only = _run_pytest_collect_only(target)
        if collect_only["returncode"] != 0:
            errors.append("pytest collect-only failed inside extracted ZIP")
    return _result(zip_path, errors=errors, warnings=warnings, start=start, collect_only=collect_only)


def _check_imports() -> list[str]:
    errors: list[str] = []
    for module in [
        "galapagos.data.public_trades.discovery",
        "galapagos.data.public_trades.ingestion",
        "galapagos.data.public_trades.quality",
        "galapagos.data.public_trades.schemas",
        "galapagos.data.public_trades.validation",
        "galapagos.data.public_trades.one_year_window",
        "galapagos.data.public_trades.one_year_window_quality",
        "galapagos.data.public_trades.one_year_window_validation",
    ]:
        try:
            importlib.import_module(module)
        except Exception as exc:
            errors.append(f"import failed for {module}: {exc}")
    return errors


def _check_reports(root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = root / "reports/manifests/public_trades_1y_window_v8_2_manifest.json"
    report_path = root / "reports/data_quality/public_trades_1y_window_v8_2.json"
    discovery_path = root / "reports/data_quality/public_trades_1y_window_v8_2_discovery.json"
    for path in [manifest_path, report_path, discovery_path]:
        if not path.exists():
            errors.append(f"missing V8.2 report in ZIP: {path.relative_to(root).as_posix()}")
    if manifest_path.exists() and report_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if manifest != report:
            errors.append("smoke V8.2 manifest/report mismatch")
        if manifest.get("version") != VERSION or manifest.get("status") != "PASS":
            errors.append("smoke V8.2 manifest version/status mismatch")
        safety = manifest.get("safety", {})
        for key in FORBIDDEN_SAFETY_TRUE:
            if safety.get(key) is not False:
                errors.append(f"smoke V8.2 safety flag must be false: {key}")
    return errors


def _check_sample(root: Path) -> list[str]:
    errors: list[str] = []
    schema_module = importlib.import_module("galapagos.data.public_trades.schemas")
    path = root / SAMPLE_ENTRY
    if not path.exists():
        return [f"missing V8.2 trades sample: {SAMPLE_ENTRY}"]
    frame = pd.read_parquet(path, engine="pyarrow")
    if list(frame.columns) != schema_module.AGG_TRADE_COLUMNS_V8_2:
        errors.append("V8.2 trades sample schema mismatch")
    if len(frame) == 0:
        errors.append("V8.2 trades sample is empty")
    forbidden_exact = {"signal", "trading_signal", "order", "strategy", "pnl", "profit", "prediction"}
    present = [column for column in frame.columns if column.casefold() in forbidden_exact]
    if present:
        errors.append(f"forbidden sample columns: {present}")
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
        if path.suffix == ".parquet" and relative != SAMPLE_ENTRY:
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
        "# Smoke ZIP V8.2",
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
