from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.25.1"
ZIP_NAME = "projet-galapagos-v9.25.1-audit-lite.zip"
ROOT = Path(".").resolve()

CORE_PATHS = [
    Path("scripts/_bootstrap.py"),
    Path("src/galapagos/data/aggtrades_post_v9_collection_v9_18.py"),
    Path("src/galapagos/data/aggtrades_post_v9_batch3_collection_v9_24.py"),
    Path("src/galapagos/data/aggtrades_post_v9_completion_campaign_v9_25.py"),
    Path("src/galapagos/data/aggtrades_post_v9_resume_campaign_v9_25_1.py"),
    Path("src/galapagos/data/aggtrades_post_v9_resume_campaign_v9_25_1_validation.py"),
    Path("scripts/run_aggtrades_post_v9_resume_campaign_v9_25_1.py"),
    Path("scripts/validate_aggtrades_post_v9_resume_campaign_v9_25_1.py"),
    Path("scripts/release_audit_lite_zip_v9_25_1.py"),
    Path("scripts/audit_audit_lite_zip_v9_25_1.py"),
    Path("scripts/smoke_audit_lite_zip_v9_25_1.py"),
    Path("tests/data/test_aggtrades_post_v9_resume_campaign_v9_25_1.py"),
    Path("tests/validation/test_aggtrades_post_v9_resume_campaign_v9_25_1_validator.py"),
    Path("reports/manifests/aggtrades_post_v9_resume_campaign_v9_25_1_manifest.json"),
    Path("reports/data/aggtrades_post_v9_resume_campaign_v9_25_1.json"),
    Path("reports/data/aggtrades_post_v9_resume_campaign_v9_25_1.md"),
    Path("docs/aggtrades_post_v9_resume_campaign_v9_25_1.md"),
]

PRIOR_REPORTS = [
    Path("reports/data/aggtrades_post_v9_completion_campaign_v9_25.json"),
    Path("reports/data/aggtrades_post_v9_completion_campaign_v9_25.md"),
    Path("reports/data/aggtrades_post_v9_completion_batch01_v9_25.json"),
    Path("reports/manifests/aggtrades_post_v9_completion_campaign_v9_25_manifest.json"),
    Path("reports/data/aggtrades_post_v9_batch3_collection_v9_24.json"),
    Path("reports/data/aggtrades_post_v9_batch2_collection_v9_23.json"),
    Path("reports/data/aggtrades_post_v9_multi_batch_plan_v9_22.json"),
    Path("reports/data/aggtrades_post_v9_batch_expansion_v9_21.json"),
    Path("reports/data/aggtrades_post_v9_batch_collection_v9_20.json"),
    Path("reports/data/aggtrades_post_v9_pilot_collection_v9_19.json"),
    Path("reports/manifests/public_trades_1y_window_v8_2_manifest.json"),
    Path("reports/manifests/max_history_public_market_data_v5_0_manifest.json"),
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
    Path("reports/audit_lite/v9_25_1_command_results.json"),
    Path("reports/audit_lite/v9_25_1_command_results.md"),
    Path("reports/audit_lite/v9_25_1_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_25_1_full_local_validation_attestation.md"),
    Path("reports/audit_lite/v9_25_1_artifact_inventory.json"),
    Path("reports/audit_lite/v9_25_1_artifact_inventory.md"),
    Path("reports/audit_lite/zip_size_report_v9_25_1.json"),
    Path("reports/audit_lite/zip_size_report_v9_25_1.md"),
    Path("reports/audit_lite/zip_audit_v9_25_1.json"),
    Path("reports/audit_lite/zip_audit_v9_25_1.md"),
    Path("reports/audit_lite/zip_smoke_v9_25_1.json"),
    Path("reports/audit_lite/zip_smoke_v9_25_1.md"),
]

FORBIDDEN_PREFIXES = ("data/raw/", "data/silver/", "data/research/", "data/gold/", "reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/", "checkpoints/")
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pem", ".key", ".zip", ".sha256.json", ".sha256.txt"}
FORBIDDEN_NAMES = {".DS_Store", ".env", "Icon", "Icon\r"}


def main() -> int:
    report = _read_json(Path("reports/data/aggtrades_post_v9_resume_campaign_v9_25_1.json"))
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
    result = {"version": VERSION, "zip_name": ZIP_NAME, "zip_bytes_estimate": (ROOT / ZIP_NAME).stat().st_size, "zip_bytes_is_authoritative": False, "included_files": len(paths), "sidecars_created": False, "zip_fingerprints_created": False, "status": "PASS"}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _ensure_placeholders() -> None:
    placeholders = {
        "reports/audit_lite/v9_25_1_command_results.json": {"version": VERSION, "status": "PENDING_CAPTURE", "commands": [], "sidecars_created": False, "zip_fingerprints_created": False},
        "reports/audit_lite/zip_audit_v9_25_1.json": {"version": VERSION, "passed": False, "errors": [], "status": "PENDING_RUN"},
        "reports/audit_lite/zip_smoke_v9_25_1.json": {"version": VERSION, "passed": False, "errors": [], "status": "PENDING_RUN"},
    }
    for raw, payload in placeholders.items():
        path = ROOT / raw
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            payload["created_at_utc"] = _utc_now()
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    texts = {
        "reports/audit_lite/v9_25_1_command_results.md": "# Commandes V9.25.1\n\nEn attente.\n",
        "reports/audit_lite/zip_audit_v9_25_1.md": "# Audit ZIP V9.25.1\n\nEn attente.\n",
        "reports/audit_lite/zip_smoke_v9_25_1.md": "# Smoke ZIP V9.25.1\n\nEn attente.\n",
    }
    for raw, text in texts.items():
        path = ROOT / raw
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")


def _collect_paths() -> list[Path]:
    batch_reports = sorted(Path("reports/data").glob("aggtrades_post_v9_resume_batch*_v9_25_1.json"))
    explicit = [*CORE_PATHS, *batch_reports, *PRIOR_REPORTS, *STATE_PATHS, *AUDIT_PATHS]
    missing = [path.as_posix() for path in explicit if path in CORE_PATHS and not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError(f"missing V9.25.1 release inputs: {missing}")
    return sorted({path for path in explicit if (ROOT / path).is_file() and _allowed(path)}, key=lambda p: p.as_posix())


def _write_attestation(report: dict[str, Any], zip_size: int | None) -> None:
    commands = _read_optional_json(Path("reports/audit_lite/v9_25_1_command_results.json")).get("commands", [])
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_size,
        "zip_bytes_is_authoritative": False,
        "commands_executed": [item.get("command") for item in commands],
        "decision": report["decision"],
        **report["resume_summary"],
        "collection_executed": report["collection_executed"],
        "features_created": report["features_created"],
        "labels_created": report["labels_created"],
        "dataset_created": report["dataset_created"],
        "ml_executed": report["ml_executed"],
        "walk_forward_executed": report["walk_forward_executed"],
        "backtest_executed": report["backtest_executed"],
        **report["safety_flags"],
    }
    _write_json(Path("reports/audit_lite/v9_25_1_full_local_validation_attestation.json"), payload)
    _write_text(
        Path("reports/audit_lite/v9_25_1_full_local_validation_attestation.md"),
        "# Attestation V9.25.1\n\n"
        f"- Decision : `{report['decision']}`.\n"
        f"- Couverture locale : `{report['resume_summary']['local_file_coverage_start']}` -> `{report['resume_summary']['local_file_coverage_end']}`.\n"
        "- Aucun trading, paper live, ordre, backtest, walk-forward, ML, dataset supervise, strategie, signal actionnable, modele persistant, API privee, cle API, client exchange authentifie ou websocket live.\n"
        "- Aucune suppression de donnees, aucun nettoyage destructif, aucun sidecar et aucune empreinte ZIP.\n",
    )


def _write_inventory(paths: list[Path], zip_size: int | None) -> None:
    payload = {"version": VERSION, "created_at_utc": _utc_now(), "zip_name": ZIP_NAME, "zip_bytes_estimate": zip_size, "zip_bytes_is_authoritative": False, "files_count": len(paths), "files": [p.as_posix() for p in paths], "sidecars_created": False, "zip_fingerprints_created": False, "forbidden_absences_verified": {"no_raw_full": True, "no_silver_full": True, "no_models": True, "no_sidecars": True}}
    _write_json(Path("reports/audit_lite/v9_25_1_artifact_inventory.json"), payload)
    _write_text(Path("reports/audit_lite/v9_25_1_artifact_inventory.md"), f"# Inventaire V9.25.1\n\n- Fichiers inclus : `{len(paths)}`.\n- `zip_bytes_is_authoritative=false`.\n")


def _write_size_report(paths: list[Path], zip_size: int | None) -> None:
    payload = {"version": VERSION, "zip_name": ZIP_NAME, "zip_bytes_estimate": zip_size, "zip_bytes_is_authoritative": False, "included_files": len(paths), "sidecars_created": False, "zip_fingerprints_created": False}
    _write_json(Path("reports/audit_lite/zip_size_report_v9_25_1.json"), payload)
    _write_text(Path("reports/audit_lite/zip_size_report_v9_25_1.md"), f"# Taille ZIP V9.25.1\n\n- ZIP bytes estimate : `{zip_size}`.\n- `zip_bytes_is_authoritative=false`.\n")


def _write_zip(paths: list[Path]) -> None:
    target = ROOT / ZIP_NAME
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in paths:
            archive.write(ROOT / path, path.as_posix())


def _allowed(path: Path) -> bool:
    name = path.as_posix()
    if name.startswith(FORBIDDEN_PREFIXES):
        return False
    if path.name in FORBIDDEN_NAMES:
        return False
    return path.suffix.casefold() not in FORBIDDEN_SUFFIXES


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _read_optional_json(path: Path) -> dict[str, Any]:
    full = ROOT / path
    return json.loads(full.read_text(encoding="utf-8")) if full.exists() else {}


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
