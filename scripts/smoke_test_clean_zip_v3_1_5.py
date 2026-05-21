from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path


VERSION = "V3.1.5"
EXPECTED_ROWS = {"1m": 10080, "5m": 2016, "15m": 672, "1h": 168}
OUTPUTS = {
    timeframe: f"data/research/v3_1/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}/window=2024-01-15_2024-01-21/labels.parquet"
    for timeframe in EXPECTED_ROWS
}
ESSENTIAL_ENTRIES = [
    "src/galapagos/labels/multi_day_validation.py",
    "src/galapagos/labels/multi_day_config.py",
    "scripts/validate_multi_day_label_factory_v3_1.py",
    "reports/manifests/multi_day_label_factory_v3_1_manifest.json",
    "reports/labels/multi_day_label_factory_v3_1.json",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_summary.md",
]
FORBIDDEN_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
}
FORBIDDEN_PREFIXES = [
    "reports/backtests/",
    "reports/strategies/",
    "reports/signals/",
    "reports/predictions/",
    "models/",
    "checkpoints/",
    "orders/",
    "execution/",
    "data/research/v3_1/datasets/",
    "data/research/v3_1/ml/",
    "data/research/v3_1/backtests/",
]
FORBIDDEN_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}
VALIDATORS = [
    ("validate_public_market_ingestion_v2_3", "scripts/validate_public_market_ingestion_v2_3.py", 90),
    ("validate_ohlcv_resampling_v2_4", "scripts/validate_ohlcv_resampling_v2_4.py", 90),
    ("validate_causal_feature_store_v2_5", "scripts/validate_causal_feature_store_v2_5.py", 90),
    ("validate_label_factory_v2_6", "scripts/validate_clean_label_factory_v2_6.py", 90),
    ("validate_offline_supervised_dataset_v2_7", "scripts/validate_offline_supervised_dataset_v2_7.py", 90),
    ("validate_offline_ml_research_v2_8", "scripts/validate_offline_ml_research_v2_8.py", 120),
    ("validate_multi_day_public_market_data_v2_9", "scripts/validate_multi_day_public_market_data_v2_9.py", 120),
    ("validate_multi_day_causal_feature_store_v3_0", "scripts/validate_multi_day_causal_feature_store_v3_0.py", 120),
    ("validate_multi_day_label_factory_v3_1", "scripts/validate_multi_day_label_factory_v3_1.py", 120),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    zip_path = Path(args.zip).resolve()
    errors: list[str] = []
    validator_timings: dict[str, float] = {}
    leak_errors: list[str] = []

    with tempfile.TemporaryDirectory(prefix="galapagos_v3_1_5_smoke_") as tmp:
        tmp_path = Path(tmp)
        extracted_root = tmp_path / "extracted"
        smoke_logs = tmp_path / "smoke_logs"
        extracted_root.mkdir()
        smoke_logs.mkdir()
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            archive.extractall(extracted_root)
        errors.extend(_validate_zip_entries(names))
        errors.extend(_validate_essential_entries(names))
        errors.extend(_validate_state_and_safety(extracted_root))
        validator_errors, validator_timings = _run_validators(extracted_root, smoke_logs)
        errors.extend(validator_errors)
        leak_errors = _validate_no_smoke_log_leaks(extracted_root)
        errors.extend(leak_errors)
        errors.extend(_validate_label_outputs(extracted_root))

    payload = {
        "version": VERSION,
        "zip_path": str(zip_path),
        "smoke_test_passed": not errors,
        "smoke_validators_run": len(validator_timings),
        "smoke_failed_count": len(errors),
        "validator_timings_seconds": validator_timings,
        "validators_isolated_by_subprocess": True,
        "validators_run_before_parquet_checks": True,
        "parent_imports_pandas_before_validators": False,
        "smoke_logs_outside_extracted_root": True,
        "smoke_log_leaks_in_extracted_root": bool(leak_errors),
        "errors": errors,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_smoke_test_v3_1_5.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    Path("reports/zip_smoke_test_v3_1_5.md").write_text(
        "# Smoke ZIP V3.1.5\n\n"
        f"- Statut : `{payload['smoke_test_passed']}`\n"
        f"- Validateurs : `{payload['smoke_validators_run']}`\n"
        f"- Isolation subprocess : `{payload['validators_isolated_by_subprocess']}`\n"
        f"- Validateurs avant Parquet : `{payload['validators_run_before_parquet_checks']}`\n"
        f"- Import pandas avant validateurs : `{payload['parent_imports_pandas_before_validators']}`\n"
        f"- Logs hors root extrait : `{payload['smoke_logs_outside_extracted_root']}`\n"
        f"- Fuites `.smoke-*` : `{payload['smoke_log_leaks_in_extracted_root']}`\n"
        f"- Erreurs : `{payload['smoke_failed_count']}`\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


def _validate_zip_entries(names: list[str]) -> list[str]:
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


def _validate_label_outputs(root: Path) -> list[str]:
    errors: list[str] = []
    sys.path.insert(0, str(root / "src"))
    try:
        import pandas as pd

        from galapagos.labels.schemas import LABEL_COLUMNS_V3_1
    except Exception as exc:
        return [f"failed to import V3.1 label schema in smoke: {exc}"]
    for timeframe, relative in OUTPUTS.items():
        path = root / relative
        if not path.exists():
            errors.append(f"missing V3.1 label parquet: {relative}")
            continue
        frame = pd.read_parquet(path)
        if list(frame.columns) != LABEL_COLUMNS_V3_1:
            errors.append(f"label schema mismatch: {timeframe}")
        if len(frame) != EXPECTED_ROWS[timeframe]:
            errors.append(f"row count mismatch: {timeframe}")
    return errors


def _validate_state_and_safety(root: Path) -> list[str]:
    errors: list[str] = []
    manifest = _read_json(root / "reports/manifests/multi_day_label_factory_v3_1_manifest.json")
    report = _read_json(root / "reports/labels/multi_day_label_factory_v3_1.json")
    if manifest.get("correction_version") is not None and manifest.get("correction_version") != VERSION:
        errors.append("V3.1 manifest correction_version mismatch")
    if report.get("correction_version") is not None and report.get("correction_version") != VERSION:
        errors.append("V3.1 report correction_version mismatch")
    if manifest.get("correction_version") is None or report.get("correction_version") is None:
        summary = (root / "reports/current/latest_summary.md").read_text(encoding="utf-8")
        project_state = (root / "reports/PROJECT_STATE.json").read_text(encoding="utf-8")
        if VERSION not in summary or VERSION not in project_state:
            errors.append("V3.1.5 must be documented in PROJECT_STATE/latest_summary when correction_version is absent")
    safety = manifest.get("safety", {})
    for flag in [
        "trading_enabled",
        "backtest_enabled",
        "orders_enabled",
        "strategy_enabled",
        "execution_enabled",
        "dataset_enabled",
        "ml_enabled",
    ]:
        if safety.get(flag) is not False:
            errors.append(f"unsafe V3.1.5 flag active: {flag}")
    if safety.get("labels_enabled") is not True:
        errors.append("labels_enabled must be true for V3.1.5 labels context")
    return errors


def _run_validators(root: Path, smoke_logs: Path) -> tuple[list[str], dict[str, float]]:
    errors: list[str] = []
    timings: dict[str, float] = {}
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    for name, script, timeout_seconds in VALIDATORS:
        print(f"running {name}", flush=True)
        log_path = smoke_logs / f"{name}.log"
        started = time.perf_counter()
        try:
            with log_path.open("wb") as log_file:
                completed = subprocess.run(
                    [sys.executable, script],
                    cwd=root,
                    env=env,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    timeout=timeout_seconds,
                    check=False,
                )
        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - started
            timings[name] = round(elapsed, 3)
            print(f"timeout {name} after {elapsed:.3f}s", flush=True)
            errors.append(f"smoke validator timeout: {name}")
            continue
        elapsed = time.perf_counter() - started
        timings[name] = round(elapsed, 3)
        if completed.returncode != 0:
            print(f"failed {name} in {elapsed:.3f}s", flush=True)
            errors.append(f"smoke validator failed: {name}: {_tail(log_path)}")
            continue
        print(f"passed {name} in {elapsed:.3f}s", flush=True)
    return errors, timings


def _validate_no_smoke_log_leaks(root: Path) -> list[str]:
    return [f"smoke log leaked into extracted project: {path}" for path in sorted(root.glob(".smoke-*"))]


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _tail(path: Path, limit: int = 4000) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    return data[-limit:].decode("utf-8", errors="replace")


if __name__ == "__main__":
    main()
