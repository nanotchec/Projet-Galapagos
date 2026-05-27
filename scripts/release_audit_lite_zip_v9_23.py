from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.23"
ZIP_NAME = "projet-galapagos-v9.23-audit-lite.zip"
ROOT = Path(".").resolve()

REPORT_PATHS = [
    Path("reports/manifests/aggtrades_post_v9_batch2_collection_v9_23_manifest.json"),
    Path("reports/data/aggtrades_post_v9_batch2_collection_v9_23.json"),
    Path("reports/data/aggtrades_post_v9_batch2_collection_v9_23.md"),
    Path("docs/aggtrades_post_v9_batch2_collection_v9_23.md"),
]

AUDIT_PATHS = [
    Path("reports/audit_lite/v9_23_command_results.json"),
    Path("reports/audit_lite/v9_23_command_results.md"),
    Path("reports/audit_lite/v9_23_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_23_full_local_validation_attestation.md"),
    Path("reports/audit_lite/v9_23_artifact_inventory.json"),
    Path("reports/audit_lite/v9_23_artifact_inventory.md"),
    Path("reports/audit_lite/zip_size_report_v9_23.json"),
    Path("reports/audit_lite/zip_size_report_v9_23.md"),
    Path("reports/audit_lite/zip_audit_v9_23.json"),
    Path("reports/audit_lite/zip_audit_v9_23.md"),
    Path("reports/audit_lite/zip_smoke_v9_23.json"),
    Path("reports/audit_lite/zip_smoke_v9_23.md"),
]

INPUT_REPORTS = [
    Path("reports/data/aggtrades_post_v9_multi_batch_plan_v9_22.json"),
    Path("reports/data/aggtrades_post_v9_multi_batch_plan_v9_22.md"),
    Path("reports/manifests/aggtrades_post_v9_multi_batch_plan_v9_22_manifest.json"),
    Path("reports/data/aggtrades_post_v9_batch_expansion_v9_21.json"),
    Path("reports/data/aggtrades_post_v9_batch_expansion_v9_21.md"),
    Path("reports/manifests/aggtrades_post_v9_batch_expansion_v9_21_manifest.json"),
    Path("reports/data/aggtrades_post_v9_batch_collection_v9_20.json"),
    Path("reports/data/aggtrades_post_v9_batch_collection_v9_20.md"),
    Path("reports/manifests/aggtrades_post_v9_batch_collection_v9_20_manifest.json"),
    Path("reports/data/aggtrades_post_v9_pilot_collection_v9_19.json"),
    Path("reports/data/aggtrades_post_v9_pilot_collection_v9_19.md"),
    Path("reports/manifests/aggtrades_post_v9_pilot_collection_v9_19_manifest.json"),
    Path("reports/data/aggtrades_post_v9_collection_v9_18.json"),
    Path("reports/data/aggtrades_post_v9_collection_v9_18.md"),
    Path("reports/manifests/aggtrades_post_v9_collection_v9_18_manifest.json"),
    Path("reports/research_decisions/derivatives_history_collection_plan_v9_17.json"),
    Path("reports/manifests/derivatives_history_collection_plan_v9_17_manifest.json"),
    Path("reports/research_decisions/derivatives_window_extension_v9_16.json"),
    Path("reports/manifests/derivatives_window_extension_v9_16_manifest.json"),
    Path("reports/manifests/public_trades_1y_window_v8_2_manifest.json"),
    Path("reports/manifests/max_history_public_market_data_v5_0_manifest.json"),
]

SCRIPT_PATHS = [
    Path("scripts/_bootstrap.py"),
    Path("scripts/run_aggtrades_post_v9_batch2_collection_v9_23.py"),
    Path("scripts/validate_aggtrades_post_v9_batch2_collection_v9_23.py"),
    Path("scripts/release_audit_lite_zip_v9_23.py"),
    Path("scripts/audit_audit_lite_zip_v9_23.py"),
    Path("scripts/smoke_audit_lite_zip_v9_23.py"),
]

TEST_PATHS = [
    Path("tests/data/test_aggtrades_post_v9_batch2_collection_v9_23.py"),
    Path("tests/validation/test_aggtrades_post_v9_batch2_collection_v9_23_validator.py"),
]

CODE_PATHS = [
    Path("src/galapagos/__init__.py"),
    Path("src/galapagos/data/__init__.py"),
    Path("src/galapagos/data/aggtrades_post_v9_collection_v9_18.py"),
    Path("src/galapagos/data/aggtrades_post_v9_batch2_collection_v9_23.py"),
    Path("src/galapagos/data/aggtrades_post_v9_batch2_collection_v9_23_validation.py"),
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
    report = _read_json(Path("reports/data/aggtrades_post_v9_batch2_collection_v9_23.json"))
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
        raise FileNotFoundError(f"missing V9.23 audit-lite inputs: {missing}")


def _ensure_placeholders() -> None:
    placeholders = {
        "reports/audit_lite/v9_23_command_results.json": {"version": VERSION, "status": "PENDING_CAPTURE", "commands": [], "sidecars_created": False, "zip_fingerprints_created": False},
        "reports/audit_lite/zip_audit_v9_23.json": {"version": VERSION, "passed": False, "errors": [], "status": "PENDING_RUN"},
        "reports/audit_lite/zip_smoke_v9_23.json": {"version": VERSION, "passed": False, "errors": [], "status": "PENDING_RUN"},
    }
    for raw_path, payload in placeholders.items():
        path = Path(raw_path)
        if not (ROOT / path).exists():
            payload["created_at_utc"] = _utc_now()
            _write_json(path, payload)
    texts = {
        "reports/audit_lite/v9_23_command_results.md": "# Commandes V9.23\n\nRapport en attente de capture finale.\n",
        "reports/audit_lite/zip_audit_v9_23.md": "# Audit ZIP V9.23\n\nRapport en attente d'execution.\n",
        "reports/audit_lite/zip_smoke_v9_23.md": "# Smoke ZIP V9.23\n\nRapport en attente d'execution.\n",
    }
    for raw_path, text in texts.items():
        path = Path(raw_path)
        if not (ROOT / path).exists():
            _write_text(path, text)


def _write_attestation(report: dict[str, Any], zip_bytes_estimate: int | None) -> None:
    command_results = _read_optional_json(Path("reports/audit_lite/v9_23_command_results.json"))
    commands = command_results.get("commands", [])
    summary = report["batch_validation"]["summary"]
    reported_coverage = report["reported_cumulative_coverage"]
    local_coverage = report["local_file_coverage"]
    payload = {
        "version": VERSION,
        "validation_scope": "aggtrades_post_v9_batch2_collection_plus_audit_lite_packaging",
        "created_at_utc": _utc_now(),
        "last_validated_version": "V9.22",
        "candidate_version": VERSION,
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_bytes_estimate,
        "zip_bytes_is_authoritative": False,
        "commands_executed": [item.get("command") for item in commands],
        "tests_passed": _commands_passed(commands, ["pytest"]),
        "validator_passed": _commands_passed(commands, ["validate_aggtrades_post_v9_batch2_collection_v9_23.py"]),
        "audit_lite_passed": _commands_passed(commands, ["audit_audit_lite_zip_v9_23.py"]),
        "smoke_audit_lite_passed": _commands_passed(commands, ["smoke_audit_lite_zip_v9_23.py"]),
        "v9_23_decision": report["v9_23_decision"]["decision"],
        "mode": report["mode"],
        "batch_id": report["batch_window"]["batch_id"],
        "batch_start": report["batch_window"]["start"],
        "batch_end": report["batch_window"]["end"],
        "days_requested": summary["days_requested"],
        "days_attempted": summary["days_attempted"],
        "days_downloaded": summary["days_downloaded"],
        "days_normalized": summary["days_normalized"],
        "days_complete": summary["days_complete"],
        "days_failed": summary["days_failed"],
        "days_quarantined": summary["days_quarantined"],
        "total_rows": summary["total_rows"],
        "raw_bytes_total": summary["raw_bytes_total"],
        "silver_bytes_total": summary["silver_bytes_total"],
        "reported_cumulative_coverage_start": reported_coverage["reported_cumulative_coverage_start"],
        "reported_cumulative_coverage_end": reported_coverage["reported_cumulative_coverage_end"],
        "local_file_coverage_start": local_coverage["local_file_coverage_start"],
        "local_file_coverage_end": local_coverage["local_file_coverage_end"],
        "estimated_full_collection_rows": summary["estimated_full_collection_rows"],
        "estimated_full_collection_raw_bytes": summary["estimated_full_collection_raw_bytes"],
        "estimated_full_collection_runtime_seconds": summary["estimated_full_collection_runtime_seconds"],
        "collection_executed": report["collection_executed"],
        "complete_collection_reached": False,
        "features_created": report["features_created"],
        "labels_created": report["labels_created"],
        "dataset_created": report["dataset_created"],
        "ml_executed": report["ml_executed"],
        "walk_forward_executed": report["walk_forward_executed"],
        "backtest_executed": report["backtest_executed"],
        **report["safety_flags"],
    }
    _write_json(Path("reports/audit_lite/v9_23_full_local_validation_attestation.json"), payload)
    _write_text(
        Path("reports/audit_lite/v9_23_full_local_validation_attestation.md"),
        "# Attestation full locale V9.23\n\n"
        f"- Decision : `{report['v9_23_decision']['decision']}`.\n"
        f"- Mode : `{report['mode']}`.\n"
        f"- Batch : `{report['batch_window']['start']}` -> `{report['batch_window']['end']}`.\n"
        f"- Jours demandes/tentes/valides : `{summary['days_requested']}` / `{summary['days_attempted']}` / `{summary['days_complete']}`.\n"
        f"- Lignes/raw/silver : `{summary['total_rows']}` / `{summary['raw_bytes_total']}` / `{summary['silver_bytes_total']}`.\n"
        f"- Couverture cumulee declaree : `{reported_coverage['reported_cumulative_coverage_start']}` -> `{reported_coverage['reported_cumulative_coverage_end']}`.\n"
        f"- Couverture locale reelle : `{local_coverage['local_file_coverage_start']}` -> `{local_coverage['local_file_coverage_end']}`.\n"
        "- Couverture complete future : `False`.\n"
        "- Reseau limite a l'archive publique read-only `data.binance.vision` pour le batch V9.23.\n"
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
    _write_json(Path("reports/audit_lite/v9_23_artifact_inventory.json"), payload)
    _write_text(
        Path("reports/audit_lite/v9_23_artifact_inventory.md"),
        "# Inventaire audit-lite V9.23\n\n"
        f"- ZIP : `{ZIP_NAME}`.\n"
        f"- Fichiers inclus : `{len(paths)}`.\n"
        f"- Taille ZIP estimee non autoritative : `{zip_bytes_estimate}`.\n"
        "- Exclusions : data/raw, data/silver, data/research, data/gold, gros trades, backtests, strategies, ordres, execution, modeles, caches, secrets, `Icon`, sidecars SHA256 et empreintes ZIP.\n",
    )


def _write_size_report(paths: list[Path], zip_bytes_estimate: int | None) -> None:
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_bytes_estimate,
        "zip_bytes_is_authoritative": False,
        "included_files": len(paths),
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    _write_json(Path("reports/audit_lite/zip_size_report_v9_23.json"), payload)
    _write_text(Path("reports/audit_lite/zip_size_report_v9_23.md"), f"# Taille ZIP V9.23\n\n- ZIP : `{ZIP_NAME}`.\n- Taille bytes estimee non autoritative : `{zip_bytes_estimate}`.\n- Fichiers inclus : `{len(paths)}`.\n")


def _forbidden_absence_checks(paths: list[Path]) -> dict[str, bool]:
    texts = [path.as_posix() for path in paths]
    names = [path.name for path in paths]
    suffixes = [path.suffix.casefold() for path in paths]
    return {
        "ds_store_absent": ".DS_Store" not in names,
        "icon_absent": "Icon" not in names and "Icon\r" not in names,
        "data_raw_absent": not any(text.startswith("data/raw/") for text in texts),
        "data_silver_absent": not any(text.startswith("data/silver/") for text in texts),
        "data_research_absent": not any(text.startswith("data/research/") for text in texts),
        "data_gold_absent": not any(text.startswith("data/gold/") for text in texts),
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
        "network_used": False,
        "no_new_data_download": True,
        "no_ingestion_executed": True,
        "no_sidecars": True,
        "no_zip_fingerprints": True,
    }


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
