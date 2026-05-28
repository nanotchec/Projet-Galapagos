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


VERSION = "V9.25"
IMPORT_TIMEOUT_SECONDS = 20
PYTEST_TIMEOUT_SECONDS = 60
TEST_TIMEOUT_SECONDS = 90
AUDIT_TIMEOUT_SECONDS = 30


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
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_25_smoke_") as tmp:
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
        errors.extend(_run_v9_25_tests(extract_root, env))
        errors.extend(_check_reports(extract_root))
        errors.extend(_run_self_audit(extract_root, zip_path, env))
    return {
        "version": VERSION,
        "zip": str(zip_path),
        "passed": not errors,
        "errors": errors,
        "import_timeout_seconds": IMPORT_TIMEOUT_SECONDS,
        "pytest_timeout_seconds": PYTEST_TIMEOUT_SECONDS,
        "test_timeout_seconds": TEST_TIMEOUT_SECONDS,
        "audit_timeout_seconds": AUDIT_TIMEOUT_SECONDS,
        "sidecars_expected": False,
        "zip_fingerprints_expected": False,
    }


def _import_modules(extract_root: Path, env: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for module in [
        "galapagos.data.aggtrades_post_v9_collection_v9_18",
        "galapagos.data.aggtrades_post_v9_batch3_collection_v9_24",
        "galapagos.data.aggtrades_post_v9_completion_campaign_v9_25",
        "galapagos.data.aggtrades_post_v9_completion_campaign_v9_25_validation",
    ]:
        completed = _run(["python", "-c", f"import {module}"], extract_root, env, IMPORT_TIMEOUT_SECONDS)
        if completed["returncode"] != 0:
            errors.append(f"import failed for {module}: {completed['stderr'][-1000:]}")
    return errors


def _run_pytest_collect(extract_root: Path, env: dict[str, str]) -> list[str]:
    completed = _run(["python", "-m", "pytest", "--collect-only", "-q"], extract_root, env, PYTEST_TIMEOUT_SECONDS)
    if completed["returncode"] != 0:
        return [f"pytest collect-only failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]
    return []


def _run_v9_25_tests(extract_root: Path, env: dict[str, str]) -> list[str]:
    completed = _run(
        [
            "python",
            "-m",
            "pytest",
            "-q",
            "tests/data/test_aggtrades_post_v9_completion_campaign_v9_25.py",
            "tests/validation/test_aggtrades_post_v9_completion_campaign_v9_25_validator.py",
        ],
        extract_root,
        env,
        TEST_TIMEOUT_SECONDS,
    )
    if completed["returncode"] != 0:
        return [f"V9.25 tests failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]
    return []


def _run_self_audit(extract_root: Path, zip_path: Path, env: dict[str, str]) -> list[str]:
    completed = _run(["python", "scripts/audit_audit_lite_zip_v9_25.py", "--zip", str(zip_path)], extract_root, env, AUDIT_TIMEOUT_SECONDS)
    if completed["returncode"] != 0:
        return [f"self audit failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]
    return []


def _check_reports(extract_root: Path) -> list[str]:
    errors: list[str] = []
    report = _read_json(extract_root / "reports/data/aggtrades_post_v9_completion_campaign_v9_25.json")
    summary = report.get("campaign_summary", {})
    if report.get("version") != VERSION:
        errors.append("V9.25 report version mismatch")
    decision = report.get("decision")
    if decision not in {
        "aggtrades_post_v9_remaining_window_collection_complete",
        "aggtrades_post_v9_remaining_window_collection_failed_storage",
    }:
        errors.append("V9.25 decision mismatch")
    if decision == "aggtrades_post_v9_remaining_window_collection_complete":
        if summary.get("days_downloaded_total") != 514 or summary.get("days_normalized_total") != 514 or summary.get("days_complete_total") != 514:
            errors.append("V9.25 smoke expects 514 downloaded, normalized and complete days for complete campaign")
        if summary.get("local_file_coverage_end") != "2026-05-05":
            errors.append("V9.25 complete smoke target end mismatch")
        if summary.get("complete_collection_reached") is not True or summary.get("future_full_coverage_complete") is not True:
            errors.append("V9.25 complete flags mismatch")
    if decision == "aggtrades_post_v9_remaining_window_collection_failed_storage":
        if summary.get("days_complete_total", 0) <= 0:
            errors.append("V9.25 storage smoke expects partial completed days")
        if summary.get("days_quarantined_total") != 0:
            errors.append("V9.25 storage smoke expects no quarantined days")
        if summary.get("complete_collection_reached") is not False or summary.get("future_full_coverage_complete") is not False:
            errors.append("V9.25 storage smoke must not claim completion")
    if summary.get("local_file_coverage_start") != "2024-05-05":
        errors.append("V9.25 local coverage mismatch")
    if summary.get("total_rows_new", 0) <= 0 or summary.get("raw_bytes_new", 0) <= 0 or summary.get("silver_bytes_new", 0) <= 0:
        errors.append("V9.25 smoke expects positive campaign metrics")
    flags = report.get("safety_flags", {})
    if flags.get("api_key_used") is not False or flags.get("private_endpoint_used") is not False:
        errors.append("V9.25 must confirm no API key and no private endpoint")
    if flags.get("exchange_auth_used") is not False or flags.get("websocket_live_used") is not False:
        errors.append("V9.25 must confirm no exchange auth and no websocket live")
    if flags.get("network_used") is not True or flags.get("no_new_data_download") is not False or flags.get("no_ingestion_executed") is not False:
        errors.append("V9.25 must confirm public network, new download and ingestion")
    return errors


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
    (report_dir / "zip_smoke_v9_25.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_smoke_v9_25.md").write_text(
        "# Smoke ZIP V9.25\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n"
        f"- Timeout imports : `{IMPORT_TIMEOUT_SECONDS}` secondes.\n"
        f"- Timeout pytest collect-only : `{PYTEST_TIMEOUT_SECONDS}` secondes.\n"
        f"- Timeout tests V9.25 : `{TEST_TIMEOUT_SECONDS}` secondes.\n"
        f"- Timeout audit : `{AUDIT_TIMEOUT_SECONDS}` secondes.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
