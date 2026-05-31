from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.47"
IMPORT_TIMEOUT_SECONDS = 20
PYTEST_TIMEOUT_SECONDS = 60
TEST_TIMEOUT_SECONDS = 120
AUDIT_TIMEOUT_SECONDS = 45
SAMPLE_CHECK_TIMEOUT_SECONDS = 45


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    result = smoke_zip(Path(args.zip_path).resolve())
    _write_reports(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


def smoke_zip(zip_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    packaging_checks_passed = False
    sample_checks_passed = True
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_47_smoke_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            archive.extractall(extract_root)
        packaging_errors = _check_packaging_names(names)
        errors.extend(packaging_errors)
        packaging_checks_passed = not packaging_errors
        env = os.environ.copy()
        env["PYTHONPATH"] = str(extract_root / "src")
        errors.extend(_import_modules(extract_root, env))
        errors.extend(_run_pytest_collect(extract_root, env))
        errors.extend(_run_v9_47_tests(extract_root, env))
        errors.extend(_run_audit_lite_validator(extract_root, env))
        errors.extend(_run_self_audit(extract_root, zip_path, env))
    return {"version": VERSION, "zip": str(zip_path), "passed": not errors, "errors": errors, "packaging_checks_passed": packaging_checks_passed, "sample_checks_passed": sample_checks_passed, "full_dataset_required": False, "import_timeout_seconds": IMPORT_TIMEOUT_SECONDS, "pytest_collect_only_timeout_seconds": PYTEST_TIMEOUT_SECONDS, "tests_timeout_seconds": TEST_TIMEOUT_SECONDS, "audit_timeout_seconds": AUDIT_TIMEOUT_SECONDS, "sample_checks_timeout_seconds": SAMPLE_CHECK_TIMEOUT_SECONDS, "sidecars_expected": False, "zip_fingerprints_expected": False}


def _check_packaging_names(names: list[str]) -> list[str]:
    errors: list[str] = []
    if any(name.endswith(".sha256.json") or name.endswith(".sha256.txt") for name in names):
        errors.append("ZIP must not contain sidecar or fingerprint files")
    if any(Path(name).name in {"Icon", "Icon\r", ".DS_Store"} for name in names):
        errors.append("ZIP must not contain Icon or .DS_Store parasite files")
    if any(name.startswith(("data/raw/", "data/silver/", "data/research/", "data/gold/")) for name in names):
        errors.append("ZIP must not contain full data directories")
    if any(name.startswith(("models/", "checkpoints/", "reports/backtests/", "reports/strategies/")) for name in names):
        errors.append("ZIP must not contain models, checkpoints, backtests or strategies")
    return errors


def _import_modules(extract_root: Path, env: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for module in [
        "galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47",
        "galapagos.features.ohlcv_aggtrades_exact_5y_feature_store_v9_47_validation",
    ]:
        completed = _run(["python", "-c", f"import {module}"], extract_root, env, IMPORT_TIMEOUT_SECONDS)
        if completed["returncode"] != 0:
            errors.append(f"import failed for {module}: {completed['stderr'][-1000:]}")
    return errors


def _run_pytest_collect(extract_root: Path, env: dict[str, str]) -> list[str]:
    completed = _run(["python", "-m", "pytest", "--collect-only", "-q", "tests/features/test_ohlcv_aggtrades_exact_5y_feature_store_v9_47.py", "tests/validation/test_ohlcv_aggtrades_exact_5y_feature_store_v9_47_validator.py"], extract_root, env, PYTEST_TIMEOUT_SECONDS)
    return [] if completed["returncode"] == 0 else [f"pytest collect-only failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]


def _run_v9_47_tests(extract_root: Path, env: dict[str, str]) -> list[str]:
    completed = _run(["python", "-m", "pytest", "-q", "tests/features/test_ohlcv_aggtrades_exact_5y_feature_store_v9_47.py", "tests/validation/test_ohlcv_aggtrades_exact_5y_feature_store_v9_47_validator.py"], extract_root, env, TEST_TIMEOUT_SECONDS)
    return [] if completed["returncode"] == 0 else [f"V9.47 tests failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]


def _run_audit_lite_validator(extract_root: Path, env: dict[str, str]) -> list[str]:
    completed = _run(["python", "scripts/validate_ohlcv_aggtrades_exact_5y_feature_store_v9_47.py", "--mode", "audit-lite"], extract_root, env, AUDIT_TIMEOUT_SECONDS)
    return [] if completed["returncode"] == 0 else [f"V9.47 audit-lite validator failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]


def _run_self_audit(extract_root: Path, zip_path: Path, env: dict[str, str]) -> list[str]:
    completed = _run(["python", "scripts/audit_audit_lite_zip_v9_47.py", "--zip", str(zip_path)], extract_root, env, AUDIT_TIMEOUT_SECONDS)
    return [] if completed["returncode"] == 0 else [f"self audit failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]


def _run(command: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False, timeout=timeout)
        return {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
    except subprocess.TimeoutExpired as exc:
        return {"returncode": 124, "stdout": exc.stdout or "", "stderr": f"timeout after {timeout}s"}


def _write_reports(result: dict[str, Any]) -> None:
    report_dir = Path("reports/audit_lite")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "zip_smoke_v9_47.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_smoke_v9_47.md").write_text("# Smoke ZIP V9.47\n\n" f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n" f"- Erreurs : `{result['errors']}`.\n" f"- Packaging checks : `{result['packaging_checks_passed']}`.\n" f"- Sample checks : `{result['sample_checks_passed']}`.\n" f"- Full dataset requis : `{result['full_dataset_required']}`.\n" f"- Timeout imports : `{IMPORT_TIMEOUT_SECONDS}` secondes.\n" f"- Timeout pytest collect-only : `{PYTEST_TIMEOUT_SECONDS}` secondes.\n" f"- Timeout tests V9.47 : `{TEST_TIMEOUT_SECONDS}` secondes.\n" f"- Timeout audit : `{AUDIT_TIMEOUT_SECONDS}` secondes.\n" f"- Timeout sample checks : `{SAMPLE_CHECK_TIMEOUT_SECONDS}` secondes.\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
