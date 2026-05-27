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


VERSION = "V9.12"
IMPORT_TIMEOUT_SECONDS = 20
PYTEST_TIMEOUT_SECONDS = 60
TEST_TIMEOUT_SECONDS = 60


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
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_12_smoke_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            archive.extractall(extract_root)
        if any(name.endswith(".sha256.json") or name.endswith(".sha256.txt") for name in names):
            errors.append("ZIP must not contain sidecar or fingerprint files")
        if any(Path(name).name in {"Icon", "Icon\r"} for name in names):
            errors.append("ZIP must not contain Icon parasite files")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(extract_root / "src")
        sys.path.insert(0, str(extract_root / "src"))
        try:
            errors.extend(_import_modules(extract_root, env))
            errors.extend(_check_reports(extract_root))
            errors.extend(_check_samples(extract_root))
        finally:
            if str(extract_root / "src") in sys.path:
                sys.path.remove(str(extract_root / "src"))
        errors.extend(_run_pytest_collect(extract_root, env))
        errors.extend(_run_v9_12_tests(extract_root, env))
    return {
        "version": VERSION,
        "zip": str(zip_path),
        "passed": not errors,
        "errors": errors,
        "import_timeout_seconds": IMPORT_TIMEOUT_SECONDS,
        "pytest_timeout_seconds": PYTEST_TIMEOUT_SECONDS,
        "test_timeout_seconds": TEST_TIMEOUT_SECONDS,
        "sidecars_expected": False,
        "zip_fingerprints_expected": False,
    }


def _import_modules(extract_root: Path, env: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for module in [
        "galapagos.labels.horizon_event_label_redesign_v9_12",
        "galapagos.labels.horizon_event_label_redesign_v9_12_schemas",
        "galapagos.labels.horizon_event_label_redesign_v9_12_validation",
    ]:
        completed = _run(["python", "-c", f"import {module}"], extract_root, env, IMPORT_TIMEOUT_SECONDS)
        if completed["returncode"] != 0:
            errors.append(f"import failed for {module}: {completed['stderr'][-1000:]}")
    return errors


def _check_reports(extract_root: Path) -> list[str]:
    errors: list[str] = []
    report = _read_json(extract_root / "reports/labels/horizon_event_label_redesign_v9_12.json")
    if report.get("version") != VERSION:
        errors.append("V9.12 report version mismatch")
    if report.get("recommended_candidate", {}).get("target_name") != "up_down_flat_volnorm_h4":
        errors.append("V9.12 recommended candidate mismatch")
    if report.get("safety_flags", {}).get("no_sidecars") is not True:
        errors.append("V9.12 report must confirm no sidecars")
    if report.get("safety_flags", {}).get("no_zip_fingerprints") is not True:
        errors.append("V9.12 report must confirm no ZIP fingerprints")
    return errors


def _check_samples(extract_root: Path) -> list[str]:
    errors: list[str] = []
    from galapagos.labels.horizon_event_label_redesign_v9_12_schemas import HORIZON_EVENT_LABEL_COLUMNS_V9_12

    forbidden = {"prediction", "model_score", "signal", "trading_signal", "order", "pnl", "sharpe", "drawdown", "equity_curve", "profit_factor", "backtest", "position_size", "strategy", "entry", "exit", "trade"}
    for timeframe in ["1m", "5m", "15m", "1h"]:
        path = extract_root / "data/audit_lite/v9_12/labels" / f"timeframe={timeframe}" / "labels_sample.parquet"
        if not path.exists():
            errors.append(f"missing V9.12 sample for {timeframe}")
            continue
        frame = pd.read_parquet(path, engine="pyarrow")
        if list(frame.columns) != HORIZON_EVENT_LABEL_COLUMNS_V9_12:
            errors.append(f"schema mismatch in sample {timeframe}")
        bad = [column for column in frame.columns if column.casefold() in forbidden]
        if bad:
            errors.append(f"forbidden columns in sample {timeframe}: {bad}")
    return errors


def _run_pytest_collect(extract_root: Path, env: dict[str, str]) -> list[str]:
    completed = _run(["python", "-m", "pytest", "--collect-only", "-q"], extract_root, env, PYTEST_TIMEOUT_SECONDS)
    if completed["returncode"] != 0:
        return [f"pytest collect-only failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]
    return []


def _run_v9_12_tests(extract_root: Path, env: dict[str, str]) -> list[str]:
    completed = _run(
        [
            "python",
            "-m",
            "pytest",
            "-q",
            "tests/labels/test_horizon_event_label_redesign_v9_12.py",
            "tests/validation/test_horizon_event_label_redesign_v9_12_validator.py",
        ],
        extract_root,
        env,
        TEST_TIMEOUT_SECONDS,
    )
    if completed["returncode"] != 0:
        return [f"V9.12 tests failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]
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
    (report_dir / "zip_smoke_v9_12.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_smoke_v9_12.md").write_text(
        "# Smoke ZIP V9.12\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n"
        f"- Timeout imports : `{IMPORT_TIMEOUT_SECONDS}` secondes.\n"
        f"- Timeout pytest collect-only : `{PYTEST_TIMEOUT_SECONDS}` secondes.\n"
        f"- Timeout tests V9.12 : `{TEST_TIMEOUT_SECONDS}` secondes.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
