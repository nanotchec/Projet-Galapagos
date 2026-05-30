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


VERSION = "V9.40"
IMPORT_TIMEOUT_SECONDS = 20
PYTEST_TIMEOUT_SECONDS = 60
TEST_TIMEOUT_SECONDS = 120
AUDIT_TIMEOUT_SECONDS = 45


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
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_40_smoke_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            archive.extractall(extract_root)
        packaging_errors = _check_packaging_names(names)
        errors.extend(packaging_errors)
        packaging_checks_passed = not packaging_errors
        env = os.environ.copy()
        env["PYTHONPATH"] = str(extract_root / "src")
        errors.extend(_check_pyarrow_available(extract_root, env))
        errors.extend(_import_modules(extract_root, env))
        errors.extend(_run_pytest_collect(extract_root, env))
        errors.extend(_run_v9_40_tests(extract_root, env))
        errors.extend(_check_reports(extract_root))
        errors.extend(_run_self_audit(extract_root, zip_path, env))
    return {
        "version": VERSION,
        "zip": str(zip_path),
        "passed": not errors,
        "errors": errors,
        "packaging_checks_passed": packaging_checks_passed,
        "parquet_checks_required": True,
        "import_timeout_seconds": IMPORT_TIMEOUT_SECONDS,
        "pytest_collect_only_timeout_seconds": PYTEST_TIMEOUT_SECONDS,
        "tests_timeout_seconds": TEST_TIMEOUT_SECONDS,
        "audit_timeout_seconds": AUDIT_TIMEOUT_SECONDS,
        "sample_checks_timeout_seconds": 0,
        "sidecars_expected": False,
        "zip_fingerprints_expected": False,
    }


def _check_packaging_names(names: list[str]) -> list[str]:
    errors: list[str] = []
    if any(name.endswith(".sha256.json") or name.endswith(".sha256.txt") for name in names):
        errors.append("ZIP must not contain sidecar or fingerprint files")
    if any(Path(name).name in {"Icon", "Icon\r", ".DS_Store"} for name in names):
        errors.append("ZIP must not contain Icon or .DS_Store parasite files")
    if any(name.startswith(("data/raw/", "data/silver/", "data/research/", "data/gold/")) for name in names):
        errors.append("ZIP must not contain full data directories")
    return errors


def _check_pyarrow_available(extract_root: Path, env: dict[str, str]) -> list[str]:
    completed = _run(["python", "-c", "import pyarrow, pyarrow.parquet"], extract_root, env, IMPORT_TIMEOUT_SECONDS)
    if completed["returncode"] != 0:
        return ["pyarrow is required for V9.40 label validation smoke checks but is not importable"]
    return []


def _import_modules(extract_root: Path, env: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for module in ["galapagos.labels.ohlcv_aggtrades_5y_label_factory_v9_40", "galapagos.labels.ohlcv_aggtrades_5y_label_factory_v9_40_validation"]:
        completed = _run(["python", "-c", f"import {module}"], extract_root, env, IMPORT_TIMEOUT_SECONDS)
        if completed["returncode"] != 0:
            errors.append(f"import failed for {module}: {completed['stderr'][-1000:]}")
    return errors


def _run_pytest_collect(extract_root: Path, env: dict[str, str]) -> list[str]:
    completed = _run(["python", "-m", "pytest", "--collect-only", "-q", "tests/labels/test_ohlcv_aggtrades_5y_label_factory_v9_40.py", "tests/validation/test_ohlcv_aggtrades_5y_label_factory_v9_40_validator.py"], extract_root, env, PYTEST_TIMEOUT_SECONDS)
    if completed["returncode"] != 0:
        return [f"pytest collect-only failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]
    return []


def _run_v9_40_tests(extract_root: Path, env: dict[str, str]) -> list[str]:
    completed = _run(["python", "-m", "pytest", "-q", "tests/labels/test_ohlcv_aggtrades_5y_label_factory_v9_40.py", "tests/validation/test_ohlcv_aggtrades_5y_label_factory_v9_40_validator.py"], extract_root, env, TEST_TIMEOUT_SECONDS)
    if completed["returncode"] != 0:
        return [f"V9.40 tests failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]
    return []


def _check_reports(extract_root: Path) -> list[str]:
    report = _read_json(extract_root / "reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json")
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.40 report version mismatch")
    if report.get("dataset_created") is not False:
        errors.append("V9.40 smoke expects no supervised dataset")
    if report.get("network_used") is not False or report.get("new_data_downloaded") is not False:
        errors.append("V9.40 smoke expects no network and no downloads")
    if report.get("ml_executed") is not False or report.get("backtest_executed") is not False:
        errors.append("V9.40 smoke expects no ML or backtest")
    if report.get("labels_created") is not True:
        errors.append("V9.40 smoke expects labels_created=true in the delivered report")
    return errors


def _run_self_audit(extract_root: Path, zip_path: Path, env: dict[str, str]) -> list[str]:
    completed = _run(["python", "scripts/audit_audit_lite_zip_v9_40.py", "--zip", str(zip_path)], extract_root, env, AUDIT_TIMEOUT_SECONDS)
    if completed["returncode"] != 0:
        return [f"self audit failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]
    return []


def _run(command: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False, timeout=timeout)
        return {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
    except subprocess.TimeoutExpired as exc:
        return {"returncode": 124, "stdout": exc.stdout or "", "stderr": f"timeout after {timeout}s"}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_reports(result: dict[str, Any]) -> None:
    report_dir = Path("reports/audit_lite")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "zip_smoke_v9_40.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_smoke_v9_40.md").write_text("# Smoke ZIP V9.40\n\n" f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n" f"- Erreurs : `{result['errors']}`.\n" f"- Packaging checks : `{result['packaging_checks_passed']}`.\n" f"- Parquet checks requis : `{result['parquet_checks_required']}`.\n" f"- Timeout imports : `{IMPORT_TIMEOUT_SECONDS}` secondes.\n" f"- Timeout pytest collect-only : `{PYTEST_TIMEOUT_SECONDS}` secondes.\n" f"- Timeout tests V9.40 : `{TEST_TIMEOUT_SECONDS}` secondes.\n" f"- Timeout audit : `{AUDIT_TIMEOUT_SECONDS}` secondes.\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
