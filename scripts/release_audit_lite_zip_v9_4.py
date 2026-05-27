from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.4"
LAST_VALIDATED_VERSION = "V9.0_to_V9.3.2"
ZIP_NAME = "projet-galapagos-v9.4-audit-lite.zip"
ROOT = Path(".").resolve()

V9_4_REPORTS = [
    Path("reports/manifests/refined_research_decision_gate_v9_4_manifest.json"),
    Path("reports/research_decisions/refined_research_decision_gate_v9_4.json"),
    Path("reports/research_decisions/refined_research_decision_gate_v9_4.md"),
    Path("docs/refined_research_decision_gate_v9_4.md"),
]

V9_4_AUDIT_REPORTS = [
    Path("reports/audit_lite/v9_4_command_results.json"),
    Path("reports/audit_lite/v9_4_command_results.md"),
    Path("reports/audit_lite/v9_4_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_4_full_local_validation_attestation.md"),
    Path("reports/audit_lite/v9_4_artifact_inventory.json"),
    Path("reports/audit_lite/v9_4_artifact_inventory.md"),
    Path("reports/audit_lite/zip_size_report_v9_4.json"),
    Path("reports/audit_lite/zip_size_report_v9_4.md"),
    Path("reports/audit_lite/zip_audit_v9_4.json"),
    Path("reports/audit_lite/zip_audit_v9_4.md"),
    Path("reports/audit_lite/zip_smoke_v9_4.json"),
    Path("reports/audit_lite/zip_smoke_v9_4.md"),
]

INPUT_REPORTS = [
    Path("reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json"),
    Path("reports/manifests/refined_ohlcv_trades_offline_supervised_dataset_v9_1_manifest.json"),
    Path("reports/manifests/refined_ohlcv_trades_offline_ml_research_v9_2_manifest.json"),
    Path("reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json"),
    Path("reports/ml/refined_ohlcv_trades_offline_ml_research_v9_2.json"),
    Path("reports/ml/refined_ohlcv_trades_offline_research_scores_v9_2.json"),
    Path("reports/ml/refined_strict_walk_forward_validation_v9_3.json"),
    Path("reports/ml/refined_strict_walk_forward_scores_v9_3.json"),
    Path("reports/audit_lite/v9_0_to_v9_3_2_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_0_to_v9_3_2_artifact_inventory.json"),
]

CODE_FILES = [
    Path("src/galapagos/__init__.py"),
    Path("src/galapagos/research/__init__.py"),
    Path("src/galapagos/research/refined_research_decision_gate_v9_4.py"),
    Path("src/galapagos/research/refined_research_decision_gate_v9_4_validation.py"),
    Path("src/galapagos/validation/__init__.py"),
    Path("src/galapagos/validation/safety.py"),
]

SCRIPT_FILES = [
    Path("scripts/_bootstrap.py"),
    Path("scripts/run_refined_research_decision_gate_v9_4.py"),
    Path("scripts/validate_refined_research_decision_gate_v9_4.py"),
    Path("scripts/release_audit_lite_zip_v9_4.py"),
    Path("scripts/audit_audit_lite_zip_v9_4.py"),
    Path("scripts/smoke_audit_lite_zip_v9_4.py"),
]

TEST_FILES = [
    Path("tests/research/test_refined_research_decision_gate_v9_4.py"),
    Path("tests/validation/test_refined_research_decision_gate_v9_4_validator.py"),
]

STATE_FILES = [
    Path("reports/PROJECT_STATE.json"),
    Path("reports/PROJECT_STATE.md"),
    Path("reports/current/latest_metrics.json"),
    Path("reports/current/latest_metrics.md"),
    Path("reports/current/latest_summary.md"),
    Path("README.md"),
    Path("pyproject.toml"),
]

EXCLUDED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
EXCLUDED_NAMES = {".DS_Store", ".env"}
EXCLUDED_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".zip", ".pem", ".key"}
FORBIDDEN_PREFIXES = [
    "data/research/",
    "reports/backtests/",
    "reports/strategies/",
    "orders/",
    "execution/",
    "models/",
    "checkpoints/",
]


def main() -> int:
    _ensure_inputs()
    _ensure_command_results()
    _write_attestation()
    placeholder_paths = _collect_zip_paths()
    _write_zip_size_report(placeholder_paths, 0, "pending")
    paths = _collect_zip_paths()
    _write_inventory(paths, 0, "pending")
    paths = _collect_zip_paths()
    _write_zip(paths)
    final_bytes = (ROOT / ZIP_NAME).stat().st_size
    final_sha256 = _sha256_file(ROOT / ZIP_NAME)
    _write_zip_size_report(paths, final_bytes, final_sha256)
    _write_inventory(paths, final_bytes, final_sha256)
    _write_sidecars(final_bytes, final_sha256)
    result = {
        "version": VERSION,
        "zip": ZIP_NAME,
        "zip_bytes": final_bytes,
        "zip_sha256": final_sha256,
        "included_files": len(paths),
        "sidecar_json": f"{ZIP_NAME}.sha256.json",
        "sidecar_txt": f"{ZIP_NAME}.sha256.txt",
        "status": "PASS",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _ensure_inputs() -> None:
    required = [*V9_4_REPORTS, *INPUT_REPORTS, *CODE_FILES, *SCRIPT_FILES, *TEST_FILES, *STATE_FILES]
    missing = [path.as_posix() for path in required if not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError(f"missing V9.4 audit-lite input files: {missing}")


def _ensure_command_results() -> None:
    path = ROOT / "reports/audit_lite/v9_4_command_results.json"
    if path.exists():
        return
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "status": "PENDING_CAPTURE",
        "commands": [],
        "note": "This placeholder is replaced after local command execution.",
    }
    _write_json(path, payload)
    _write_text(
        ROOT / "reports/audit_lite/v9_4_command_results.md",
        "# Commandes V9.4\n\nRapport en attente de capture finale.\n",
    )


def _write_attestation() -> None:
    decision = _read_json(ROOT / "reports/research_decisions/refined_research_decision_gate_v9_4.json")
    manifest = _read_json(ROOT / "reports/manifests/refined_research_decision_gate_v9_4_manifest.json")
    command_results = _read_json(ROOT / "reports/audit_lite/v9_4_command_results.json")
    payload = {
        "version": VERSION,
        "validation_scope": "full_local",
        "created_at_utc": _utc_now(),
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "research_decision": decision["research_decision"],
        "manifest_sha256": _sha256_file(ROOT / "reports/manifests/refined_research_decision_gate_v9_4_manifest.json"),
        "decision_report_sha256": _sha256_file(ROOT / "reports/research_decisions/refined_research_decision_gate_v9_4.json"),
        "command_results_sha256": _sha256_file(ROOT / "reports/audit_lite/v9_4_command_results.json"),
        "commands_recorded": len(command_results.get("commands", [])),
        "tests_passed": _commands_passed(command_results, ["pytest"]),
        "validator_passed": _commands_passed(command_results, ["validate_refined_research_decision_gate_v9_4.py"]),
        "audit_lite_passed": _commands_passed(command_results, ["audit_audit_lite_zip_v9_4.py"]),
        "smoke_audit_lite_passed": _commands_passed(command_results, ["smoke_audit_lite_zip_v9_4.py"]),
        "source_manifest_status": manifest["status"],
        "safety_flags": decision["safety"],
        "findings": decision["findings"],
        "no_trading": True,
        "no_paper_live": True,
        "no_orders": True,
        "no_backtest_performed": True,
        "no_strategy": True,
        "no_actionable_signal": True,
        "no_persistent_model": True,
        "api_key_used": False,
        "private_endpoint_used": False,
    }
    _write_json(ROOT / "reports/audit_lite/v9_4_full_local_validation_attestation.json", payload)
    _write_text(
        ROOT / "reports/audit_lite/v9_4_full_local_validation_attestation.md",
        "# Attestation full locale V9.4\n\n"
        f"- Version : `{VERSION}`.\n"
        f"- Decision research : `{decision['research_decision']}`.\n"
        "- Aucun trading, aucun paper live, aucun ordre, aucun backtest execute, aucune strategie, aucun signal actionnable.\n",
    )


def _commands_passed(command_results: dict[str, Any], needles: list[str]) -> bool:
    commands = command_results.get("commands", [])
    return any(command.get("status") == "PASS" and all(needle in command.get("command", "") for needle in needles) for command in commands)


def _collect_zip_paths() -> list[Path]:
    explicit = [*V9_4_REPORTS, *V9_4_AUDIT_REPORTS, *INPUT_REPORTS, *CODE_FILES, *SCRIPT_FILES, *TEST_FILES, *STATE_FILES]
    return sorted({path for path in explicit if (ROOT / path).is_file() and _is_allowed(path)}, key=lambda item: item.as_posix())


def _is_allowed(path: Path) -> bool:
    text = path.as_posix()
    if any(text.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return False
    if set(path.parts) & EXCLUDED_PARTS:
        return False
    if path.name in EXCLUDED_NAMES:
        return False
    return path.suffix.casefold() not in EXCLUDED_SUFFIXES


def _write_zip(paths: list[Path]) -> None:
    zip_path = ROOT / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in paths:
            archive.write(ROOT / path, path.as_posix())


def _write_inventory(paths: list[Path], zip_bytes: int, zip_sha256: str) -> None:
    payload = {
        "version": VERSION,
        "zip_name": ZIP_NAME,
        "zip_bytes": zip_bytes,
        "zip_sha256": zip_sha256,
        "files_count": len(paths),
        "files": [path.as_posix() for path in paths],
        "created_at_utc": _utc_now(),
        "forbidden_absences_verified": _forbidden_absence_checks(paths),
        "safety": {
            "trading_enabled": False,
            "paper_live_enabled": False,
            "orders_enabled": False,
            "backtest_enabled": False,
            "strategy_enabled": False,
            "execution_enabled": False,
            "api_key_used": False,
            "private_endpoint_used": False,
        },
    }
    _write_json(ROOT / "reports/audit_lite/v9_4_artifact_inventory.json", payload)
    _write_text(
        ROOT / "reports/audit_lite/v9_4_artifact_inventory.md",
        "# Inventaire audit-lite V9.4\n\n"
        f"- ZIP : `{ZIP_NAME}`.\n"
        f"- Fichiers inclus : `{len(paths)}`.\n"
        f"- Taille ZIP : `{zip_bytes}`.\n"
        f"- SHA256 ZIP : `{zip_sha256}`.\n"
        "- Aucun trading, aucun backtest, aucune strategie, aucun signal, aucun ordre.\n",
    )


def _write_zip_size_report(paths: list[Path], zip_bytes: int, zip_sha256: str) -> None:
    payload = {
        "version": VERSION,
        "zip_name": ZIP_NAME,
        "zip_bytes": zip_bytes,
        "zip_sha256": zip_sha256,
        "included_files": len(paths),
        "created_at_utc": _utc_now(),
        "sidecar_is_authoritative": True,
    }
    _write_json(ROOT / "reports/audit_lite/zip_size_report_v9_4.json", payload)
    _write_text(
        ROOT / "reports/audit_lite/zip_size_report_v9_4.md",
        "# Taille ZIP audit-lite V9.4\n\n"
        f"- ZIP : `{ZIP_NAME}`.\n"
        f"- Taille bytes : `{zip_bytes}`.\n"
        f"- SHA256 : `{zip_sha256}`.\n"
        f"- Fichiers inclus : `{len(paths)}`.\n"
        "- Le sidecar externe donne le hash final reel du ZIP.\n",
    )


def _write_sidecars(zip_bytes: int, zip_sha256: str) -> None:
    payload = {
        "version": VERSION,
        "zip_name": ZIP_NAME,
        "zip_bytes": zip_bytes,
        "sha256": zip_sha256,
        "created_at_utc": _utc_now(),
        "sidecar_scope": "external_final_zip_hash",
    }
    _write_json(ROOT / f"{ZIP_NAME}.sha256.json", payload)
    _write_text(ROOT / f"{ZIP_NAME}.sha256.txt", f"{zip_sha256}  {ZIP_NAME}\n")


def _forbidden_absence_checks(paths: list[Path]) -> dict[str, bool]:
    texts = [path.as_posix() for path in paths]
    suffixes = [path.suffix.casefold() for path in paths]
    names = [path.name for path in paths]
    return {
        "ds_store_absent": ".DS_Store" not in names,
        "venv_absent": not any(".venv" in path.parts for path in paths),
        "pycache_absent": not any("__pycache__" in path.parts for path in paths),
        "pyc_absent": ".pyc" not in suffixes,
        "cache_dirs_absent": not any(part in {".pytest_cache", ".ruff_cache", ".mypy_cache"} for path in paths for part in path.parts),
        "secrets_absent": not any(name in {".env"} or suffix in {".pem", ".key"} for name, suffix in zip(names, suffixes, strict=False)),
        "persistent_models_absent": not any(suffix in {".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt"} for suffix in suffixes),
        "data_research_full_absent": not any(text.startswith("data/research/") for text in texts),
        "execution_artifacts_absent": not any(text.startswith(("reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/", "checkpoints/")) for text in texts),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
