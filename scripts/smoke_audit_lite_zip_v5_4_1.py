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


VERSION = "V5.4.1"
SMOKE_JSON = Path("reports/audit_lite/zip_smoke_v5_4_1.json")
SMOKE_MD = Path("reports/audit_lite/zip_smoke_v5_4_1.md")
FORBIDDEN_SAFETY_TRUE = ["trading_enabled", "orders_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled"]


def smoke_zip(zip_path: Path) -> dict[str, Any]:
    start = time.perf_counter()
    errors: list[str] = []
    warnings: list[str] = []
    collect_only: dict[str, Any] = {"executed": False}
    if not zip_path.exists():
        return _result(zip_path, errors=[f"missing zip: {zip_path}"], warnings=warnings, start=start, collect_only=collect_only)
    with tempfile.TemporaryDirectory(prefix="galapagos_v5_4_1_smoke_") as tmp:
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
        "reports/manifests/max_history_offline_ml_research_v5_4_manifest.json",
        "reports/ml/max_history_offline_ml_research_v5_4.json",
        "reports/audit_lite/v5_4_full_local_validation_attestation.json",
        "docs/max_history_offline_ml_research_v5_4.md",
        "scripts/release_audit_lite_zip_v5_4_1.py",
        "scripts/audit_audit_lite_zip_v5_4_1.py",
        "scripts/smoke_audit_lite_zip_v5_4_1.py",
        "tests/ml/test_max_history_offline_ml_research_v5_4.py",
        "tests/validation/test_max_history_offline_ml_research_v5_4_validator.py",
    ]
    return [f"missing smoke file: {relative}" for relative in required if not (root / relative).exists()]


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
        if relative.startswith(("data/raw/", "reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/", "checkpoints/")):
            errors.append(f"forbidden runtime artifact found: {relative}")
        if path.suffix.casefold() in {".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt"}:
            errors.append(f"forbidden persistent model artifact found: {relative}")
    return errors


def _is_forbidden_pytest_collectible_script(relative: str) -> bool:
    path = Path(relative)
    if len(path.parts) != 2 or path.parts[0] != "scripts" or path.suffix != ".py":
        return False
    name = path.name
    return name in {"run_forward_paper_test.py", "test_llm_provider.py"} or name.startswith("test_") or name.endswith("_test.py")


def _check_imports(root: Path) -> list[str]:
    sys.path.insert(0, str(root / "src"))
    errors: list[str] = []
    for module in [
        "galapagos.ml.max_history_window",
        "galapagos.ml.max_history_window_metrics",
        "galapagos.ml.max_history_window_quality",
        "galapagos.ml.max_history_window_validation",
        "galapagos.ml.schemas",
    ]:
        try:
            importlib.import_module(module)
        except Exception as exc:  # pragma: no cover - smoke diagnostic
            errors.append(f"import failed for {module}: {exc}")
    return errors


def _check_samples(root: Path) -> list[str]:
    errors: list[str] = []
    schema_module = importlib.import_module("galapagos.ml.schemas")
    expected_columns = schema_module.ML_SCORE_COLUMNS_V5_4
    for timeframe in ["1m", "5m", "15m", "1h"]:
        path = root / "data" / "audit_lite" / "v5_4" / "ml_scores" / f"timeframe={timeframe}" / "sample.parquet"
        if not path.exists():
            errors.append(f"missing score sample for {timeframe}")
            continue
        frame = pd.read_parquet(path, engine="pyarrow")
        if list(frame.columns) != expected_columns:
            errors.append(f"score sample schema mismatch for {timeframe}")
        forbidden = {"signal", "trading_signal", "order", "strategy", "pnl", "profit"}
        present = [column for column in frame.columns if column.casefold() in forbidden]
        if present:
            errors.append(f"forbidden score sample columns for {timeframe}: {present}")
    return errors


def _check_reports(root: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = root / "reports/manifests/max_history_offline_ml_research_v5_4_manifest.json"
    report_path = root / "reports/ml/max_history_offline_ml_research_v5_4.json"
    if manifest_path.exists() and report_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if manifest != report:
            errors.append("smoke manifest/report mismatch")
        safety = manifest.get("safety", {})
        for key in FORBIDDEN_SAFETY_TRUE:
            if safety.get(key) is not False:
                errors.append(f"smoke safety flag must be false: {key}")
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
        "# Smoke ZIP V5.4.1",
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
