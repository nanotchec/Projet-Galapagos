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


VERSION = "V3.2.1"
CURRENT_VALIDATOR = "validate_multi_day_offline_supervised_dataset_v3_2"
CURRENT_VALIDATOR_SCRIPT = "scripts/validate_multi_day_offline_supervised_dataset_v3_2.py"
EXPECTED_ROWS = {"1m": 10080, "5m": 2016, "15m": 672, "1h": 168}
EXPECTED_SPLITS = {
    "1m": {"train": 6048, "validation": 2016, "test": 2016},
    "5m": {"train": 1209, "validation": 403, "test": 404},
    "15m": {"train": 403, "validation": 134, "test": 135},
    "1h": {"train": 100, "validation": 33, "test": 35},
}
DATASET_OUTPUTS = {
    timeframe: f"data/research/v3_2/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}/window=2024-01-15_2024-01-21/dataset.parquet"
    for timeframe in EXPECTED_ROWS
}
SPLIT_OUTPUTS = {
    timeframe: f"data/research/v3_2/datasets/offline_supervised/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}/window=2024-01-15_2024-01-21/splits.parquet"
    for timeframe in EXPECTED_ROWS
}
ESSENTIAL_ENTRIES = [
    "src/galapagos/datasets/multi_day.py",
    "src/galapagos/datasets/multi_day_validation.py",
    "src/galapagos/datasets/multi_day_quality.py",
    "src/galapagos/datasets/multi_day_datacard.py",
    CURRENT_VALIDATOR_SCRIPT,
    "reports/manifests/multi_day_offline_supervised_dataset_v3_2_manifest.json",
    "reports/datasets/multi_day_offline_supervised_dataset_v3_2.json",
    "reports/datasets/multi_day_offline_supervised_dataset_v3_2_datacard.md",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_summary.md",
    *DATASET_OUTPUTS.values(),
    *SPLIT_OUTPUTS.values(),
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
    "data/research/v3_2/ml/",
    "data/research/v3_2/backtests/",
    "data/research/v3_2/strategies/",
]
FORBIDDEN_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}
SAFETY_FALSE_FLAGS = [
    "trading_enabled",
    "backtest_enabled",
    "orders_enabled",
    "strategy_enabled",
    "execution_enabled",
    "ml_enabled",
]


def main() -> None:
    started = time.perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    zip_path = Path(args.zip).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    dataset_row_counts: dict[str, int] = {}
    split_counts: dict[str, dict[str, int]] = {}
    current_validator_seconds: float | None = None
    forbidden_entries: list[str] = []

    with tempfile.TemporaryDirectory(prefix="galapagos_v3_2_smoke_") as tmp:
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
        errors.extend(_validate_state_manifest_and_report(extracted_root))
        dataset_errors, dataset_row_counts, split_counts = _validate_dataset_outputs(extracted_root)
        errors.extend(dataset_errors)
        validator_errors, current_validator_seconds = _run_current_validator(extracted_root, smoke_logs)
        errors.extend(validator_errors)
        errors.extend(_validate_no_smoke_log_leaks(extracted_root))

    smoke_duration = round(time.perf_counter() - started, 3)
    payload = {
        "version": VERSION,
        "smoke_test_passed": not errors,
        "zip_path": str(zip_path),
        "current_validator_run": CURRENT_VALIDATOR,
        "current_validator_timing_seconds": current_validator_seconds,
        "historical_validators_run": False,
        "historical_validators_checked_by_manifest_only": True,
        "dataset_row_counts": dataset_row_counts,
        "split_counts": split_counts,
        "dataset_schema_strict": not any(error.startswith("dataset schema mismatch") for error in errors),
        "forbidden_entries_found": forbidden_entries,
        "safety_flags_ok": not any("unsafe V3.2 flag active" in error for error in errors),
        "smoke_duration_seconds": smoke_duration,
        "errors": errors,
        "warnings": warnings,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_smoke_test_v3_2_1.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_smoke_test_v3_2_1.md").write_text(
        "# Smoke ZIP V3.2.1\n\n"
        f"- Statut : `{payload['smoke_test_passed']}`\n"
        f"- Validateur courant : `{payload['current_validator_run']}`\n"
        f"- Validateurs historiques relancés : `{payload['historical_validators_run']}`\n"
        f"- Schema dataset strict : `{payload['dataset_schema_strict']}`\n"
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
            errors.append(f"forbidden model artifact: {name}")
    for prefix in FORBIDDEN_PREFIXES:
        if any(name.startswith(prefix) for name in names):
            errors.append(f"forbidden zip prefix: {prefix}")
    return errors


def _validate_essential_entries(names: list[str]) -> list[str]:
    name_set = set(names)
    return [f"missing essential entry: {entry}" for entry in ESSENTIAL_ENTRIES if entry not in name_set]


def _validate_state_manifest_and_report(root: Path) -> list[str]:
    errors: list[str] = []
    manifest = _read_json(root / "reports/manifests/multi_day_offline_supervised_dataset_v3_2_manifest.json")
    report = _read_json(root / "reports/datasets/multi_day_offline_supervised_dataset_v3_2.json")
    project_state_text = (root / "reports/PROJECT_STATE.json").read_text(encoding="utf-8")
    latest_summary = (root / "reports/current/latest_summary.md").read_text(encoding="utf-8")
    project_state = json.loads(project_state_text)
    if manifest != report:
        errors.append("V3.2 report JSON must match manifest")
    if manifest.get("version") not in {"V3.2", VERSION} or report.get("version") not in {"V3.2", VERSION}:
        errors.append("V3.2 manifest/report version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V3.2 manifest status must be PASS")
    if project_state.get("candidate_version") != VERSION and VERSION not in latest_summary:
        errors.append("PROJECT_STATE/latest_summary must identify V3.2.1 as candidate")
    if project_state.get("last_validated_version") != "V3.1.10":
        errors.append("last_validated_version must be V3.1.10")
    if "pending_external_audit" not in latest_summary and project_state.get("candidate_status") != "pending_external_audit":
        errors.append("V3.2 must remain pending_external_audit")
    safety = manifest.get("safety", {})
    for flag in SAFETY_FALSE_FLAGS:
        if safety.get(flag) is not False:
            errors.append(f"unsafe V3.2 flag active: {flag}")
    if safety.get("labels_enabled") is not True or safety.get("dataset_enabled") is not True:
        errors.append("labels_enabled and dataset_enabled must be true for V3.2 dataset context")
    for timeframe, expected in EXPECTED_ROWS.items():
        if manifest.get("outputs", {}).get(timeframe, {}).get("rows") != expected:
            errors.append(f"manifest output rows mismatch: {timeframe}")
    lower_state = (project_state_text + "\n" + latest_summary).casefold()
    for claim in ["aucun trading", "aucun paper live", "aucun ordre", "aucun backtest", "aucun ml v3.2", "aucun modele ml v3.2"]:
        if claim not in lower_state and claim.replace("modele", "modèle") not in lower_state:
            errors.append(f"missing state safety claim: {claim}")
    return errors


def _validate_dataset_outputs(root: Path) -> tuple[list[str], dict[str, int], dict[str, dict[str, int]]]:
    errors: list[str] = []
    row_counts: dict[str, int] = {}
    split_counts: dict[str, dict[str, int]] = {}
    sys.path.insert(0, str(root / "src"))
    try:
        import pandas as pd

        from galapagos.datasets.schemas import DATASET_COLUMNS_V3_2
    except Exception as exc:
        return [f"failed to import V3.2 dataset schema in smoke: {exc}"], row_counts, split_counts
    for timeframe, relative in DATASET_OUTPUTS.items():
        path = root / relative
        split_path = root / SPLIT_OUTPUTS[timeframe]
        if not path.exists():
            errors.append(f"missing V3.2 dataset parquet: {relative}")
            continue
        if not split_path.exists():
            errors.append(f"missing V3.2 split parquet: {SPLIT_OUTPUTS[timeframe]}")
            continue
        frame = pd.read_parquet(path)
        split_frame = pd.read_parquet(split_path)
        row_counts[timeframe] = len(frame)
        split_counts[timeframe] = {key: int(value) for key, value in frame["split"].value_counts().to_dict().items()}
        if list(frame.columns) != DATASET_COLUMNS_V3_2:
            errors.append(f"dataset schema mismatch: {timeframe}")
        if len(frame) != EXPECTED_ROWS[timeframe]:
            errors.append(f"row count mismatch: {timeframe}")
        if split_counts[timeframe] != EXPECTED_SPLITS[timeframe]:
            errors.append(f"split counts mismatch: {timeframe}")
        if len(split_frame) != len(frame):
            errors.append(f"split file row count mismatch: {timeframe}")
    return errors, row_counts, split_counts


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
