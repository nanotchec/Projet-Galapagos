from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.4.1"
SOURCE_VERSION = "V9.4"
LAST_VALIDATED_VERSION = "V9.0_to_V9.3.2"
CORRECTION_SCOPE = "packaging_sidecars_only"
ZIP_NAME = "projet-galapagos-v9.4.1-audit-lite.zip"
ROOT = Path(".").resolve()

SOURCE_V9_4_REPORTS = [
    Path("reports/manifests/refined_research_decision_gate_v9_4_manifest.json"),
    Path("reports/research_decisions/refined_research_decision_gate_v9_4.json"),
    Path("reports/research_decisions/refined_research_decision_gate_v9_4.md"),
    Path("docs/refined_research_decision_gate_v9_4.md"),
]

V9_4_1_AUDIT_REPORTS = [
    Path("reports/audit_lite/v9_4_1_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_4_1_full_local_validation_attestation.md"),
    Path("reports/audit_lite/v9_4_1_artifact_inventory.json"),
    Path("reports/audit_lite/v9_4_1_artifact_inventory.md"),
    Path("reports/audit_lite/zip_size_report_v9_4_1.json"),
    Path("reports/audit_lite/zip_size_report_v9_4_1.md"),
    Path("reports/audit_lite/zip_audit_v9_4_1.json"),
    Path("reports/audit_lite/zip_audit_v9_4_1.md"),
    Path("reports/audit_lite/zip_smoke_v9_4_1.json"),
    Path("reports/audit_lite/zip_smoke_v9_4_1.md"),
]

SOURCE_AUDIT_REPORTS = [
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
    Path("scripts/release_audit_lite_zip_v9_4_1.py"),
    Path("scripts/audit_audit_lite_zip_v9_4_1.py"),
    Path("scripts/smoke_audit_lite_zip_v9_4_1.py"),
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
    _update_state_surfaces()
    _ensure_inputs()
    _ensure_audit_placeholders()
    _write_attestation()
    paths = _collect_zip_paths()
    _write_zip_size_report(paths, 0, "external_sidecar_pending")
    _write_inventory(paths, 0, "external_sidecar_pending")
    paths = _collect_zip_paths()
    _write_zip_size_report(paths, 0, "external_sidecar_pending")
    _write_inventory(paths, 0, "external_sidecar_pending")
    paths = _collect_zip_paths()
    _write_zip(paths)
    final_bytes = (ROOT / ZIP_NAME).stat().st_size
    final_sha256 = _sha256_file(ROOT / ZIP_NAME)
    _write_zip_size_report(paths, final_bytes, final_sha256)
    _write_inventory(paths, final_bytes, final_sha256)
    _write_sidecars(final_bytes, final_sha256)
    result = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "correction_scope": CORRECTION_SCOPE,
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
    required = [*SOURCE_V9_4_REPORTS, *SOURCE_AUDIT_REPORTS, *INPUT_REPORTS, *CODE_FILES, *SCRIPT_FILES, *TEST_FILES, *STATE_FILES]
    missing = [path.as_posix() for path in required if not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError(f"missing V9.4.1 audit-lite input files: {missing}")


def _ensure_audit_placeholders() -> None:
    for name in ["zip_audit_v9_4_1", "zip_smoke_v9_4_1"]:
        json_path = ROOT / f"reports/audit_lite/{name}.json"
        md_path = ROOT / f"reports/audit_lite/{name}.md"
        if not json_path.exists():
            _write_json(
                json_path,
                {
                    "version": VERSION,
                    "source_version": SOURCE_VERSION,
                    "correction_scope": CORRECTION_SCOPE,
                    "passed": False,
                    "status": "PENDING_EXTERNAL_RUN",
                    "errors": [],
                    "created_at_utc": _utc_now(),
                },
            )
        if not md_path.exists():
            _write_text(md_path, f"# {name} V9.4.1\n\nRapport en attente d'execution.\n")


def _write_attestation() -> None:
    decision_path = ROOT / "reports/research_decisions/refined_research_decision_gate_v9_4.json"
    manifest_path = ROOT / "reports/manifests/refined_research_decision_gate_v9_4_manifest.json"
    decision = _read_json(decision_path)
    manifest = _read_json(manifest_path)
    audit_report = _read_optional_json(ROOT / "reports/audit_lite/zip_audit_v9_4_1.json")
    smoke_report = _read_optional_json(ROOT / "reports/audit_lite/zip_smoke_v9_4_1.json")
    payload = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "validation_scope": "packaging_audit_lite",
        "correction_scope": CORRECTION_SCOPE,
        "created_at_utc": _utc_now(),
        "research_decision": decision["research_decision"],
        "research_decision_unchanged_from_v9_4": decision["research_decision"] == "backtest_not_justified_refine_labels",
        "business_results_recalculated": False,
        "business_results_modified": False,
        "source_manifest_status": manifest["status"],
        "source_decision_report_sha256": _sha256_file(decision_path),
        "source_manifest_sha256": _sha256_file(manifest_path),
        "tests_passed": _source_command_passed("pytest"),
        "validator_passed": _source_command_passed("validate_refined_research_decision_gate_v9_4.py"),
        "audit_lite_passed": audit_report.get("passed") is True,
        "smoke_audit_lite_passed": smoke_report.get("passed") is True,
        "safety_flags": decision["safety"],
        "findings": decision["findings"],
        "no_trading": True,
        "no_paper_live": True,
        "no_orders": True,
        "no_backtest": True,
        "no_backtest_performed": True,
        "no_strategy": True,
        "no_actionable_signal": True,
        "no_persistent_model": True,
        "api_key_used": False,
        "private_endpoint_used": False,
    }
    _write_json(ROOT / "reports/audit_lite/v9_4_1_full_local_validation_attestation.json", payload)
    _write_text(
        ROOT / "reports/audit_lite/v9_4_1_full_local_validation_attestation.md",
        "# Attestation corrective V9.4.1\n\n"
        f"- Version corrective : `{VERSION}`.\n"
        f"- Source metier : `{SOURCE_VERSION}`.\n"
        f"- Correction : `{CORRECTION_SCOPE}`.\n"
        f"- Decision research inchangee : `{decision['research_decision']}`.\n"
        "- Aucun resultat metier V9.4 n'est recalcule ou modifie.\n"
        "- Aucun trading, paper live, ordre, backtest, strategie, signal actionnable, modele persistant, API privee ou cle API.\n",
    )


def _source_command_passed(needle: str) -> bool:
    command_results = _read_optional_json(ROOT / "reports/audit_lite/v9_4_command_results.json")
    return any(command.get("status") == "PASS" and needle in command.get("command", "") for command in command_results.get("commands", []))


def _update_state_surfaces() -> None:
    decision = _read_json(ROOT / "reports/research_decisions/refined_research_decision_gate_v9_4.json")
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": SOURCE_VERSION,
        "correction_scope": CORRECTION_SCOPE,
        "direction": "correction packaging audit-lite sidecars V9.4",
        "research_decision_v9_4": decision["research_decision"],
        "research_decision_unchanged": True,
        "backtest_performed": False,
        "strategy_enabled": False,
        "actionable_signal_produced": False,
        "orders_enabled": False,
        "trading_enabled": False,
        "paper_live_enabled": False,
        "persistent_model_created": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "external_validation_required": True,
    }
    state_path = ROOT / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(state_path, state, sort_keys=False)
    _write_json(ROOT / "reports/current/latest_metrics.json", metrics)
    _write_text(
        ROOT / "reports/PROJECT_STATE.md",
        "# Etat du Projet : V9.0_to_V9.3.2 validee + candidat V9.4.1\n\n"
        "- **Derniere version validee** : V9.0_to_V9.3.2.\n"
        "- **Version candidate** : V9.4.1.\n"
        "- **Statut candidate** : `pending_external_audit`.\n"
        "- **Source metier** : V9.4.\n"
        "- **Correction** : packaging audit-lite / sidecars uniquement.\n"
        f"- **Decision research inchangee** : `{decision['research_decision']}`.\n\n"
        "Aucun backtest, aucune strategie, aucun signal actionnable, aucun ordre, aucun paper live, aucun trading reel, aucun modele persistant, aucune API privee, aucune cle API.\n",
    )
    _write_text(
        ROOT / "reports/current/latest_metrics.md",
        "# Latest Metrics V9.4.1\n\n"
        "- Derniere version validee : V9.0_to_V9.3.2.\n"
        "- Candidate : V9.4.1.\n"
        "- Source : V9.4.\n"
        "- Correction : packaging sidecars only.\n"
        f"- Decision research V9.4 : `{decision['research_decision']}`.\n\n"
        "Aucun backtest, aucune strategie, aucun signal actionnable, aucun ordre, aucun trading reel.\n",
    )
    _write_text(
        ROOT / "reports/current/latest_summary.md",
        "# Latest Summary V9.4.1\n\n"
        "V9.0_to_V9.3.2 est la derniere version validee par audit externe.\n\n"
        "V9.4.1 est une corrective packaging : elle fournit un ZIP audit-lite V9.4.1 avec sidecars externes JSON/TXT alignes sur le hash final du ZIP audite.\n\n"
        f"La decision research V9.4 reste inchangee : `{decision['research_decision']}`.\n\n"
        "La candidate reste `pending_external_audit`. Aucun trading, paper live, ordre, backtest, strategie, signal actionnable ou modele persistant n'est produit.\n",
    )
    _write_text(
        ROOT / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V9.0_to_V9.3.2.\n"
        "- Candidate : V9.4.1, correction packaging audit-lite sidecars.\n"
        "- Source metier : V9.4.\n"
        f"- Decision research inchangee : {decision['research_decision']}.\n\n"
        "V9.4.1 ne modifie pas les resultats metier V9.4. Elle livre uniquement le ZIP audit-lite correctif et ses sidecars externes.\n\n"
        "Aucun trading reel, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal actionnable, aucune API privee, aucune cle API et aucun modele persistant.\n",
    )


def _collect_zip_paths() -> list[Path]:
    explicit = [
        *SOURCE_V9_4_REPORTS,
        *SOURCE_AUDIT_REPORTS,
        *V9_4_1_AUDIT_REPORTS,
        *INPUT_REPORTS,
        *CODE_FILES,
        *SCRIPT_FILES,
        *TEST_FILES,
        *STATE_FILES,
    ]
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
        "source_version": SOURCE_VERSION,
        "correction_scope": CORRECTION_SCOPE,
        "zip_name": ZIP_NAME,
        "zip_bytes": zip_bytes,
        "zip_sha256": zip_sha256,
        "sidecar_is_authoritative": True,
        "files_count": len(paths),
        "files": [path.as_posix() for path in paths],
        "created_at_utc": _utc_now(),
        "forbidden_absences_verified": _forbidden_absence_checks(paths),
        "safety": _safety_flags(),
    }
    _write_json(ROOT / "reports/audit_lite/v9_4_1_artifact_inventory.json", payload)
    _write_text(
        ROOT / "reports/audit_lite/v9_4_1_artifact_inventory.md",
        "# Inventaire audit-lite V9.4.1\n\n"
        f"- ZIP : `{ZIP_NAME}`.\n"
        f"- Source metier : `{SOURCE_VERSION}`.\n"
        f"- Correction : `{CORRECTION_SCOPE}`.\n"
        f"- Fichiers inclus : `{len(paths)}`.\n"
        f"- Taille ZIP : `{zip_bytes}`.\n"
        f"- SHA256 ZIP : `{zip_sha256}`.\n"
        "- Le sidecar externe est l'autorite pour le hash final du ZIP.\n"
        "- Aucun trading, aucun backtest, aucune strategie, aucun signal, aucun ordre.\n",
    )


def _write_zip_size_report(paths: list[Path], zip_bytes: int, zip_sha256: str) -> None:
    payload = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "correction_scope": CORRECTION_SCOPE,
        "zip_name": ZIP_NAME,
        "zip_bytes": zip_bytes,
        "zip_sha256": zip_sha256,
        "included_files": len(paths),
        "created_at_utc": _utc_now(),
        "sidecar_is_authoritative": True,
    }
    _write_json(ROOT / "reports/audit_lite/zip_size_report_v9_4_1.json", payload)
    _write_text(
        ROOT / "reports/audit_lite/zip_size_report_v9_4_1.md",
        "# Taille ZIP audit-lite V9.4.1\n\n"
        f"- ZIP : `{ZIP_NAME}`.\n"
        f"- Taille bytes : `{zip_bytes}`.\n"
        f"- SHA256 : `{zip_sha256}`.\n"
        f"- Fichiers inclus : `{len(paths)}`.\n"
        "- Le sidecar externe donne le hash final reel du ZIP.\n",
    )


def _write_sidecars(zip_bytes: int, zip_sha256: str) -> None:
    payload = {
        "version": VERSION,
        "source_version": SOURCE_VERSION,
        "correction_scope": CORRECTION_SCOPE,
        "zip_name": ZIP_NAME,
        "zip_bytes": zip_bytes,
        "sha256": zip_sha256,
        "created_at_utc": _utc_now(),
        "sidecar_scope": "external_final_zip_hash",
        "research_decision_unchanged": True,
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
        "secrets_absent": not any(name == ".env" or suffix in {".pem", ".key"} for name, suffix in zip(names, suffixes, strict=False)),
        "persistent_models_absent": not any(suffix in {".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt"} for suffix in suffixes),
        "data_research_full_absent": not any(text.startswith("data/research/") for text in texts),
        "execution_artifacts_absent": not any(text.startswith(("reports/backtests/", "reports/strategies/", "orders/", "execution/", "models/", "checkpoints/")) for text in texts),
    }


def _safety_flags() -> dict[str, bool]:
    return {
        "trading_enabled": False,
        "paper_live_enabled": False,
        "orders_enabled": False,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "execution_enabled": False,
        "api_key_used": False,
        "private_endpoint_used": False,
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _read_json(path)


def _write_json(path: Path, payload: dict[str, Any], *, sort_keys: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=sort_keys, ensure_ascii=False) + "\n", encoding="utf-8")


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
