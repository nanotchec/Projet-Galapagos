from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.30"
ZIP_NAME = "projet-galapagos-v9.30-audit-lite.zip"
ROOT = Path(".").resolve()

CORE_PATHS = [
    Path("scripts/_bootstrap.py"),
    Path("src/galapagos/data/aggtrades_post_v9_collection_v9_18.py"),
    Path("src/galapagos/data/aggtrades_post_v9_batch3_collection_v9_24.py"),
    Path("src/galapagos/data/aggtrades_post_v9_completion_campaign_v9_25.py"),
    Path("src/galapagos/data/aggtrades_post_v9_storage_recheck_resume_v9_27.py"),
    Path("src/galapagos/data/aggtrades_post_v9_bad_day_repair_v9_28.py"),
    Path("src/galapagos/data/aggtrades_5y_extension_plan_v9_30.py"),
    Path("src/galapagos/data/aggtrades_5y_extension_plan_v9_30_validation.py"),
    Path("scripts/run_aggtrades_5y_extension_plan_v9_30.py"),
    Path("scripts/validate_aggtrades_5y_extension_plan_v9_30.py"),
    Path("scripts/release_audit_lite_zip_v9_30.py"),
    Path("scripts/audit_audit_lite_zip_v9_30.py"),
    Path("scripts/smoke_audit_lite_zip_v9_30.py"),
    Path("tests/data/test_aggtrades_5y_extension_plan_v9_30.py"),
    Path("tests/validation/test_aggtrades_5y_extension_plan_v9_30_validator.py"),
    Path("reports/manifests/aggtrades_5y_extension_plan_v9_30_manifest.json"),
    Path("reports/data/aggtrades_5y_extension_plan_v9_30.json"),
    Path("reports/data/aggtrades_5y_extension_plan_v9_30.md"),
    Path("docs/aggtrades_5y_extension_plan_v9_30.md"),
]

PRIOR_REPORTS = [
    Path("reports/data/aggtrades_post_v9_full_coverage_validation_v9_29.json"),
    Path("reports/data/aggtrades_post_v9_full_coverage_validation_v9_29.md"),
    Path("reports/manifests/aggtrades_post_v9_full_coverage_validation_v9_29_manifest.json"),
    Path("reports/data/aggtrades_post_v9_bad_day_repair_v9_28.json"),
    Path("reports/data/aggtrades_post_v9_bad_day_repair_v9_28.md"),
    Path("reports/data/aggtrades_post_v9_bad_day_repair_2026_02_11_v9_28.json"),
    Path("reports/data/aggtrades_post_v9_bad_day_repair_2026_02_11_v9_28.md"),
    Path("reports/data/aggtrades_post_v9_final_tail_collection_v9_28.json"),
    Path("reports/data/aggtrades_post_v9_final_tail_collection_v9_28.md"),
    Path("reports/manifests/aggtrades_post_v9_bad_day_repair_v9_28_manifest.json"),
    Path("reports/data/aggtrades_post_v9_storage_recheck_resume_v9_27.json"),
    Path("reports/data/aggtrades_post_v9_storage_recheck_batch06_v9_27.json"),
    Path("reports/manifests/aggtrades_post_v9_storage_recheck_resume_v9_27_manifest.json"),
    Path("reports/data/aggtrades_post_v9_storage_resume_campaign_v9_26.json"),
    Path("reports/manifests/aggtrades_post_v9_storage_resume_campaign_v9_26_manifest.json"),
    Path("reports/data/aggtrades_post_v9_resume_campaign_v9_25_1.json"),
    Path("reports/manifests/aggtrades_post_v9_resume_campaign_v9_25_1_manifest.json"),
    Path("reports/data/aggtrades_post_v9_completion_campaign_v9_25.json"),
    Path("reports/manifests/aggtrades_post_v9_completion_campaign_v9_25_manifest.json"),
    Path("reports/data/aggtrades_post_v9_batch3_collection_v9_24.json"),
    Path("reports/manifests/aggtrades_post_v9_batch3_collection_v9_24_manifest.json"),
    Path("reports/data/aggtrades_post_v9_batch2_collection_v9_23.json"),
    Path("reports/manifests/aggtrades_post_v9_batch2_collection_v9_23_manifest.json"),
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

AUDIT_PATHS = [
    Path("reports/audit_lite/v9_30_command_results.json"),
    Path("reports/audit_lite/v9_30_command_results.md"),
    Path("reports/audit_lite/v9_30_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_30_full_local_validation_attestation.md"),
    Path("reports/audit_lite/v9_30_artifact_inventory.json"),
    Path("reports/audit_lite/v9_30_artifact_inventory.md"),
    Path("reports/audit_lite/zip_size_report_v9_30.json"),
    Path("reports/audit_lite/zip_size_report_v9_30.md"),
    Path("reports/audit_lite/zip_audit_v9_30.json"),
    Path("reports/audit_lite/zip_audit_v9_30.md"),
    Path("reports/audit_lite/zip_smoke_v9_30.json"),
    Path("reports/audit_lite/zip_smoke_v9_30.md"),
]

FORBIDDEN_PREFIXES = (
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
)
FORBIDDEN_SUFFIXES = {
    ".pyc",
    ".pkl",
    ".pickle",
    ".joblib",
    ".onnx",
    ".pt",
    ".pth",
    ".ckpt",
    ".pem",
    ".key",
    ".zip",
    ".sha256.json",
    ".sha256.txt",
}
FORBIDDEN_NAMES = {".DS_Store", ".env", "Icon", "Icon\r"}


def main() -> int:
    report = _read_json(Path("reports/data/aggtrades_5y_extension_plan_v9_30.json"))
    _ensure_placeholders()
    zip_size: int | None = None
    paths: list[Path] = []
    for _ in range(20):
        _write_attestation(report, zip_size)
        paths = _collect_paths()
        _write_inventory(paths, zip_size)
        _write_size_report(paths, zip_size)
        paths = _collect_paths()
        _write_zip(paths)
        current = (ROOT / ZIP_NAME).stat().st_size
        if current == zip_size:
            break
        zip_size = current
    result = {
        "version": VERSION,
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": (ROOT / ZIP_NAME).stat().st_size,
        "zip_bytes_is_authoritative": False,
        "included_files": len(paths),
        "sidecars_created": False,
        "zip_fingerprints_created": False,
        "status": "PASS",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _ensure_placeholders() -> None:
    placeholders = {
        "reports/audit_lite/v9_30_command_results.json": {"version": VERSION, "status": "PENDING_CAPTURE", "commands": [], "sidecars_created": False, "zip_fingerprints_created": False},
        "reports/audit_lite/zip_audit_v9_30.json": {"version": VERSION, "passed": False, "errors": [], "status": "PENDING_RUN"},
        "reports/audit_lite/zip_smoke_v9_30.json": {"version": VERSION, "passed": False, "errors": [], "status": "PENDING_RUN"},
    }
    texts = {
        "reports/audit_lite/v9_30_command_results.md": "# Commandes V9.30\n\nEn attente.\n",
        "reports/audit_lite/zip_audit_v9_30.md": "# Audit ZIP V9.30\n\nEn attente.\n",
        "reports/audit_lite/zip_smoke_v9_30.md": "# Smoke ZIP V9.30\n\nEn attente.\n",
    }
    for raw, payload in placeholders.items():
        path = ROOT / raw
        if not path.exists():
            payload["created_at_utc"] = _utc_now()
            _write_json(path, payload)
    for raw, text in texts.items():
        path = ROOT / raw
        if not path.exists():
            _write_text(path, text)


def _collect_paths() -> list[Path]:
    explicit = [*CORE_PATHS, *PRIOR_REPORTS, *STATE_PATHS, *AUDIT_PATHS]
    missing_core = [path.as_posix() for path in CORE_PATHS if not (ROOT / path).is_file()]
    if missing_core:
        raise FileNotFoundError(f"missing V9.30 release inputs: {missing_core}")
    return sorted({path for path in explicit if (ROOT / path).is_file() and _allowed(path)}, key=lambda item: item.as_posix())


def _write_attestation(report: dict[str, Any], zip_size: int | None) -> None:
    commands = _read_optional_json(Path("reports/audit_lite/v9_30_command_results.json")).get("commands", [])
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_size,
        "zip_bytes_is_authoritative": False,
        "commands_executed": [item.get("command") for item in commands],
        "decision": report["decision"],
        "target_5y_window_start": report["target_5y_window_start"],
        "target_5y_window_end": report["target_5y_window_end"],
        "target_5y_days_expected": report["target_5y_days_expected"],
        "already_validated_days": report["already_validated_days"],
        "extension_days_needed": report["extension_days_needed"],
        "estimated_extension_raw_bytes": report["estimated_extension_raw_bytes"],
        "estimated_extension_silver_bytes": report["estimated_extension_silver_bytes"],
        "safe_for_5y_extension_collection": report["safe_for_5y_extension_collection"],
        "network_used": report["network_used"],
        "new_data_downloaded": report["new_data_downloaded"],
        "ingestion_executed": report["ingestion_executed"],
        "features_created": report["features_created"],
        "labels_created": report["labels_created"],
        "dataset_created": report["dataset_created"],
        "ml_executed": report["ml_executed"],
        "walk_forward_executed": report["walk_forward_executed"],
        "backtest_executed": report["backtest_executed"],
        **report["safety_flags"],
    }
    _write_json(Path("reports/audit_lite/v9_30_full_local_validation_attestation.json"), payload)
    _write_text(
        Path("reports/audit_lite/v9_30_full_local_validation_attestation.md"),
        "# Attestation V9.30\n\n"
        f"- Decision : `{report['decision']}`.\n"
        f"- Fenetre cible 5Y : `{report['target_5y_window_start']}` -> `{report['target_5y_window_end']}`.\n"
        f"- Extension : `{report['extension_window_start']}` -> `{report['extension_window_end']}` (`{report['extension_days_needed']}` jours).\n"
        f"- Safe stockage : `{report['safe_for_5y_extension_collection']}`.\n"
        "- Aucun trading, paper live, ordre, backtest, walk-forward, ML, dataset supervise, strategie, signal actionnable, modele persistant, API privee, cle API, client exchange authentifie ou websocket live.\n"
        "- Aucun telechargement de nouvelles donnees, aucune ingestion, aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.\n",
    )


def _write_inventory(paths: list[Path], zip_size: int | None) -> None:
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_size,
        "zip_bytes_is_authoritative": False,
        "files_count": len(paths),
        "files": [path.as_posix() for path in paths],
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    _write_json(Path("reports/audit_lite/v9_30_artifact_inventory.json"), payload)
    _write_text(
        Path("reports/audit_lite/v9_30_artifact_inventory.md"),
        "# Inventaire audit-lite V9.30\n\n"
        f"- Fichiers inclus : `{len(paths)}`.\n"
        f"- ZIP : `{ZIP_NAME}`.\n"
        "- Aucun gros repertoire data/raw, data/silver ou data/research n'est inclus.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n",
    )


def _write_size_report(paths: list[Path], zip_size: int | None) -> None:
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_size,
        "zip_bytes_is_authoritative": False,
        "included_files": len(paths),
        "included_uncompressed_bytes": sum((ROOT / path).stat().st_size for path in paths),
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    _write_json(Path("reports/audit_lite/zip_size_report_v9_30.json"), payload)
    _write_text(
        Path("reports/audit_lite/zip_size_report_v9_30.md"),
        "# Taille ZIP V9.30\n\n"
        f"- Estimation ZIP bytes : `{zip_size}`.\n"
        f"- Fichiers inclus : `{len(paths)}`.\n"
        "- `zip_bytes_is_authoritative=false`.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n",
    )


def _write_zip(paths: list[Path]) -> None:
    zip_path = ROOT / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(ROOT / path, path.as_posix())


def _allowed(path: Path) -> bool:
    name = path.name
    raw = path.as_posix()
    if name in FORBIDDEN_NAMES:
        return False
    if any(raw.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return False
    return not any(name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES)


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
