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


VERSION = "V3.3"
CURRENT_VALIDATOR = "validate_multi_day_offline_ml_research_v3_3"
CURRENT_VALIDATOR_SCRIPT = "scripts/validate_multi_day_offline_ml_research_v3_3.py"
TIMEFRAMES = ["1m", "5m", "15m", "1h"]
DATASET_ROWS = {"1m": 10080, "5m": 2016, "15m": 672, "1h": 168}
SCORE_OUTPUTS = {
    timeframe: f"data/research/v3_3/ml/offline_research/source=binance_archive/market_type=spot/symbol=BTCUSDT/timeframe={timeframe}/window=2024-01-15_2024-01-21/ml-scores.parquet"
    for timeframe in TIMEFRAMES
}
ESSENTIAL_ENTRIES = [
    "src/galapagos/ml/multi_day.py",
    "src/galapagos/ml/multi_day_validation.py",
    "src/galapagos/ml/multi_day_metrics.py",
    "src/galapagos/ml/multi_day_quality.py",
    CURRENT_VALIDATOR_SCRIPT,
    "reports/manifests/multi_day_offline_ml_research_v3_3_manifest.json",
    "reports/ml/multi_day_offline_ml_research_v3_3.json",
    "reports/ml/multi_day_offline_research_scores_v3_3.json",
    "reports/PROJECT_STATE.json",
    "reports/current/latest_summary.md",
    *SCORE_OUTPUTS.values(),
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
    "data/research/v3_3/backtests/",
    "data/research/v3_3/strategies/",
    "data/research/v3_3/orders/",
]
FORBIDDEN_SUFFIXES = {".pkl", ".pickle", ".joblib", ".ckpt", ".pt", ".pth", ".onnx"}
SAFETY_FALSE_FLAGS = [
    "trading_enabled",
    "backtest_enabled",
    "orders_enabled",
    "strategy_enabled",
    "execution_enabled",
]


def main() -> None:
    started = time.perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    args = parser.parse_args()
    zip_path = Path(args.zip).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    score_row_counts: dict[str, int] = {}
    current_validator_seconds: float | None = None
    forbidden_entries: list[str] = []

    with tempfile.TemporaryDirectory(prefix="galapagos_v3_3_smoke_") as tmp:
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
        validator_errors, current_validator_seconds = _run_current_validator(extracted_root, smoke_logs)
        errors.extend(validator_errors)
        score_errors, score_row_counts = _validate_score_outputs(extracted_root)
        errors.extend(score_errors)
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
        "score_row_counts": score_row_counts,
        "ml_score_schema_strict": not any(error.startswith("ML score schema mismatch") for error in errors),
        "forbidden_entries_found": forbidden_entries,
        "safety_flags_ok": not any("unsafe V3.3 flag active" in error for error in errors),
        "smoke_duration_seconds": smoke_duration,
        "errors": errors,
        "warnings": warnings,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/zip_smoke_test_v3_3.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path("reports/zip_smoke_test_v3_3.md").write_text(
        "# Smoke ZIP V3.3\n\n"
        f"- Statut : `{payload['smoke_test_passed']}`\n"
        f"- Validateur courant : `{payload['current_validator_run']}`\n"
        f"- Validateurs historiques relances : `{payload['historical_validators_run']}`\n"
        f"- Schema ML strict : `{payload['ml_score_schema_strict']}`\n"
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
    return [f"missing essential entry: {entry}" for entry in ESSENTIAL_ENTRIES if entry not in name_set]


def _validate_state_manifest_and_report(root: Path) -> list[str]:
    errors: list[str] = []
    manifest = _read_json(root / "reports/manifests/multi_day_offline_ml_research_v3_3_manifest.json")
    report = _read_json(root / "reports/ml/multi_day_offline_ml_research_v3_3.json")
    project_state_text = (root / "reports/PROJECT_STATE.json").read_text(encoding="utf-8")
    latest_summary = (root / "reports/current/latest_summary.md").read_text(encoding="utf-8")
    project_state = json.loads(project_state_text)
    if manifest != report:
        errors.append("V3.3 report JSON must match manifest")
    if manifest.get("version") != VERSION or report.get("version") != VERSION:
        errors.append("V3.3 manifest/report version mismatch")
    if manifest.get("status") != "PASS":
        errors.append("V3.3 manifest status must be PASS")
    if project_state.get("candidate_version") != VERSION and VERSION not in latest_summary:
        errors.append("PROJECT_STATE/latest_summary must identify V3.3 as candidate")
    if project_state.get("last_validated_version") != "V3.2.1":
        errors.append("last_validated_version must be V3.2.1")
    if "pending_external_audit" not in latest_summary and project_state.get("candidate_status") != "pending_external_audit":
        errors.append("V3.3 must remain pending_external_audit")
    safety = manifest.get("safety", {})
    for flag in SAFETY_FALSE_FLAGS:
        if safety.get(flag) is not False:
            errors.append(f"unsafe V3.3 flag active: {flag}")
    if safety.get("ml_enabled") is not True or safety.get("labels_enabled") is not True or safety.get("dataset_enabled") is not True:
        errors.append("ml_enabled, labels_enabled and dataset_enabled must be true for V3.3 offline research context")
    lower_state = (project_state_text + "\n" + latest_summary).casefold()
    for claim in ["aucun trading", "aucun paper live", "aucun ordre", "aucun backtest", "aucune strategie"]:
        if claim not in lower_state and claim.replace("strategie", "stratégie") not in lower_state:
            errors.append(f"missing state safety claim: {claim}")
    return errors


def _validate_score_outputs(root: Path) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    row_counts: dict[str, int] = {}
    sys.path.insert(0, str(root / "src"))
    try:
        import pandas as pd

        from galapagos.ml.schemas import ML_SCORE_COLUMNS_V3_3, MODEL_NAMES_V3_3
    except Exception as exc:
        return [f"failed to import V3.3 ML schema in smoke: {exc}"], row_counts
    for timeframe, relative in SCORE_OUTPUTS.items():
        path = root / relative
        if not path.exists():
            errors.append(f"missing V3.3 score parquet: {relative}")
            continue
        frame = pd.read_parquet(path)
        row_counts[timeframe] = len(frame)
        if list(frame.columns) != ML_SCORE_COLUMNS_V3_3:
            errors.append(f"ML score schema mismatch: {timeframe}")
        if set(frame["model_name"].unique()) != set(MODEL_NAMES_V3_3):
            errors.append(f"ML score models mismatch: {timeframe}")
        if set(frame["target_name"].unique()) != {"up_down_flat_h1"}:
            errors.append(f"ML score target mismatch: {timeframe}")
        if len(frame) <= DATASET_ROWS[timeframe]:
            errors.append(f"ML score row count too small: {timeframe}")
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
