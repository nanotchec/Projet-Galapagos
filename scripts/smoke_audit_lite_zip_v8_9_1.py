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


VERSION = "V8.9.1"
SMOKE_JSON = Path("reports/audit_lite/zip_smoke_v8_9_1.json")
SMOKE_MD = Path("reports/audit_lite/zip_smoke_v8_9_1.md")


def smoke_zip(zip_path: Path) -> dict[str, Any]:
    start = time.perf_counter()
    errors: list[str] = []
    warnings: list[str] = []
    collect_only: dict[str, Any] = {"executed": False}
    targeted_tests: dict[str, Any] = {"executed": False}
    if not zip_path.exists():
        return _result(zip_path, errors=[f"missing zip: {zip_path}"], warnings=warnings, start=start, collect_only=collect_only, targeted_tests=targeted_tests)
    with tempfile.TemporaryDirectory(prefix="galapagos_v8_9_1_smoke_") as tmp:
        target = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(target)
        errors.extend(_check_required_files(target))
        errors.extend(_check_forbidden_files(target))
        errors.extend(_check_imports(target))
        errors.extend(_check_reports(target))
        collect_only = _run_command(target, [sys.executable, "-m", "pytest", "--collect-only", "-q"], "PYTHONPATH=src python -m pytest --collect-only -q")
        if collect_only["returncode"] != 0:
            errors.append("pytest collect-only failed inside extracted V8.9.1 ZIP")
        targeted_tests = _run_command(
            target,
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "tests/features/test_ohlcv_trades_feature_audit_v8_9.py",
                "tests/validation/test_ohlcv_trades_feature_audit_v8_9_validator.py",
            ],
            "PYTHONPATH=src python -m pytest -q tests/features/test_ohlcv_trades_feature_audit_v8_9.py tests/validation/test_ohlcv_trades_feature_audit_v8_9_validator.py",
        )
        if targeted_tests["returncode"] != 0:
            errors.append("V8.9 targeted tests failed inside extracted V8.9.1 ZIP")
    return _result(zip_path, errors=errors, warnings=warnings, start=start, collect_only=collect_only, targeted_tests=targeted_tests)


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
        "reports/manifests/ohlcv_trades_feature_audit_v8_9_manifest.json",
        "reports/features/ohlcv_trades_feature_audit_v8_9.json",
        "reports/features/ohlcv_trades_feature_selection_v8_9.json",
        "reports/manifests/ohlcv_trades_1y_offline_supervised_dataset_v8_4_manifest.json",
        "reports/manifests/ohlcv_trades_1y_feature_store_v8_3_manifest.json",
        "reports/features/ohlcv_trades_1y_feature_store_v8_3.json",
        "reports/manifests/ohlcv_trades_1y_offline_ml_research_v8_5_manifest.json",
        "reports/ml/ohlcv_trades_1y_offline_ml_research_v8_5.json",
        "reports/manifests/strict_walk_forward_validation_v8_7_manifest.json",
        "reports/ml/strict_walk_forward_validation_v8_7.json",
        "reports/research_decisions/v8_8_research_decision_gate.json",
        "reports/audit_lite/v8_9_full_local_validation_attestation.json",
        "reports/audit_lite/v8_9_artifact_inventory.json",
        "docs/ohlcv_trades_feature_audit_v8_9.md",
        "scripts/release_audit_lite_zip_v8_9_1.py",
        "scripts/audit_audit_lite_zip_v8_9_1.py",
        "scripts/smoke_audit_lite_zip_v8_9_1.py",
        "tests/features/test_ohlcv_trades_feature_audit_v8_9.py",
        "tests/validation/test_ohlcv_trades_feature_audit_v8_9_validator.py",
    ]
    return [f"missing smoke file: {relative}" for relative in required if not (root / relative).exists()]


def _check_forbidden_files(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            errors.append(f"forbidden cache artifact found: {relative}")
        if relative.startswith(("data/raw/", "data/research/", "reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/", "checkpoints/")):
            errors.append(f"forbidden runtime artifact found: {relative}")
        if path.suffix.casefold() in {".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt"}:
            errors.append(f"forbidden binary/model artifact found: {relative}")
    return errors


def _check_imports(root: Path) -> list[str]:
    sys.path.insert(0, str(root / "src"))
    errors: list[str] = []
    for module in [
        "galapagos.features.ohlcv_trades_feature_audit",
        "galapagos.features.ohlcv_trades_feature_audit_validation",
        "galapagos.features.ohlcv_trades_feature_selection",
        "galapagos.features.ohlcv_trades_feature_selection_schemas",
    ]:
        try:
            importlib.import_module(module)
        except Exception as exc:  # pragma: no cover - smoke diagnostic
            errors.append(f"import failed for {module}: {exc}")
    return errors


def _check_reports(root: Path) -> list[str]:
    errors: list[str] = []
    from galapagos.features.ohlcv_trades_feature_selection import is_forbidden_feature_v8_9

    manifest_path = root / "reports/manifests/ohlcv_trades_feature_audit_v8_9_manifest.json"
    report_path = root / "reports/features/ohlcv_trades_feature_audit_v8_9.json"
    selection_path = root / "reports/features/ohlcv_trades_feature_selection_v8_9.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    if manifest != report:
        errors.append("smoke V8.9 manifest/report mismatch")
    selected = selection.get("candidate_refined_feature_set", {}).get("selected_features", [])
    if not selected:
        errors.append("smoke selection report missing selected features")
    forbidden = [feature for feature in selected if is_forbidden_feature_v8_9(feature)]
    if forbidden:
        errors.append(f"smoke selected features contain forbidden features: {forbidden}")
    if manifest.get("leakage_guard", {}).get("passed") is not True:
        errors.append("smoke leakage_guard.passed must be true")
    findings = manifest.get("findings", {})
    for key in ["feature_set_validated_for_trading", "strategy_validated", "backtest_performed", "actionable_signal_produced"]:
        if findings.get(key) is not False:
            errors.append(f"smoke finding must be false: {key}")
    safety = manifest.get("safety", {})
    for key in ["trading_enabled", "orders_enabled", "backtest_enabled", "strategy_enabled", "execution_enabled"]:
        if safety.get(key) is not False:
            errors.append(f"smoke safety flag must be false: {key}")
    return errors


def _run_command(root: Path, command: list[str], label: str) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    completed = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, check=False)
    return {
        "executed": True,
        "command": label,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def _result(
    zip_path: Path,
    *,
    errors: list[str],
    warnings: list[str],
    start: float,
    collect_only: dict[str, Any],
    targeted_tests: dict[str, Any],
) -> dict[str, Any]:
    return {
        "version": VERSION,
        "zip_path": str(zip_path),
        "zip_size_bytes": zip_path.stat().st_size if zip_path.exists() else 0,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "pytest_collect_only": collect_only,
        "targeted_tests": targeted_tests,
        "smoke_duration_seconds": round(time.perf_counter() - start, 3),
    }


def _write_reports(result: dict[str, Any]) -> None:
    SMOKE_JSON.parent.mkdir(parents=True, exist_ok=True)
    SMOKE_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    SMOKE_MD.write_text(
        "\n".join(
            [
                "# Smoke ZIP V8.9.1",
                "",
                f"- ZIP : `{result['zip_path']}`.",
                f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.",
                f"- Pytest collect-only : `{result['pytest_collect_only'].get('returncode') == 0}`.",
                f"- Tests V8.9 inclus : `{result['targeted_tests'].get('returncode') == 0}`.",
                f"- Duree : `{result['smoke_duration_seconds']}` secondes.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
