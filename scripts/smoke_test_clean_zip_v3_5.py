from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import _bootstrap

_bootstrap.bootstrap_src_path()


VERSION = "V3.5"
CURRENT_VALIDATOR = "validate_expanded_public_market_data_v3_5"
CURRENT_VALIDATOR_SCRIPT = "scripts/validate_expanded_public_market_data_v3_5.py"
EXPECTED_ROWS = {"1m": 129600, "5m": 25920, "15m": 8640, "1h": 2160}
ESSENTIAL_ENTRIES = [
    "src/galapagos/data/public_market/expanded_window.py",
    "src/galapagos/data/public_market/expanded_window_quality.py",
    "src/galapagos/data/public_market/expanded_window_validation.py",
    CURRENT_VALIDATOR_SCRIPT,
    "reports/manifests/expanded_public_market_data_v3_5_manifest.json",
    "reports/data_quality/expanded_public_market_data_v3_5.json",
    "reports/data_quality/expanded_public_market_data_v3_5.md",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_summary.md",
]
FORBIDDEN_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
FORBIDDEN_PREFIXES = [
    "reports/backtests/",
    "reports/strategies/",
    "reports/signals/",
    "reports/predictions/",
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
    "data/research/v3_5/features/",
    "data/research/v3_5/labels/",
    "data/research/v3_5/datasets/",
    "data/research/v3_5/ml/",
    "data/research/v3_5/backtests/",
    "data/research/v3_5/strategies/",
]
FORBIDDEN_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}
SAFETY_FALSE_FLAGS = [
    "trading_enabled",
    "backtest_enabled",
    "orders_enabled",
    "strategy_enabled",
    "execution_enabled",
    "ml_enabled",
    "labels_enabled",
    "dataset_enabled",
]


def main() -> None:
    started = time.perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    zip_path = Path(args.zip).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    current_validator_seconds: float | None = None
    forbidden_entries: list[str] = []
    row_counts: dict[str, int] = {}

    with tempfile.TemporaryDirectory(prefix="galapagos_v3_5_smoke_") as tmp:
        tmp_path = Path(tmp)
        extracted_root = tmp_path / "extracted"
        smoke_logs = tmp_path / "smoke_logs"
        extracted_root.mkdir()
        smoke_logs.mkdir()
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            archive.extractall(extracted_root)

        forbidden_entries = _find_forbidden_zip_entries(names)
        errors.extend(forbidden_entries)
        errors.extend(_validate_essential_entries(names))
        errors.extend(_validate_manifest_state_and_safety(extracted_root))
        validator_errors, current_validator_seconds = _run_current_validator(extracted_root, smoke_logs)
        errors.extend(validator_errors)
        label_errors, row_counts = _validate_output_rows_and_schema(extracted_root)
        errors.extend(label_errors)
        errors.extend(_validate_no_smoke_log_leaks(extracted_root))

    smoke_duration = round(time.perf_counter() - started, 3)
    payload = {
        "version": VERSION,
        "smoke_test_passed": not errors,
        "zip_path": str(zip_path),
        "current_validator_run": CURRENT_VALIDATOR,
        "current_validator_timing_seconds": current_validator_seconds,
        "historical_validators_run": False,
        "row_counts": row_counts,
        "forbidden_entries_found": forbidden_entries,
        "safety_flags_ok": not any("unsafe V3.5 flag active" in error for error in errors),
        "smoke_duration_seconds": smoke_duration,
        "errors": errors,
        "warnings": warnings,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_smoke_test_v3_5.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_smoke_test_v3_5.md").write_text(
        "# Smoke ZIP V3.5\n\n"
        f"- Statut : `{payload['smoke_test_passed']}`\n"
        f"- Validateur courant : `{payload['current_validator_run']}`\n"
        f"- Validateurs historiques relances : `{payload['historical_validators_run']}`\n"
        f"- Duree : `{payload['smoke_duration_seconds']}` secondes\n"
        f"- Erreurs : `{len(errors)}`\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


def _find_forbidden_zip_entries(names: list[str]) -> list[str]:
    errors: list[str] = []
    for name in names:
        relative = Path(name)
        if any(part in FORBIDDEN_PARTS for part in relative.parts):
            errors.append(f"forbidden zip part: {name}")
        if name.endswith(".zip") and not name.startswith("data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/"):
            errors.append(f"forbidden nested zip: {name}")
        if relative.name == ".env" or "secret" in name.casefold():
            errors.append(f"forbidden secret-like entry: {name}")
        if relative.name.startswith(".smoke-"):
            errors.append(f"forbidden smoke log entry: {name}")
        if relative.suffix.casefold() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden persistent model artifact: {name}")
    for prefix in FORBIDDEN_PREFIXES:
        if any(name.startswith(prefix) for name in names):
            errors.append(f"forbidden zip prefix: {prefix}")
    return errors


def _validate_essential_entries(names: list[str]) -> list[str]:
    name_set = set(names)
    errors = [f"missing essential entry: {entry}" for entry in ESSENTIAL_ENTRIES if entry not in name_set]
    raw_count = sum(1 for name in names if name.startswith("data/raw/public_market/binance_archive/spot/BTCUSDT/klines/1m/BTCUSDT-1m-2024-") and name.endswith(".zip"))
    if raw_count < 90:
        errors.append(f"expected at least 90 V3.5 raw zip entries, found {raw_count}")
    return errors


def _validate_manifest_state_and_safety(root: Path) -> list[str]:
    errors: list[str] = []
    manifest = _read_json(root / "reports/manifests/expanded_public_market_data_v3_5_manifest.json")
    report = _read_json(root / "reports/data_quality/expanded_public_market_data_v3_5.json")
    project_state_text = (root / "reports/PROJECT_STATE.json").read_text(encoding="utf-8")
    latest_summary = (root / "reports/current/latest_summary.md").read_text(encoding="utf-8")
    project_state = json.loads(project_state_text)
    if manifest != report:
        errors.append("V3.5 report JSON must match manifest")
    if manifest.get("version") != VERSION or report.get("version") != VERSION:
        errors.append("V3.5 manifest/report version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V3.5 manifest status must be PASS")
    if manifest.get("expected_rows") != EXPECTED_ROWS:
        errors.append("V3.5 expected rows mismatch")
    if project_state.get("candidate_version") != VERSION and VERSION not in latest_summary:
        errors.append("PROJECT_STATE/latest_summary must identify V3.5 as candidate")
    if project_state.get("last_validated_version") != "V3.4.1":
        errors.append("last_validated_version must be V3.4.1")
    if "pending_external_audit" not in latest_summary and project_state.get("candidate_status") != "pending_external_audit":
        errors.append("V3.5 must remain pending_external_audit")
    safety = manifest.get("safety", {})
    for flag in SAFETY_FALSE_FLAGS:
        if safety.get(flag) is not False:
            errors.append(f"unsafe V3.5 flag active: {flag}")
    if safety.get("public_read_only") is not True:
        errors.append("V3.5 public_read_only must be true")
    lower_state = (project_state_text + "\n" + latest_summary).casefold()
    for claim in ["aucun trading", "aucun paper live", "aucun ordre", "aucun backtest", "aucune strategie", "aucune feature", "aucun label"]:
        if claim not in lower_state and claim.replace("strategie", "stratégie") not in lower_state:
            errors.append(f"missing state safety claim: {claim}")
    return errors


def _validate_output_rows_and_schema(root: Path) -> tuple[list[str], dict[str, int]]:
    from galapagos.data.public_market.expanded_window import output_path
    from galapagos.data.public_market.schemas import OHLCV_COLUMNS
    from galapagos.data.public_market.storage import read_parquet

    errors: list[str] = []
    row_counts: dict[str, int] = {}
    for timeframe, expected_rows in EXPECTED_ROWS.items():
        frame = read_parquet(output_path(root, timeframe))
        row_counts[timeframe] = int(len(frame))
        if row_counts[timeframe] != expected_rows:
            errors.append(f"V3.5 row count mismatch for {timeframe}: {row_counts[timeframe]} != {expected_rows}")
        if list(frame.columns) != OHLCV_COLUMNS:
            errors.append(f"V3.5 OHLCV schema mismatch for {timeframe}")
    return errors, row_counts


def _run_current_validator(root: Path, smoke_logs: Path) -> tuple[list[str], float | None]:
    errors: list[str] = []
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    log_path = smoke_logs / f"{CURRENT_VALIDATOR}.log"
    started = time.perf_counter()
    print(f"running {CURRENT_VALIDATOR}", flush=True)
    with log_path.open("wb") as log_file:
        process = subprocess.Popen(
            [sys.executable, CURRENT_VALIDATOR_SCRIPT],
            cwd=root,
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            returncode = process.wait(timeout=120)
        except subprocess.TimeoutExpired:
            _terminate_process_group(process)
            elapsed = round(time.perf_counter() - started, 3)
            errors.append(f"smoke validator timeout: {CURRENT_VALIDATOR}: {_tail(log_path)}")
            return errors, elapsed
    elapsed = round(time.perf_counter() - started, 3)
    if returncode != 0:
        errors.append(f"smoke validator failed: {CURRENT_VALIDATOR}: {_tail(log_path)}")
    else:
        print(f"passed {CURRENT_VALIDATOR} in {elapsed:.3f}s", flush=True)
    return errors, elapsed


def _validate_no_smoke_log_leaks(root: Path) -> list[str]:
    leaks = sorted(root.rglob(".smoke-*"))
    return [f"smoke log leaked into extracted project: {path}" for path in leaks]


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait(timeout=5)
    except Exception:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except Exception:
            process.kill()


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _tail(path: Path, limit: int = 4000) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    return data[-limit:].decode("utf-8", errors="replace")


if __name__ == "__main__":
    main()
