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


VERSION = "V3.1.9"
CURRENT_VALIDATOR = "validate_multi_day_label_factory_v3_1"
CURRENT_VALIDATOR_SCRIPT = "scripts/validate_multi_day_label_factory_v3_1.py"
EXPECTED_ROWS = {"1m": 10080, "5m": 2016, "15m": 672, "1h": 168}
OUTPUTS = {
    timeframe: f"data/research/v3_1/labels/forward_returns/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}/window=2024-01-15_2024-01-21/labels.parquet"
    for timeframe in EXPECTED_ROWS
}
ESSENTIAL_ENTRIES = [
    "src/galapagos/labels/multi_day_validation.py",
    "src/galapagos/labels/multi_day_config.py",
    CURRENT_VALIDATOR_SCRIPT,
    "reports/manifests/multi_day_label_factory_v3_1_manifest.json",
    "reports/labels/multi_day_label_factory_v3_1.json",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_summary.md",
    *OUTPUTS.values(),
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
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
    "data/research/v3_1/datasets/",
    "data/research/v3_1/ml/",
    "data/research/v3_1/backtests/",
]
FORBIDDEN_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}
SAFETY_FALSE_FLAGS = [
    "trading_enabled",
    "backtest_enabled",
    "orders_enabled",
    "strategy_enabled",
    "execution_enabled",
    "dataset_enabled",
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
    label_row_counts: dict[str, int] = {}
    current_validator_seconds: float | None = None
    forbidden_entries: list[str] = []

    with tempfile.TemporaryDirectory(prefix="galapagos_v3_1_9_smoke_") as tmp:
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
        label_errors, label_row_counts = _validate_label_outputs(extracted_root)
        errors.extend(label_errors)
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
        "label_row_counts": label_row_counts,
        "label_schema_strict": not any(error.startswith("label schema mismatch") for error in errors),
        "forbidden_entries_found": forbidden_entries,
        "safety_flags_ok": not any("unsafe V3.1.9 flag active" in error for error in errors),
        "correction_version_ok": not any("correction_version" in error for error in errors),
        "smoke_duration_seconds": smoke_duration,
        "errors": errors,
        "warnings": warnings,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_smoke_test_v3_1_9.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    Path("reports/zip_smoke_test_v3_1_9.md").write_text(
        "# Smoke ZIP V3.1.9\n\n"
        f"- Statut : `{payload['smoke_test_passed']}`\n"
        f"- Validateur courant : `{payload['current_validator_run']}`\n"
        f"- Validateurs historiques relances : `{payload['historical_validators_run']}`\n"
        f"- Checks historiques par manifest/artefacts : `{payload['historical_validators_checked_by_manifest_only']}`\n"
        f"- Schema labels strict : `{payload['label_schema_strict']}`\n"
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
    manifest = _read_json(root / "reports/manifests/multi_day_label_factory_v3_1_manifest.json")
    report = _read_json(root / "reports/labels/multi_day_label_factory_v3_1.json")
    project_state_text = (root / "reports/PROJECT_STATE.json").read_text(encoding="utf-8")
    latest_summary = (root / "reports/current/latest_summary.md").read_text(encoding="utf-8")
    project_state = json.loads(project_state_text)

    for name, payload in [("manifest", manifest), ("report", report)]:
        if payload.get("version") != "V3.1":
            errors.append(f"V3.1 {name} version mismatch")
        if payload.get("status") != "PASS":
            errors.append(f"V3.1 {name} status must be PASS")
        if payload.get("correction_version") is not None and payload.get("correction_version") != VERSION:
            errors.append(f"V3.1 {name} correction_version mismatch")

    if manifest.get("correction_version") is None or report.get("correction_version") is None:
        if VERSION not in project_state_text or VERSION not in latest_summary:
            errors.append("V3.1.9 must be documented in PROJECT_STATE/latest_summary when correction_version is absent")

    if project_state.get("candidate_version") != VERSION and VERSION not in latest_summary:
        errors.append("PROJECT_STATE/latest_summary must identify V3.1.9 as candidate")
    if project_state.get("last_validated_version") != "V3.0":
        errors.append("last_validated_version must remain V3.0")
    if "pending_external_audit" not in latest_summary and project_state.get("candidate_status") != "pending_external_audit":
        errors.append("V3.1.9 must remain pending_external_audit")

    outputs = manifest.get("outputs", {})
    for timeframe, expected in EXPECTED_ROWS.items():
        if outputs.get(timeframe, {}).get("rows") != expected:
            errors.append(f"manifest output rows mismatch: {timeframe}")
        if report.get("outputs", {}).get(timeframe, {}).get("rows") != expected:
            errors.append(f"report output rows mismatch: {timeframe}")

    safety = manifest.get("safety", {})
    for flag in SAFETY_FALSE_FLAGS:
        if safety.get(flag) is not False:
            errors.append(f"unsafe V3.1.9 flag active: {flag}")
    if safety.get("labels_enabled") is not True:
        errors.append("labels_enabled must be true for V3.1 labels context")

    lower_state = (project_state_text + "\n" + latest_summary).casefold()
    required_claims = [
        ("aucun trading",),
        ("aucun paper live",),
        ("aucun ordre",),
        ("aucun backtest",),
        ("aucun dataset ml v3.1",),
        ("aucun modele ml v3.1", "aucun modèle ml v3.1"),
    ]
    for alternatives in required_claims:
        if not any(claim in lower_state for claim in alternatives):
            errors.append(f"missing state safety claim: {alternatives[0]}")
    return errors


def _validate_label_outputs(root: Path) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    row_counts: dict[str, int] = {}
    sys.path.insert(0, str(root / "src"))
    try:
        import pandas as pd

        from galapagos.labels.schemas import LABEL_COLUMNS_V3_1
    except Exception as exc:
        return [f"failed to import V3.1 label schema in smoke: {exc}"], row_counts
    for timeframe, relative in OUTPUTS.items():
        path = root / relative
        if not path.exists():
            errors.append(f"missing V3.1 label parquet: {relative}")
            continue
        frame = pd.read_parquet(path)
        row_counts[timeframe] = len(frame)
        if list(frame.columns) != LABEL_COLUMNS_V3_1:
            errors.append(f"label schema mismatch: {timeframe}")
        if len(frame) != EXPECTED_ROWS[timeframe]:
            errors.append(f"row count mismatch: {timeframe}")
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
