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


VERSION = "V9.33"
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
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_33_smoke_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            archive.extractall(extract_root)
        if any(name.endswith(".sha256.json") or name.endswith(".sha256.txt") for name in names):
            errors.append("ZIP must not contain sidecar or fingerprint files")
        if any(Path(name).name in {"Icon", "Icon\r", ".DS_Store"} for name in names):
            errors.append("ZIP must not contain Icon or .DS_Store parasite files")
        if any(name.startswith(("data/raw/", "data/silver/", "data/research/", "data/gold/")) for name in names):
            errors.append("ZIP must not contain full data directories")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(extract_root / "src")
        errors.extend(_import_modules(extract_root, env))
        errors.extend(_run_pytest_collect(extract_root, env))
        errors.extend(_run_v9_33_tests(extract_root, env))
        errors.extend(_check_reports(extract_root))
        errors.extend(_run_self_audit(extract_root, zip_path, env))
    return {
        "version": VERSION,
        "zip": str(zip_path),
        "passed": not errors,
        "errors": errors,
        "import_timeout_seconds": IMPORT_TIMEOUT_SECONDS,
        "pytest_collect_only_timeout_seconds": PYTEST_TIMEOUT_SECONDS,
        "tests_timeout_seconds": TEST_TIMEOUT_SECONDS,
        "audit_timeout_seconds": AUDIT_TIMEOUT_SECONDS,
        "sample_checks_timeout_seconds": 0,
        "sidecars_expected": False,
        "zip_fingerprints_expected": False,
    }


def _import_modules(extract_root: Path, env: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for module in [
        "galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_33_schemas",
        "galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_33",
        "galapagos.features.ohlcv_aggtrades_5y_feature_store_v9_33_validation",
    ]:
        completed = _run(["python", "-c", f"import {module}"], extract_root, env, IMPORT_TIMEOUT_SECONDS)
        if completed["returncode"] != 0:
            errors.append(f"import failed for {module}: {completed['stderr'][-1000:]}")
    return errors


def _run_pytest_collect(extract_root: Path, env: dict[str, str]) -> list[str]:
    completed = _run(
        [
            "python",
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "tests/features/test_ohlcv_aggtrades_5y_feature_store_v9_33.py",
            "tests/validation/test_ohlcv_aggtrades_5y_feature_store_v9_33_validator.py",
        ],
        extract_root,
        env,
        PYTEST_TIMEOUT_SECONDS,
    )
    if completed["returncode"] != 0:
        return [f"pytest collect-only failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]
    return []


def _run_v9_33_tests(extract_root: Path, env: dict[str, str]) -> list[str]:
    completed = _run(
        [
            "python",
            "-m",
            "pytest",
            "-q",
            "tests/features/test_ohlcv_aggtrades_5y_feature_store_v9_33.py",
            "tests/validation/test_ohlcv_aggtrades_5y_feature_store_v9_33_validator.py",
        ],
        extract_root,
        env,
        TEST_TIMEOUT_SECONDS,
    )
    if completed["returncode"] != 0:
        return [f"V9.33 tests failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]
    return []


def _check_reports(extract_root: Path) -> list[str]:
    report = _read_json(extract_root / "reports/features/ohlcv_aggtrades_5y_feature_store_v9_33.json")
    errors: list[str] = []
    if report.get("version") != VERSION:
        errors.append("V9.33 report version mismatch")
    if report.get("aggtrades_readiness", {}).get("aggtrades_5y_ready") is not True:
        errors.append("V9.33 smoke expects aggTrades 5Y readiness")
    if report.get("decision") == "ohlcv_5y_extension_required_before_feature_store":
        if report.get("feature_store_created") is not False or report.get("features_created") is not False:
            errors.append("V9.33 extension-required decision must not create feature store")
    if report.get("labels_created") is not False or report.get("dataset_created") is not False or report.get("ml_executed") is not False:
        errors.append("V9.33 smoke expects no labels, dataset or ML")
    if report.get("network_used") is not False or report.get("new_data_downloaded") is not False or report.get("ingestion_executed") is not False:
        errors.append("V9.33 smoke expects no network, no new downloads and no ingestion")
    return errors


def _run_self_audit(extract_root: Path, zip_path: Path, env: dict[str, str]) -> list[str]:
    completed = _run(["python", "scripts/audit_audit_lite_zip_v9_33.py", "--zip", str(zip_path)], extract_root, env, AUDIT_TIMEOUT_SECONDS)
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
    (report_dir / "zip_smoke_v9_33.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_smoke_v9_33.md").write_text(
        "# Smoke ZIP V9.33\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n"
        f"- Timeout imports : `{IMPORT_TIMEOUT_SECONDS}` secondes.\n"
        f"- Timeout pytest collect-only : `{PYTEST_TIMEOUT_SECONDS}` secondes.\n"
        f"- Timeout tests V9.33 : `{TEST_TIMEOUT_SECONDS}` secondes.\n"
        f"- Timeout audit : `{AUDIT_TIMEOUT_SECONDS}` secondes.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
