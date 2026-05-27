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


VERSION = "V9.14"
IMPORT_TIMEOUT_SECONDS = 20
PYTEST_TIMEOUT_SECONDS = 60
TEST_TIMEOUT_SECONDS = 60
SAMPLE_TIMEOUT_SECONDS = 40


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
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_14_smoke_") as tmp:
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
        errors.extend(_import_modules(extract_root, env))
        errors.extend(_run_pytest_collect(extract_root, env))
        errors.extend(_run_v9_14_tests(extract_root, env))
        errors.extend(_check_reports(extract_root))
        errors.extend(_check_samples_in_subprocess(extract_root, env))
    return {
        "version": VERSION,
        "zip": str(zip_path),
        "passed": not errors,
        "errors": errors,
        "import_timeout_seconds": IMPORT_TIMEOUT_SECONDS,
        "pytest_timeout_seconds": PYTEST_TIMEOUT_SECONDS,
        "test_timeout_seconds": TEST_TIMEOUT_SECONDS,
        "sample_timeout_seconds": SAMPLE_TIMEOUT_SECONDS,
        "sidecars_expected": False,
        "zip_fingerprints_expected": False,
    }


def _import_modules(extract_root: Path, env: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for module in [
        "galapagos.research.feature_label_separability_v9_14",
        "galapagos.research.feature_label_separability_v9_14_validation",
    ]:
        completed = _run(["python", "-c", f"import {module}"], extract_root, env, IMPORT_TIMEOUT_SECONDS)
        if completed["returncode"] != 0:
            errors.append(f"import failed for {module}: {completed['stderr'][-1000:]}")
    return errors


def _check_reports(extract_root: Path) -> list[str]:
    errors: list[str] = []
    report = _read_json(extract_root / "reports/research_decisions/feature_label_separability_v9_14.json")
    if report.get("version") != VERSION:
        errors.append("V9.14 report version mismatch")
    if report.get("target_name") != "up_down_flat_volnorm_h4":
        errors.append("V9.14 target mismatch")
    if report.get("v9_14_decision", {}).get("decision") != "feature_first_before_more_labels":
        errors.append("V9.14 decision mismatch")
    if report.get("safety_flags", {}).get("no_walk_forward") is not True:
        errors.append("V9.14 must confirm no walk-forward")
    if report.get("safety_flags", {}).get("no_sidecars") is not True:
        errors.append("V9.14 must confirm no sidecars")
    return errors


def _check_samples_in_subprocess(extract_root: Path, env: dict[str, str]) -> list[str]:
    code = r'''
from pathlib import Path
try:
    import pandas as pd
except Exception as exc:
    raise SystemExit(f"pandas/pyarrow sample check dependency unavailable: {exc}")
root = Path(".")
required = []
for timeframe in ["1m", "5m", "15m", "1h"]:
    required.append(root / "data/audit_lite/v9_13/datasets" / f"timeframe={timeframe}" / "dataset_sample.parquet")
    required.append(root / "data/audit_lite/v9_13/ml_scores" / f"timeframe={timeframe}" / "ml-scores_sample.parquet")
for path in required:
    if not path.exists():
        raise SystemExit(f"missing sample: {path}")
    frame = pd.read_parquet(path, engine="pyarrow")
    if frame.empty:
        raise SystemExit(f"empty sample: {path}")
    forbidden = {"signal", "trading_signal", "order", "pnl", "sharpe", "drawdown", "equity_curve", "profit_factor", "backtest", "position_size", "strategy"}
    bad = [column for column in frame.columns if column.casefold() in forbidden]
    if bad:
        raise SystemExit(f"forbidden columns in sample {path}: {bad}")
'''
    completed = _run(["python", "-c", code], extract_root, env, SAMPLE_TIMEOUT_SECONDS)
    if completed["returncode"] != 0:
        return [f"sample check failed cleanly: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]
    return []


def _run_pytest_collect(extract_root: Path, env: dict[str, str]) -> list[str]:
    completed = _run(["python", "-m", "pytest", "--collect-only", "-q"], extract_root, env, PYTEST_TIMEOUT_SECONDS)
    if completed["returncode"] != 0:
        return [f"pytest collect-only failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]
    return []


def _run_v9_14_tests(extract_root: Path, env: dict[str, str]) -> list[str]:
    completed = _run(
        [
            "python",
            "-m",
            "pytest",
            "-q",
            "tests/research/test_feature_label_separability_v9_14.py",
            "tests/validation/test_feature_label_separability_v9_14_validator.py",
        ],
        extract_root,
        env,
        TEST_TIMEOUT_SECONDS,
    )
    if completed["returncode"] != 0:
        return [f"V9.14 tests failed: {completed['stdout'][-1000:]} {completed['stderr'][-1000:]}"]
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
    (report_dir / "zip_smoke_v9_14.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_smoke_v9_14.md").write_text(
        "# Smoke ZIP V9.14\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n"
        f"- Timeout imports : `{IMPORT_TIMEOUT_SECONDS}` secondes.\n"
        f"- Timeout pytest collect-only : `{PYTEST_TIMEOUT_SECONDS}` secondes.\n"
        f"- Timeout tests V9.14 : `{TEST_TIMEOUT_SECONDS}` secondes.\n"
        f"- Timeout samples : `{SAMPLE_TIMEOUT_SECONDS}` secondes.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
