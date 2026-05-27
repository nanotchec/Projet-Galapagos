from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.13"
LAST_VALIDATED_VERSION = "V9.12"
ZIP_NAME = "projet-galapagos-v9.13-audit-lite.zip"
ROOT = Path(".").resolve()

REPORT_PATHS = [
    Path("reports/manifests/h4_label_candidate_dataset_v9_13_manifest.json"),
    Path("reports/datasets/h4_label_candidate_dataset_v9_13.json"),
    Path("reports/datasets/h4_label_candidate_dataset_v9_13.md"),
    Path("reports/datasets/h4_label_candidate_dataset_v9_13_datacard.md"),
    Path("docs/h4_label_candidate_dataset_v9_13.md"),
    Path("reports/manifests/h4_label_candidate_offline_ml_v9_13_manifest.json"),
    Path("reports/ml/h4_label_candidate_offline_ml_v9_13.json"),
    Path("reports/ml/h4_label_candidate_offline_ml_v9_13.md"),
    Path("reports/ml/h4_label_candidate_offline_scores_v9_13.json"),
    Path("reports/ml/h4_label_candidate_offline_scores_v9_13.md"),
    Path("docs/h4_label_candidate_offline_ml_v9_13.md"),
]

AUDIT_PATHS = [
    Path("reports/audit_lite/v9_13_command_results.json"),
    Path("reports/audit_lite/v9_13_command_results.md"),
    Path("reports/audit_lite/v9_13_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_13_full_local_validation_attestation.md"),
    Path("reports/audit_lite/v9_13_artifact_inventory.json"),
    Path("reports/audit_lite/v9_13_artifact_inventory.md"),
    Path("reports/audit_lite/zip_size_report_v9_13.json"),
    Path("reports/audit_lite/zip_size_report_v9_13.md"),
    Path("reports/audit_lite/zip_audit_v9_13.json"),
    Path("reports/audit_lite/zip_audit_v9_13.md"),
    Path("reports/audit_lite/zip_smoke_v9_13.json"),
    Path("reports/audit_lite/zip_smoke_v9_13.md"),
]

INPUT_REPORTS = [
    Path("reports/labels/horizon_event_label_redesign_v9_12.json"),
    Path("reports/manifests/horizon_event_label_redesign_v9_12_manifest.json"),
    Path("reports/ml/refined_volnorm_labels_offline_ml_v9_8.json"),
    Path("reports/research_decisions/refined_volnorm_research_decision_gate_v9_10.json"),
    Path("reports/research_decisions/label_failure_analysis_v9_11.json"),
]

SCRIPT_PATHS = [
    Path("scripts/_bootstrap.py"),
    Path("scripts/run_h4_label_candidate_dataset_v9_13.py"),
    Path("scripts/validate_h4_label_candidate_dataset_v9_13.py"),
    Path("scripts/run_h4_label_candidate_offline_ml_v9_13.py"),
    Path("scripts/validate_h4_label_candidate_offline_ml_v9_13.py"),
    Path("scripts/release_audit_lite_zip_v9_13.py"),
    Path("scripts/audit_audit_lite_zip_v9_13.py"),
    Path("scripts/smoke_audit_lite_zip_v9_13.py"),
]

TEST_PATHS = [
    Path("tests/datasets/test_h4_label_candidate_dataset_v9_13.py"),
    Path("tests/validation/test_h4_label_candidate_dataset_v9_13_validator.py"),
    Path("tests/ml/test_h4_label_candidate_offline_ml_v9_13.py"),
    Path("tests/validation/test_h4_label_candidate_offline_ml_v9_13_validator.py"),
]

CODE_PATHS = [
    Path("src/galapagos/__init__.py"),
    Path("src/galapagos/data/__init__.py"),
    Path("src/galapagos/data/public_market/storage.py"),
    Path("src/galapagos/features/advanced_ohlcv_schemas.py"),
    Path("src/galapagos/features/ohlcv_trades_schemas.py"),
    Path("src/galapagos/features/ohlcv_trades_90d_schemas.py"),
    Path("src/galapagos/features/ohlcv_trades_1y_schemas.py"),
    Path("src/galapagos/features/refined_ohlcv_trades_schemas.py"),
    Path("src/galapagos/features/schemas.py"),
    Path("src/galapagos/labels/horizon_event_label_redesign_v9_12_schemas.py"),
    Path("src/galapagos/labels/schemas.py"),
    Path("src/galapagos/datasets/schemas.py"),
    Path("src/galapagos/datasets/h4_label_candidate_dataset_v9_13.py"),
    Path("src/galapagos/datasets/h4_label_candidate_dataset_v9_13_schemas.py"),
    Path("src/galapagos/datasets/h4_label_candidate_dataset_v9_13_validation.py"),
    Path("src/galapagos/datasets/h4_label_candidate_dataset_v9_13_datacard.py"),
    Path("src/galapagos/ml/h4_label_candidate_offline_ml_v9_13.py"),
    Path("src/galapagos/ml/h4_label_candidate_offline_ml_v9_13_metrics.py"),
    Path("src/galapagos/ml/h4_label_candidate_offline_ml_v9_13_quality.py"),
    Path("src/galapagos/ml/h4_label_candidate_offline_ml_v9_13_validation.py"),
    Path("src/galapagos/ml/offline_baselines.py"),
    Path("src/galapagos/ml/schemas.py"),
]

STATE_PATHS = [
    Path("reports/PROJECT_STATE.json"),
    Path("reports/PROJECT_STATE.md"),
    Path("reports/current/latest_metrics.json"),
    Path("reports/current/latest_metrics.md"),
    Path("reports/current/latest_summary.md"),
    Path("README.md"),
    Path("pyproject.toml"),
]

EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", "orders", "execution", "models", "checkpoints"}
EXCLUDED_NAMES = {".DS_Store", ".env", "Icon", "Icon\r"}
EXCLUDED_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".zip", ".pem", ".key"}
FORBIDDEN_PREFIXES = ["data/research/", "reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/", "checkpoints/"]


def main() -> int:
    _ensure_inputs()
    dataset_report = _read_json(Path("reports/datasets/h4_label_candidate_dataset_v9_13.json"))
    ml_report = _read_json(Path("reports/ml/h4_label_candidate_offline_ml_v9_13.json"))
    _write_state_surfaces(dataset_report, ml_report)
    _ensure_placeholders()
    _write_samples(dataset_report, ml_report)
    zip_bytes: int | None = None
    zip_paths: list[Path] = []
    final_bytes = 0
    for _ in range(20):
        _write_attestation(dataset_report, ml_report, zip_bytes)
        zip_paths = _collect_paths()
        _write_size_report(zip_paths, zip_bytes)
        _write_inventory(zip_paths, zip_bytes)
        zip_paths = _collect_paths()
        _write_zip(zip_paths)
        final_bytes = (ROOT / ZIP_NAME).stat().st_size
        if final_bytes == zip_bytes:
            break
        zip_bytes = final_bytes
    result = {
        "version": VERSION,
        "zip_name": ZIP_NAME,
        "zip_bytes": final_bytes,
        "included_files": len(zip_paths),
        "sidecars_created": False,
        "zip_fingerprints_created": False,
        "status": "PASS",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _ensure_inputs() -> None:
    required = [*REPORT_PATHS, *INPUT_REPORTS, *SCRIPT_PATHS, *TEST_PATHS, *CODE_PATHS, Path("pyproject.toml")]
    missing = [path.as_posix() for path in required if not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError(f"missing V9.13 audit-lite inputs: {missing}")


def _ensure_placeholders() -> None:
    placeholders = {
        "reports/audit_lite/v9_13_command_results.json": {"version": VERSION, "status": "PENDING_CAPTURE", "commands": [], "sidecars_created": False, "zip_fingerprints_created": False},
        "reports/audit_lite/zip_audit_v9_13.json": {"version": VERSION, "passed": False, "errors": [], "status": "PENDING_RUN"},
        "reports/audit_lite/zip_smoke_v9_13.json": {"version": VERSION, "passed": False, "errors": [], "status": "PENDING_RUN"},
    }
    for raw_path, payload in placeholders.items():
        path = Path(raw_path)
        if not (ROOT / path).exists():
            payload["created_at_utc"] = _utc_now()
            _write_json(path, payload)
    for raw_path, text in {
        "reports/audit_lite/v9_13_command_results.md": "# Commandes V9.13\n\nRapport en attente de capture finale.\n",
        "reports/audit_lite/zip_audit_v9_13.md": "# Audit ZIP V9.13\n\nRapport en attente d'execution.\n",
        "reports/audit_lite/zip_smoke_v9_13.md": "# Smoke ZIP V9.13\n\nRapport en attente d'execution.\n",
    }.items():
        path = Path(raw_path)
        if not (ROOT / path).exists():
            _write_text(path, text)


def _write_samples(dataset_report: dict[str, Any], ml_report: dict[str, Any]) -> None:
    for timeframe, output in dataset_report.get("outputs", {}).items():
        source = ROOT / output.get("path", "")
        if source.is_file():
            sample_dir = ROOT / "data/audit_lite/v9_13/datasets" / f"timeframe={timeframe}"
            sample_dir.mkdir(parents=True, exist_ok=True)
            pd.read_parquet(source, engine="pyarrow").head(200).to_parquet(sample_dir / "dataset_sample.parquet", index=False, engine="pyarrow")
    for timeframe, output in ml_report.get("outputs", {}).items():
        source = ROOT / output.get("path", "")
        if source.is_file():
            sample_dir = ROOT / "data/audit_lite/v9_13/ml_scores" / f"timeframe={timeframe}"
            sample_dir.mkdir(parents=True, exist_ok=True)
            pd.read_parquet(source, engine="pyarrow").head(400).to_parquet(sample_dir / "ml-scores_sample.parquet", index=False, engine="pyarrow")


def _write_attestation(dataset_report: dict[str, Any], ml_report: dict[str, Any], zip_bytes: int | None) -> None:
    command_results = _read_optional_json(Path("reports/audit_lite/v9_13_command_results.json"))
    commands = command_results.get("commands", [])
    payload = {
        "version": VERSION,
        "validation_scope": "full_local_plus_audit_lite_packaging",
        "created_at_utc": _utc_now(),
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "zip_name": ZIP_NAME,
        "zip_bytes": zip_bytes,
        "commands_executed": [item.get("command") for item in commands],
        "tests_passed": _commands_passed(commands, ["pytest"]),
        "dataset_validator_passed": _commands_passed(commands, ["validate_h4_label_candidate_dataset_v9_13.py"]),
        "ml_validator_passed": _commands_passed(commands, ["validate_h4_label_candidate_offline_ml_v9_13.py"]),
        "audit_lite_passed": _commands_passed(commands, ["audit_audit_lite_zip_v9_13.py"]),
        "smoke_audit_lite_passed": _commands_passed(commands, ["smoke_audit_lite_zip_v9_13.py"]),
        "dataset_decision": dataset_report["decision"],
        "ml_decision": ml_report["decision"],
        "global_decision": ml_report["global_decision"]["decision"],
        "no_trading": True,
        "no_paper_live": True,
        "no_orders": True,
        "no_backtest": True,
        "no_strategy": True,
        "no_actionable_signal": True,
        "no_persistent_model": True,
        "api_key_used": False,
        "private_endpoint_used": False,
        "no_sidecars": True,
        "no_zip_fingerprints": True,
    }
    _write_json(Path("reports/audit_lite/v9_13_full_local_validation_attestation.json"), payload)
    _write_text(
        Path("reports/audit_lite/v9_13_full_local_validation_attestation.md"),
        "# Attestation full locale V9.13\n\n"
        f"- Dataset : `{dataset_report['decision']}`.\n"
        f"- ML : `{ml_report['decision']}`.\n"
        f"- Decision globale : `{ml_report['global_decision']['decision']}`.\n"
        "- Aucun trading, paper live, ordre, backtest, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n",
    )


def _commands_passed(commands: list[dict[str, Any]], needles: list[str]) -> bool:
    return any(command.get("status") == "PASS" and all(needle in command.get("command", "") for needle in needles) for command in commands)


def _collect_paths() -> list[Path]:
    sample_paths = sorted(Path("data/audit_lite/v9_13").rglob("*.parquet")) if (ROOT / "data/audit_lite/v9_13").exists() else []
    explicit = [*REPORT_PATHS, *AUDIT_PATHS, *INPUT_REPORTS, *SCRIPT_PATHS, *TEST_PATHS, *CODE_PATHS, *STATE_PATHS, *sample_paths]
    return sorted({path for path in explicit if (ROOT / path).is_file() and _is_allowed(path)}, key=lambda item: item.as_posix())


def _write_zip(paths: list[Path]) -> None:
    zip_path = ROOT / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in paths:
            archive.write(ROOT / path, arcname=path.as_posix())


def _write_inventory(paths: list[Path], zip_bytes: int | None) -> None:
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes": zip_bytes,
        "files_count": len(paths),
        "files": [path.as_posix() for path in paths],
        "forbidden_absences_verified": _forbidden_absence_checks(paths),
        "sidecars_created": False,
        "zip_fingerprints_created": False,
        "safety_flags": _safety(),
    }
    _write_json(Path("reports/audit_lite/v9_13_artifact_inventory.json"), payload)
    _write_text(Path("reports/audit_lite/v9_13_artifact_inventory.md"), f"# Inventaire audit-lite V9.13\n\n- ZIP : `{ZIP_NAME}`.\n- Fichiers inclus : `{len(paths)}`.\n- Taille ZIP : `{zip_bytes}`.\n- Exclusions : data/research full, backtests, strategies, ordres, execution, modeles, caches, secrets, sidecars SHA256 et empreintes ZIP.\n")


def _write_size_report(paths: list[Path], zip_bytes: int | None) -> None:
    payload = {"version": VERSION, "created_at_utc": _utc_now(), "zip_name": ZIP_NAME, "zip_bytes": zip_bytes, "included_files": len(paths), "sidecars_created": False, "zip_fingerprints_created": False}
    _write_json(Path("reports/audit_lite/zip_size_report_v9_13.json"), payload)
    _write_text(Path("reports/audit_lite/zip_size_report_v9_13.md"), f"# Taille ZIP V9.13\n\n- ZIP : `{ZIP_NAME}`.\n- Taille bytes : `{zip_bytes}`.\n- Fichiers inclus : `{len(paths)}`.\n")


def _write_state_surfaces(dataset_report: dict[str, Any], ml_report: dict[str, Any]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "direction": "h4_label_candidate_dataset_ml_diagnostic",
        "dataset_decision_v9_13": dataset_report["decision"],
        "ml_decision_v9_13": ml_report["decision"],
        "global_decision_v9_13": ml_report["global_decision"]["decision"],
        "target_name": "up_down_flat_volnorm_h4",
        "no_trading": True,
        "no_paper_live": True,
        "no_orders": True,
        "no_backtest": True,
        "no_strategy": True,
        "no_actionable_signal": True,
        "no_persistent_model": True,
        "api_key_used": False,
        "private_endpoint_used": False,
        "no_sidecars": True,
        "no_zip_fingerprints": True,
    }
    state_path = ROOT / "reports/PROJECT_STATE.json"
    state = _read_json(Path("reports/PROJECT_STATE.json")) if state_path.exists() else {}
    state.update(metrics)
    _write_json(Path("reports/PROJECT_STATE.json"), state)
    _write_json(Path("reports/current/latest_metrics.json"), metrics)
    summary = (
        "# Synthese courante - V9.13\n\n"
        "- Derniere version validee : `V9.12`.\n"
        "- Candidate : `V9.13`.\n"
        "- Statut : `pending_external_audit`.\n"
        "- Direction : dataset + diagnostic ML offline du label h4.\n"
        f"- Dataset : `{dataset_report['decision']}`.\n"
        f"- ML : `{ml_report['decision']}`.\n"
        f"- Decision globale : `{ml_report['global_decision']['decision']}`.\n"
        "- Aucun trading, paper live, ordre, backtest, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n"
    )
    _write_text(Path("reports/PROJECT_STATE.md"), summary)
    _write_text(Path("reports/current/latest_summary.md"), summary)
    _write_text(Path("reports/current/latest_metrics.md"), summary)
    _write_text(Path("README.md"), "# Projet Galapagos\n\n- Derniere version validee : V9.12.\n- Candidate : V9.13, dataset + diagnostic ML offline du label h4.\n- Aucun trading, ordre, backtest, strategie, signal actionnable, modele persistant, API privee ou cle API.\n- Aucun sidecar et aucune empreinte ZIP.\n")


def _forbidden_absence_checks(paths: list[Path]) -> dict[str, bool]:
    texts = [path.as_posix() for path in paths]
    names = [path.name for path in paths]
    suffixes = [path.suffix.casefold() for path in paths]
    return {
        "ds_store_absent": ".DS_Store" not in names,
        "icon_absent": "Icon" not in names and "Icon\r" not in names,
        "full_data_research_absent": not any(text.startswith("data/research/") for text in texts),
        "backtests_absent": not any(text.startswith("reports/backtests/") for text in texts),
        "strategies_absent": not any(text.startswith("reports/strategies/") for text in texts),
        "orders_absent": not any(text.startswith("orders/") for text in texts),
        "execution_absent": not any(text.startswith("execution/") for text in texts),
        "models_absent": not any(text.startswith("models/") for text in texts),
        "persistent_models_absent": not any(suffix in {".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt"} for suffix in suffixes),
        "secret_files_absent": not any(path.name == ".env" or path.suffix.casefold() in {".pem", ".key"} for path in paths),
        "sidecars_absent": not any(text.endswith(".sha256.json") or text.endswith(".sha256.txt") for text in texts),
    }


def _safety() -> dict[str, bool]:
    return {"no_trading": True, "no_paper_live": True, "no_orders": True, "no_backtest": True, "no_strategy": True, "no_actionable_signal": True, "no_persistent_model": True, "api_key_used": False, "private_endpoint_used": False, "no_sidecars": True, "no_zip_fingerprints": True}


def _is_allowed(path: Path) -> bool:
    text = path.as_posix()
    if any(text.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return False
    if set(path.parts) & EXCLUDED_PARTS:
        return False
    if path.name in EXCLUDED_NAMES:
        return False
    if text.endswith(".sha256.json") or text.endswith(".sha256.txt"):
        return False
    return path.suffix.casefold() not in EXCLUDED_SUFFIXES


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _read_optional_json(path: Path) -> dict[str, Any]:
    full = ROOT / path
    if not full.exists():
        return {}
    return json.loads(full.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    full = ROOT / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    full = ROOT / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
