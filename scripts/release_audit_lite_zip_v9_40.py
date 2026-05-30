from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.40"
ZIP_NAME = "projet-galapagos-v9.40-audit-lite.zip"
ROOT = Path(".").resolve()

CORE_PATHS = [
    Path("scripts/_bootstrap.py"),
    Path("src/galapagos/labels/ohlcv_aggtrades_5y_label_factory_v9_40.py"),
    Path("src/galapagos/labels/ohlcv_aggtrades_5y_label_factory_v9_40_validation.py"),
    Path("src/galapagos/labels/ohlcv_aggtrades_5y_label_factory_v9_40_schemas.py"),
    Path("scripts/run_ohlcv_aggtrades_5y_label_factory_v9_40.py"),
    Path("scripts/validate_ohlcv_aggtrades_5y_label_factory_v9_40.py"),
    Path("scripts/release_audit_lite_zip_v9_40.py"),
    Path("scripts/audit_audit_lite_zip_v9_40.py"),
    Path("scripts/smoke_audit_lite_zip_v9_40.py"),
    Path("tests/labels/test_ohlcv_aggtrades_5y_label_factory_v9_40.py"),
    Path("tests/validation/test_ohlcv_aggtrades_5y_label_factory_v9_40_validator.py"),
    Path("reports/manifests/ohlcv_aggtrades_5y_label_factory_v9_40_manifest.json"),
    Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json"),
    Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.md"),
    Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40_datacard.md"),
    Path("reports/labels/ohlcv_aggtrades_5y_label_distribution_v9_40.json"),
    Path("reports/labels/ohlcv_aggtrades_5y_label_stability_v9_40.json"),
    Path("docs/ohlcv_aggtrades_5y_label_factory_v9_40.md"),
]

PRIOR_REPORTS = [
    Path("reports/datasets/ohlcv_aggtrades_5y_dataset_v9_39.json"),
    Path("reports/manifests/ohlcv_aggtrades_5y_dataset_v9_39_manifest.json"),
    Path("reports/features/ohlcv_aggtrades_5y_feature_store_validation_v9_38.json"),
    Path("reports/features/ohlcv_aggtrades_5y_feature_store_v9_37.json"),
    Path("reports/data/ohlcv_from_aggtrades_5y_validation_v9_36.json"),
    Path("reports/research_decisions/label_failure_analysis_v9_11.json"),
    Path("reports/labels/horizon_event_label_redesign_v9_12.json"),
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
    Path("reports/audit_lite/v9_40_command_results.json"),
    Path("reports/audit_lite/v9_40_command_results.md"),
    Path("reports/audit_lite/v9_40_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_40_full_local_validation_attestation.md"),
    Path("reports/audit_lite/v9_40_artifact_inventory.json"),
    Path("reports/audit_lite/v9_40_artifact_inventory.md"),
    Path("reports/audit_lite/zip_size_report_v9_40.json"),
    Path("reports/audit_lite/zip_size_report_v9_40.md"),
    Path("reports/audit_lite/zip_audit_v9_40.json"),
    Path("reports/audit_lite/zip_audit_v9_40.md"),
    Path("reports/audit_lite/zip_smoke_v9_40.json"),
    Path("reports/audit_lite/zip_smoke_v9_40.md"),
]

FORBIDDEN_PREFIXES = ("data/raw/", "data/silver/", "data/research/", "data/gold/", "reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/", "checkpoints/")
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pem", ".key", ".zip", ".sha256.json", ".sha256.txt"}
FORBIDDEN_NAMES = {".DS_Store", ".env", "Icon", "Icon\r"}


def main() -> int:
    report = _read_json(Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json"))
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
    print(json.dumps({"version": VERSION, "zip_name": ZIP_NAME, "zip_bytes_estimate": (ROOT / ZIP_NAME).stat().st_size, "zip_bytes_is_authoritative": False, "included_files": len(paths), "sidecars_created": False, "zip_fingerprints_created": False, "status": "PASS"}, indent=2, ensure_ascii=False))
    return 0


def _ensure_placeholders() -> None:
    placeholders = {
        "reports/audit_lite/v9_40_command_results.json": {"version": VERSION, "status": "PENDING_CAPTURE", "commands": [], "sidecars_created": False, "zip_fingerprints_created": False},
        "reports/audit_lite/zip_audit_v9_40.json": {"version": VERSION, "passed": False, "errors": [], "status": "PENDING_RUN"},
        "reports/audit_lite/zip_smoke_v9_40.json": {"version": VERSION, "passed": False, "errors": [], "status": "PENDING_RUN"},
    }
    texts = {
        "reports/audit_lite/v9_40_command_results.md": "# Commandes V9.40\n\nEn attente.\n",
        "reports/audit_lite/zip_audit_v9_40.md": "# Audit ZIP V9.40\n\nEn attente.\n",
        "reports/audit_lite/zip_smoke_v9_40.md": "# Smoke ZIP V9.40\n\nEn attente.\n",
    }
    for raw, payload in placeholders.items():
        path = ROOT / raw
        if not path.exists():
            payload["created_at_utc"] = _utc_now()
            _write_json(Path(raw), payload)
    for raw, text in texts.items():
        path = ROOT / raw
        if not path.exists():
            _write_text(Path(raw), text)


def _collect_paths() -> list[Path]:
    explicit = [*CORE_PATHS, *PRIOR_REPORTS, *STATE_PATHS, *AUDIT_PATHS]
    missing_core = [path.as_posix() for path in CORE_PATHS if not (ROOT / path).is_file()]
    if missing_core:
        raise FileNotFoundError(f"missing V9.40 release inputs: {missing_core}")
    return sorted({path for path in explicit if (ROOT / path).is_file() and _allowed(path)}, key=lambda item: item.as_posix())


def _write_attestation(report: dict[str, Any], zip_size: int | None) -> None:
    commands = _read_optional_json(Path("reports/audit_lite/v9_40_command_results.json")).get("commands", [])
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_size,
        "zip_bytes_is_authoritative": False,
        "commands_executed": [item.get("command") for item in commands],
        "decision": report["decision"],
        "labels_created": report["labels_created"],
        "dataset_created": report["dataset_created"],
        "selected_primary_label": report["selected_primary_label"],
        "quality_status": report["quality_status"],
        "coverage_status": report["coverage_status"],
        "leakage_guard_status": report["leakage_guard"]["status"],
        "network_used": report["network_used"],
        "new_data_downloaded": report["new_data_downloaded"],
        "ml_executed": report["ml_executed"],
        "walk_forward_executed": report["walk_forward_executed"],
        "backtest_executed": report["backtest_executed"],
        **report["safety_flags"],
    }
    _write_json(Path("reports/audit_lite/v9_40_full_local_validation_attestation.json"), payload)
    _write_text(Path("reports/audit_lite/v9_40_full_local_validation_attestation.md"), "# Attestation V9.40\n\n" f"- Decision : `{report['decision']}`.\n" f"- Labels crees : `{report['labels_created']}`.\n" f"- Dataset supervise cree : `{report['dataset_created']}`.\n" f"- Label principal : `{report['selected_primary_label']}`.\n" "- Aucun reseau, telechargement, trading, paper live, ordre, backtest, walk-forward, ML, dataset supervise, strategie, signal actionnable, modele persistant, API privee, cle API, client exchange authentifie ou websocket live.\n" "- Aucune suppression destructive, aucun sidecar et aucune empreinte ZIP.\n")


def _write_inventory(paths: list[Path], zip_size: int | None) -> None:
    payload = {"version": VERSION, "created_at_utc": _utc_now(), "zip_name": ZIP_NAME, "zip_bytes_estimate": zip_size, "zip_bytes_is_authoritative": False, "files_count": len(paths), "files": [path.as_posix() for path in paths], "sidecars_created": False, "zip_fingerprints_created": False}
    _write_json(Path("reports/audit_lite/v9_40_artifact_inventory.json"), payload)
    _write_text(Path("reports/audit_lite/v9_40_artifact_inventory.md"), "# Inventaire audit-lite V9.40\n\n" f"- Fichiers inclus : `{len(paths)}`.\n" f"- ZIP : `{ZIP_NAME}`.\n")


def _write_size_report(paths: list[Path], zip_size: int | None) -> None:
    payload = {"version": VERSION, "created_at_utc": _utc_now(), "zip_name": ZIP_NAME, "zip_bytes_estimate": zip_size, "zip_bytes_is_authoritative": False, "files_count": len(paths), "largest_files": sorted([{"path": path.as_posix(), "bytes": (ROOT / path).stat().st_size} for path in paths], key=lambda item: item["bytes"], reverse=True)[:20], "sidecars_created": False, "zip_fingerprints_created": False}
    _write_json(Path("reports/audit_lite/zip_size_report_v9_40.json"), payload)
    _write_text(Path("reports/audit_lite/zip_size_report_v9_40.md"), "# Taille ZIP V9.40\n\n" f"- Fichiers : `{len(paths)}`.\n" f"- ZIP bytes estimate : `{zip_size}`.\n")


def _write_zip(paths: list[Path]) -> None:
    zip_path = ROOT / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(ROOT / path, path.as_posix())


def _allowed(path: Path) -> bool:
    raw = path.as_posix()
    if any(raw.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return False
    if path.name in FORBIDDEN_NAMES:
        return False
    return not any(path.name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES)


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
