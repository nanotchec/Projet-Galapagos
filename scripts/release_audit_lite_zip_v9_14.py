from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.14"
LAST_VALIDATED_VERSION = "V9.13"
ZIP_NAME = "projet-galapagos-v9.14-audit-lite.zip"
ROOT = Path(".").resolve()

REPORT_PATHS = [
    Path("reports/manifests/feature_label_separability_v9_14_manifest.json"),
    Path("reports/research_decisions/feature_label_separability_v9_14.json"),
    Path("reports/research_decisions/feature_label_separability_v9_14.md"),
    Path("docs/feature_label_separability_v9_14.md"),
]

AUDIT_PATHS = [
    Path("reports/audit_lite/v9_14_command_results.json"),
    Path("reports/audit_lite/v9_14_command_results.md"),
    Path("reports/audit_lite/v9_14_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_14_full_local_validation_attestation.md"),
    Path("reports/audit_lite/v9_14_artifact_inventory.json"),
    Path("reports/audit_lite/v9_14_artifact_inventory.md"),
    Path("reports/audit_lite/zip_size_report_v9_14.json"),
    Path("reports/audit_lite/zip_size_report_v9_14.md"),
    Path("reports/audit_lite/zip_audit_v9_14.json"),
    Path("reports/audit_lite/zip_audit_v9_14.md"),
    Path("reports/audit_lite/zip_smoke_v9_14.json"),
    Path("reports/audit_lite/zip_smoke_v9_14.md"),
]

INPUT_REPORTS = [
    Path("reports/datasets/h4_label_candidate_dataset_v9_13.json"),
    Path("reports/ml/h4_label_candidate_offline_ml_v9_13.json"),
    Path("reports/ml/h4_label_candidate_offline_scores_v9_13.json"),
    Path("reports/labels/horizon_event_label_redesign_v9_12.json"),
    Path("reports/research_decisions/label_failure_analysis_v9_11.json"),
    Path("reports/research_decisions/refined_volnorm_research_decision_gate_v9_10.json"),
    Path("reports/ml/refined_volnorm_labels_offline_ml_v9_8.json"),
    Path("reports/ml/refined_volnorm_strict_walk_forward_v9_9.json"),
]

SCRIPT_PATHS = [
    Path("scripts/_bootstrap.py"),
    Path("scripts/run_feature_label_separability_v9_14.py"),
    Path("scripts/validate_feature_label_separability_v9_14.py"),
    Path("scripts/release_audit_lite_zip_v9_14.py"),
    Path("scripts/audit_audit_lite_zip_v9_14.py"),
    Path("scripts/smoke_audit_lite_zip_v9_14.py"),
]

TEST_PATHS = [
    Path("tests/research/test_feature_label_separability_v9_14.py"),
    Path("tests/validation/test_feature_label_separability_v9_14_validator.py"),
]

CODE_PATHS = [
    Path("src/galapagos/__init__.py"),
    Path("src/galapagos/research/feature_label_separability_v9_14.py"),
    Path("src/galapagos/research/feature_label_separability_v9_14_validation.py"),
    Path("src/galapagos/datasets/h4_label_candidate_dataset_v9_13_schemas.py"),
    Path("src/galapagos/features/refined_ohlcv_trades_schemas.py"),
    Path("src/galapagos/labels/horizon_event_label_redesign_v9_12_schemas.py"),
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
    report = _read_json(Path("reports/research_decisions/feature_label_separability_v9_14.json"))
    _ensure_placeholders()
    zip_bytes: int | None = None
    zip_paths: list[Path] = []
    final_bytes = 0
    for _ in range(30):
        _write_attestation(report, zip_bytes)
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
        raise FileNotFoundError(f"missing V9.14 audit-lite inputs: {missing}")


def _ensure_placeholders() -> None:
    placeholders = {
        "reports/audit_lite/v9_14_command_results.json": {"version": VERSION, "status": "PENDING_CAPTURE", "commands": [], "sidecars_created": False, "zip_fingerprints_created": False},
        "reports/audit_lite/zip_audit_v9_14.json": {"version": VERSION, "passed": False, "errors": [], "status": "PENDING_RUN"},
        "reports/audit_lite/zip_smoke_v9_14.json": {"version": VERSION, "passed": False, "errors": [], "status": "PENDING_RUN"},
    }
    for raw_path, payload in placeholders.items():
        path = Path(raw_path)
        if not (ROOT / path).exists():
            payload["created_at_utc"] = _utc_now()
            _write_json(path, payload)
    for raw_path, text in {
        "reports/audit_lite/v9_14_command_results.md": "# Commandes V9.14\n\nRapport en attente de capture finale.\n",
        "reports/audit_lite/zip_audit_v9_14.md": "# Audit ZIP V9.14\n\nRapport en attente d'execution.\n",
        "reports/audit_lite/zip_smoke_v9_14.md": "# Smoke ZIP V9.14\n\nRapport en attente d'execution.\n",
    }.items():
        path = Path(raw_path)
        if not (ROOT / path).exists():
            _write_text(path, text)


def _write_attestation(report: dict[str, Any], zip_bytes: int | None) -> None:
    command_results = _read_optional_json(Path("reports/audit_lite/v9_14_command_results.json"))
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
        "validator_passed": _commands_passed(commands, ["validate_feature_label_separability_v9_14.py"]),
        "audit_lite_passed": _commands_passed(commands, ["audit_audit_lite_zip_v9_14.py"]),
        "smoke_audit_lite_passed": _commands_passed(commands, ["smoke_audit_lite_zip_v9_14.py"]),
        "v9_14_decision": report["v9_14_decision"]["decision"],
        **report["safety_flags"],
    }
    _write_json(Path("reports/audit_lite/v9_14_full_local_validation_attestation.json"), payload)
    _write_text(
        Path("reports/audit_lite/v9_14_full_local_validation_attestation.md"),
        "# Attestation full locale V9.14\n\n"
        f"- Decision : `{report['v9_14_decision']['decision']}`.\n"
        "- Aucun trading, paper live, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun sidecar, aucune empreinte ZIP et aucun champ zip_sha256.\n",
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
    _write_json(Path("reports/audit_lite/v9_14_artifact_inventory.json"), payload)
    _write_text(Path("reports/audit_lite/v9_14_artifact_inventory.md"), f"# Inventaire audit-lite V9.14\n\n- ZIP : `{ZIP_NAME}`.\n- Fichiers inclus : `{len(paths)}`.\n- Taille ZIP : `{zip_bytes}`.\n- Exclusions : data/research full, backtests, strategies, ordres, execution, modeles, caches, secrets, `Icon`, sidecars SHA256 et empreintes ZIP.\n")


def _write_size_report(paths: list[Path], zip_bytes: int | None) -> None:
    payload = {"version": VERSION, "created_at_utc": _utc_now(), "zip_name": ZIP_NAME, "zip_bytes": zip_bytes, "included_files": len(paths), "sidecars_created": False, "zip_fingerprints_created": False}
    _write_json(Path("reports/audit_lite/zip_size_report_v9_14.json"), payload)
    _write_text(Path("reports/audit_lite/zip_size_report_v9_14.md"), f"# Taille ZIP V9.14\n\n- ZIP : `{ZIP_NAME}`.\n- Taille bytes : `{zip_bytes}`.\n- Fichiers inclus : `{len(paths)}`.\n")


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
    return {"no_trading": True, "no_paper_live": True, "no_orders": True, "no_backtest": True, "no_walk_forward": True, "no_strategy": True, "no_actionable_signal": True, "no_persistent_model": True, "api_key_used": False, "private_endpoint_used": False, "no_sidecars": True, "no_zip_fingerprints": True}


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
