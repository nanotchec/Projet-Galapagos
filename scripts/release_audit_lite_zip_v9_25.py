from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.25"
ZIP_NAME = "projet-galapagos-v9.25-audit-lite.zip"
ROOT = Path(".").resolve()

BATCH_REPORTS = [Path(f"reports/data/aggtrades_post_v9_completion_batch{index:02d}_v9_25.json") for index in range(1, 7)]

REPORT_PATHS = [
    *BATCH_REPORTS,
    Path("reports/manifests/aggtrades_post_v9_completion_campaign_v9_25_manifest.json"),
    Path("reports/data/aggtrades_post_v9_completion_campaign_v9_25.json"),
    Path("reports/data/aggtrades_post_v9_completion_campaign_v9_25.md"),
    Path("docs/aggtrades_post_v9_completion_campaign_v9_25.md"),
]

AUDIT_PATHS = [
    Path("reports/audit_lite/v9_25_command_results.json"),
    Path("reports/audit_lite/v9_25_command_results.md"),
    Path("reports/audit_lite/v9_25_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_25_full_local_validation_attestation.md"),
    Path("reports/audit_lite/v9_25_artifact_inventory.json"),
    Path("reports/audit_lite/v9_25_artifact_inventory.md"),
    Path("reports/audit_lite/zip_size_report_v9_25.json"),
    Path("reports/audit_lite/zip_size_report_v9_25.md"),
    Path("reports/audit_lite/zip_audit_v9_25.json"),
    Path("reports/audit_lite/zip_audit_v9_25.md"),
    Path("reports/audit_lite/zip_smoke_v9_25.json"),
    Path("reports/audit_lite/zip_smoke_v9_25.md"),
]

INPUT_REPORTS = [
    Path("reports/data/aggtrades_post_v9_batch3_collection_v9_24.json"),
    Path("reports/data/aggtrades_post_v9_batch3_collection_v9_24.md"),
    Path("reports/manifests/aggtrades_post_v9_batch3_collection_v9_24_manifest.json"),
    Path("reports/data/aggtrades_post_v9_batch2_collection_v9_23.json"),
    Path("reports/data/aggtrades_post_v9_batch2_collection_v9_23.md"),
    Path("reports/manifests/aggtrades_post_v9_batch2_collection_v9_23_manifest.json"),
    Path("reports/data/aggtrades_post_v9_multi_batch_plan_v9_22.json"),
    Path("reports/data/aggtrades_post_v9_multi_batch_plan_v9_22.md"),
    Path("reports/manifests/aggtrades_post_v9_multi_batch_plan_v9_22_manifest.json"),
    Path("reports/data/aggtrades_post_v9_batch_expansion_v9_21.json"),
    Path("reports/data/aggtrades_post_v9_batch_collection_v9_20.json"),
    Path("reports/data/aggtrades_post_v9_pilot_collection_v9_19.json"),
    Path("reports/data/aggtrades_post_v9_collection_v9_18.json"),
    Path("reports/manifests/public_trades_1y_window_v8_2_manifest.json"),
    Path("reports/manifests/max_history_public_market_data_v5_0_manifest.json"),
]

SCRIPT_PATHS = [
    Path("scripts/_bootstrap.py"),
    Path("scripts/run_aggtrades_post_v9_completion_campaign_v9_25.py"),
    Path("scripts/validate_aggtrades_post_v9_completion_campaign_v9_25.py"),
    Path("scripts/release_audit_lite_zip_v9_25.py"),
    Path("scripts/audit_audit_lite_zip_v9_25.py"),
    Path("scripts/smoke_audit_lite_zip_v9_25.py"),
]

TEST_PATHS = [
    Path("tests/data/test_aggtrades_post_v9_completion_campaign_v9_25.py"),
    Path("tests/validation/test_aggtrades_post_v9_completion_campaign_v9_25_validator.py"),
]

CODE_PATHS = [
    Path("src/galapagos/__init__.py"),
    Path("src/galapagos/data/__init__.py"),
    Path("src/galapagos/data/aggtrades_post_v9_collection_v9_18.py"),
    Path("src/galapagos/data/aggtrades_post_v9_batch3_collection_v9_24.py"),
    Path("src/galapagos/data/aggtrades_post_v9_completion_campaign_v9_25.py"),
    Path("src/galapagos/data/aggtrades_post_v9_completion_campaign_v9_25_validation.py"),
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
FORBIDDEN_PREFIXES = [
    "data/raw/",
    "data/silver/",
    "data/research/",
    "data/gold/",
    "reports/backtests/",
    "reports/strategies/",
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
]


def main() -> int:
    _ensure_inputs()
    report = _read_json(Path("reports/data/aggtrades_post_v9_completion_campaign_v9_25.json"))
    _ensure_placeholders()
    zip_bytes_estimate: int | None = None
    zip_paths: list[Path] = []
    final_bytes = 0
    for _ in range(30):
        _write_attestation(report, zip_bytes_estimate)
        zip_paths = _collect_paths()
        _write_size_report(zip_paths, zip_bytes_estimate)
        zip_paths = _collect_paths()
        _write_inventory(zip_paths, zip_bytes_estimate)
        zip_paths = _collect_paths()
        _write_zip(zip_paths)
        final_bytes = (ROOT / ZIP_NAME).stat().st_size
        if final_bytes == zip_bytes_estimate:
            break
        zip_bytes_estimate = final_bytes
    result = {
        "version": VERSION,
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": final_bytes,
        "zip_bytes_is_authoritative": False,
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
        raise FileNotFoundError(f"missing V9.25 audit-lite inputs: {missing}")


def _ensure_placeholders() -> None:
    placeholders = {
        "reports/audit_lite/v9_25_command_results.json": {"version": VERSION, "status": "PENDING_CAPTURE", "commands": [], "sidecars_created": False, "zip_fingerprints_created": False},
        "reports/audit_lite/zip_audit_v9_25.json": {"version": VERSION, "passed": False, "errors": [], "status": "PENDING_RUN"},
        "reports/audit_lite/zip_smoke_v9_25.json": {"version": VERSION, "passed": False, "errors": [], "status": "PENDING_RUN"},
    }
    for raw_path, payload in placeholders.items():
        path = Path(raw_path)
        if not (ROOT / path).exists():
            payload["created_at_utc"] = _utc_now()
            _write_json(path, payload)
    texts = {
        "reports/audit_lite/v9_25_command_results.md": "# Commandes V9.25\n\nRapport en attente de capture finale.\n",
        "reports/audit_lite/zip_audit_v9_25.md": "# Audit ZIP V9.25\n\nRapport en attente d'execution.\n",
        "reports/audit_lite/zip_smoke_v9_25.md": "# Smoke ZIP V9.25\n\nRapport en attente d'execution.\n",
    }
    for raw_path, text in texts.items():
        path = Path(raw_path)
        if not (ROOT / path).exists():
            _write_text(path, text)


def _write_attestation(report: dict[str, Any], zip_bytes_estimate: int | None) -> None:
    command_results = _read_optional_json(Path("reports/audit_lite/v9_25_command_results.json"))
    commands = command_results.get("commands", [])
    summary = report["campaign_summary"]
    payload = {
        "version": VERSION,
        "validation_scope": "aggtrades_post_v9_remaining_window_completion_campaign_plus_audit_lite_packaging",
        "created_at_utc": _utc_now(),
        "last_validated_version": "V9.24",
        "candidate_version": VERSION,
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_bytes_estimate,
        "zip_bytes_is_authoritative": False,
        "commands_executed": [item.get("command") for item in commands],
        "tests_passed": _commands_passed(commands, ["pytest"]),
        "validator_passed": _commands_passed(commands, ["validate_aggtrades_post_v9_completion_campaign_v9_25.py"]),
        "audit_lite_passed": _commands_passed(commands, ["audit_audit_lite_zip_v9_25.py"]),
        "smoke_audit_lite_passed": _commands_passed(commands, ["smoke_audit_lite_zip_v9_25.py"]),
        "decision": report["decision"],
        **summary,
        "collection_executed": report["collection_executed"],
        "features_created": report["features_created"],
        "labels_created": report["labels_created"],
        "dataset_created": report["dataset_created"],
        "ml_executed": report["ml_executed"],
        "walk_forward_executed": report["walk_forward_executed"],
        "backtest_executed": report["backtest_executed"],
        **report["safety_flags"],
    }
    _write_json(Path("reports/audit_lite/v9_25_full_local_validation_attestation.json"), payload)
    _write_text(
        Path("reports/audit_lite/v9_25_full_local_validation_attestation.md"),
        "# Attestation full locale V9.25\n\n"
        f"- Decision : `{report['decision']}`.\n"
        f"- Lots planifies/executés/reussis/echoues : `{summary['batches_planned']}` / `{summary['batches_executed']}` / `{summary['batches_complete']}` / `{summary['batches_failed']}`.\n"
        f"- Jours telecharges/normalises/valides : `{summary['days_downloaded_total']}` / `{summary['days_normalized_total']}` / `{summary['days_complete_total']}`.\n"
        f"- Lignes nouvelles/cumulees : `{summary['total_rows_new']}` / `{summary['total_rows_cumulative']}`.\n"
        f"- Couverture locale reelle : `{summary['local_file_coverage_start']}` -> `{summary['local_file_coverage_end']}`.\n"
        f"- Couverture complete atteinte : `{summary['complete_collection_reached']}`.\n"
        "- Reseau limite a l'archive publique read-only `data.binance.vision` pour la campagne V9.25.\n"
        "- Aucun trading, paper live, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, API privee, cle API, client exchange authentifie ou websocket live.\n"
        "- Aucun sidecar, aucune empreinte ZIP et aucun champ zip_sha256.\n",
    )


def _commands_passed(commands: list[dict[str, Any]], needles: list[str]) -> bool:
    return any(command.get("status") == "PASS" and all(needle in command.get("command", "") for needle in needles) for command in commands)


def _collect_paths() -> list[Path]:
    explicit = [*REPORT_PATHS, *AUDIT_PATHS, *INPUT_REPORTS, *SCRIPT_PATHS, *TEST_PATHS, *CODE_PATHS, *STATE_PATHS]
    return sorted({path for path in explicit if (ROOT / path).is_file() and _is_allowed(path)}, key=lambda item: item.as_posix())


def _write_zip(paths: list[Path]) -> None:
    zip_path = ROOT / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in paths:
            archive.write(ROOT / path, arcname=path.as_posix())


def _write_inventory(paths: list[Path], zip_bytes_estimate: int | None) -> None:
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_bytes_estimate,
        "zip_bytes_is_authoritative": False,
        "files_count": len(paths),
        "files": [path.as_posix() for path in paths],
        "forbidden_absences_verified": _forbidden_absence_checks(paths),
        "sidecars_created": False,
        "zip_fingerprints_created": False,
        "safety_flags": _safety(),
    }
    _write_json(Path("reports/audit_lite/v9_25_artifact_inventory.json"), payload)
    _write_text(
        Path("reports/audit_lite/v9_25_artifact_inventory.md"),
        "# Inventaire audit-lite V9.25\n\n"
        f"- Fichiers inclus : `{len(paths)}`.\n"
        f"- ZIP bytes estimate : `{zip_bytes_estimate}`.\n"
        "- `zip_bytes_is_authoritative=false`.\n"
        "- Aucun raw/silver full, modele, backtest, ordre, sidecar ou empreinte ZIP.\n",
    )


def _write_size_report(paths: list[Path], zip_bytes_estimate: int | None) -> None:
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_bytes_estimate,
        "zip_bytes_is_authoritative": False,
        "source_files_count": len(paths),
        "source_bytes_total": sum((ROOT / path).stat().st_size for path in paths),
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    _write_json(Path("reports/audit_lite/zip_size_report_v9_25.json"), payload)
    _write_text(
        Path("reports/audit_lite/zip_size_report_v9_25.md"),
        "# Taille ZIP V9.25\n\n"
        f"- ZIP bytes estimate : `{zip_bytes_estimate}`.\n"
        "- `zip_bytes_is_authoritative=false`.\n"
        f"- Fichiers source : `{len(paths)}`.\n",
    )


def _forbidden_absence_checks(paths: list[Path]) -> dict[str, bool]:
    names = [path.as_posix() for path in paths]
    return {
        "no_data_raw": not any(name.startswith("data/raw/") for name in names),
        "no_data_silver": not any(name.startswith("data/silver/") for name in names),
        "no_data_research": not any(name.startswith("data/research/") for name in names),
        "no_backtests": not any(name.startswith("reports/backtests/") for name in names),
        "no_models": not any(name.startswith(("models/", "checkpoints/")) for name in names),
        "no_sidecars": not any(name.endswith((".sha256.json", ".sha256.txt")) for name in names),
        "no_zip_fingerprints": True,
    }


def _is_allowed(path: Path) -> bool:
    name = path.as_posix()
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    if path.name in EXCLUDED_NAMES:
        return False
    if path.suffix.casefold() in EXCLUDED_SUFFIXES:
        return False
    return not any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)


def _safety() -> dict[str, Any]:
    return {
        "no_trading": True,
        "no_paper_live": True,
        "no_orders": True,
        "no_backtest": True,
        "no_walk_forward": True,
        "no_strategy": True,
        "no_actionable_signal": True,
        "no_persistent_model": True,
        "api_key_used": False,
        "private_endpoint_used": False,
        "exchange_auth_used": False,
        "websocket_live_used": False,
        "no_sidecars": True,
        "no_zip_fingerprints": True,
    }


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
