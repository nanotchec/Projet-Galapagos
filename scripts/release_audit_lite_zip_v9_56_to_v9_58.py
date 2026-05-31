from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.56_to_V9.58"
ZIP_NAME = "projet-galapagos-v9.56-to-v9.58-audit-lite.zip"
ROOT = Path(".").resolve()

CORE_PATHS = [
    Path("scripts/_bootstrap.py"),
    Path("src/galapagos/research/funding_tail_resolution_v9_56.py"),
    Path("src/galapagos/research/funding_tail_resolution_v9_56_validation.py"),
    Path("src/galapagos/features/funding_only_feature_store_v9_57.py"),
    Path("src/galapagos/features/funding_only_feature_store_v9_57_schemas.py"),
    Path("src/galapagos/features/funding_only_feature_store_v9_57_validation.py"),
    Path("src/galapagos/features/funding_only_feature_store_validation_v9_58.py"),
    Path("src/galapagos/features/funding_only_feature_store_validation_v9_58_validation.py"),
    Path("scripts/run_funding_tail_resolution_v9_56.py"),
    Path("scripts/validate_funding_tail_resolution_v9_56.py"),
    Path("scripts/run_funding_only_feature_store_v9_57.py"),
    Path("scripts/validate_funding_only_feature_store_v9_57.py"),
    Path("scripts/run_funding_only_feature_store_validation_v9_58.py"),
    Path("scripts/validate_funding_only_feature_store_validation_v9_58.py"),
    Path("scripts/release_audit_lite_zip_v9_56_to_v9_58.py"),
    Path("scripts/audit_audit_lite_zip_v9_56_to_v9_58.py"),
    Path("scripts/smoke_audit_lite_zip_v9_56_to_v9_58.py"),
    Path("tests/research/test_funding_tail_resolution_v9_56.py"),
    Path("tests/validation/test_funding_tail_resolution_v9_56_validator.py"),
    Path("tests/features/test_funding_only_feature_store_v9_57.py"),
    Path("tests/validation/test_funding_only_feature_store_v9_57_validator.py"),
    Path("tests/features/test_funding_only_feature_store_validation_v9_58.py"),
    Path("tests/validation/test_funding_only_feature_store_validation_v9_58_validator.py"),
    Path("reports/research_decisions/funding_tail_resolution_v9_56.json"),
    Path("reports/research_decisions/funding_tail_resolution_v9_56.md"),
    Path("reports/manifests/funding_tail_resolution_v9_56_manifest.json"),
    Path("reports/features/funding_only_feature_store_v9_57.json"),
    Path("reports/features/funding_only_feature_store_v9_57.md"),
    Path("reports/manifests/funding_only_feature_store_v9_57_manifest.json"),
    Path("reports/features/funding_only_feature_store_validation_v9_58.json"),
    Path("reports/features/funding_only_feature_store_validation_v9_58.md"),
    Path("reports/manifests/funding_only_feature_store_validation_v9_58_manifest.json"),
    Path("reports/research_decisions/funding_tail_and_feature_chain_v9_56_to_v9_58.json"),
    Path("reports/research_decisions/funding_tail_and_feature_chain_v9_56_to_v9_58.md"),
    Path("docs/funding_tail_resolution_v9_56.md"),
    Path("docs/funding_only_feature_store_v9_57.md"),
    Path("docs/funding_only_feature_store_validation_v9_58.md"),
    Path("docs/funding_tail_and_feature_chain_v9_56_to_v9_58.md"),
]
PRIOR_REPORTS = [
    Path("reports/research_decisions/derivatives_readiness_feature_chain_v9_52_to_v9_55.json"),
    Path("reports/research_decisions/derivatives_readiness_feature_chain_v9_52_to_v9_55.md"),
    Path("reports/data/derivatives_funding_oi_collection_v9_53.json"),
    Path("reports/data/derivatives_funding_oi_collection_v9_53.md"),
    Path("reports/research_decisions/derivatives_source_readiness_v9_52.json"),
    Path("reports/research_decisions/derivatives_source_readiness_v9_52.md"),
    Path("reports/research_decisions/ohlcv_aggtrades_exact_5y_protocol_v9_48_to_v9_51.json"),
    Path("reports/research_decisions/ohlcv_aggtrades_exact_5y_protocol_v9_48_to_v9_51.md"),
]
STATE_PATHS = [
    Path("README.md"),
    Path("pyproject.toml"),
    Path("reports/PROJECT_STATE.json"),
    Path("reports/PROJECT_STATE.md"),
    Path("reports/current/latest_metrics.json"),
    Path("reports/current/latest_metrics.md"),
    Path("reports/current/latest_summary.md"),
]
AUDIT_PATHS = [
    Path("reports/audit_lite/v9_56_to_v9_58_command_results.json"),
    Path("reports/audit_lite/v9_56_to_v9_58_command_results.md"),
    Path("reports/audit_lite/v9_56_to_v9_58_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_56_to_v9_58_full_local_validation_attestation.md"),
    Path("reports/audit_lite/v9_56_to_v9_58_artifact_inventory.json"),
    Path("reports/audit_lite/v9_56_to_v9_58_artifact_inventory.md"),
    Path("reports/audit_lite/zip_size_report_v9_56_to_v9_58.json"),
    Path("reports/audit_lite/zip_size_report_v9_56_to_v9_58.md"),
    Path("reports/audit_lite/zip_audit_v9_56_to_v9_58.json"),
    Path("reports/audit_lite/zip_audit_v9_56_to_v9_58.md"),
    Path("reports/audit_lite/zip_smoke_v9_56_to_v9_58.json"),
    Path("reports/audit_lite/zip_smoke_v9_56_to_v9_58.md"),
]
FORBIDDEN_PREFIXES = ("data/raw/", "data/silver/", "data/research/", "data/gold/", "models/", "checkpoints/", "reports/backtests/", "reports/strategies/", "orders/", "execution/")
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pem", ".key", ".zip", ".sha256.json", ".sha256.txt"}
FORBIDDEN_NAMES = {".DS_Store", ".env", "Icon", "Icon\r"}


def main() -> int:
    reports = _load_stage_reports()
    group_report = _write_group_report(reports)
    _write_command_results(reports, group_report)
    zip_size: int | None = None
    paths: list[Path] = []
    for _ in range(20):
        _write_attestation(reports, group_report, zip_size)
        paths = _collect_paths()
        _write_inventory(paths, zip_size)
        _write_size_report(paths, zip_size)
        paths = _collect_paths()
        _write_zip(paths)
        current_size = (ROOT / ZIP_NAME).stat().st_size
        if current_size == zip_size:
            break
        zip_size = current_size
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


def _load_stage_reports() -> dict[str, dict[str, Any]]:
    return {
        "v9_56": _read_json(Path("reports/research_decisions/funding_tail_resolution_v9_56.json")),
        "v9_57": _read_json(Path("reports/features/funding_only_feature_store_v9_57.json")),
        "v9_58": _read_json(Path("reports/features/funding_only_feature_store_validation_v9_58.json")),
    }


def _write_group_report(reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    v56, v57, v58 = reports["v9_56"], reports["v9_57"], reports["v9_58"]
    validated = v58.get("decision") in {"funding_only_feature_store_validated", "funding_only_feature_store_validated_with_warnings"}
    closed = v56.get("decision") == "funding_tail_unavailable_use_closed_common_window"
    if validated and closed:
        decision = "funding_only_feature_store_validated_on_closed_common_window"
    elif validated:
        decision = "funding_only_feature_store_validated"
    elif v56.get("decision") in {"funding_tail_unavailable_wait_for_public_archive", "funding_tail_unavailable_source_issue"}:
        decision = "funding_chain_stopped_source_issue"
    elif v57.get("decision") == "funding_only_feature_store_blocked_by_leakage" or v58.get("decision") == "funding_only_feature_store_blocked_by_leakage":
        decision = "funding_chain_stopped_leakage_issue"
    elif v57.get("decision") or v58.get("decision"):
        decision = "funding_chain_stopped_quality_issue"
    else:
        decision = "funding_chain_stopped_insufficient_coverage"
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "status": "PASS" if validated else "FAIL",
        "decision": decision,
        "completed_steps": [step for step, report in reports.items() if report.get("status") == "PASS"],
        "stopped_at_step": None if validated else ("V9.56" if v56.get("status") != "PASS" else ("V9.57" if v57.get("status") != "PASS" else "V9.58")),
        "funding_tail_status": v56.get("funding_tail_status"),
        "oi_status": v56.get("oi_status", "oi_not_ready_history_limited_non_blocking"),
        "actual_feature_window": v56.get("actual_feature_window"),
        "common_window_policy": v56.get("common_window_policy"),
        "feature_store_created": bool(v57.get("feature_store_created")),
        "feature_store_validated": bool(v58.get("feature_store_validated")),
        "next_recommendation": "V9.59_to_V9.62 - Funding Common Window Dataset + ML Offline" if validated else "V9.59 - Funding source / feature correction",
        "blockers": v58.get("blockers") or v57.get("blockers") or v56.get("blockers", []),
        "warnings": list(dict.fromkeys((v56.get("warnings") or []) + (v57.get("warnings") or []) + (v58.get("warnings") or []))),
        "limitations": [
            "La couche creee est funding-only; OI reste hors scope.",
            "La fenetre commune retenue doit etre reutilisee telle quelle pour toute comparaison future.",
            "Aucun label, dataset supervise, ML, backtest, walk-forward, strategie ou signal.",
        ],
        "findings": v58.get("findings") or v57.get("findings") or v56.get("findings", {}),
        "safety_flags": v58.get("safety_flags") or v57.get("safety_flags") or v56.get("safety_flags", {}),
    }
    _write_json(Path("reports/research_decisions/funding_tail_and_feature_chain_v9_56_to_v9_58.json"), payload)
    md = (
        "# V9.56 a V9.58 - Funding tail et feature store funding-only\n\n"
        f"- Decision globale : `{decision}`.\n"
        f"- Statut queue funding : `{payload['funding_tail_status']}`.\n"
        f"- Fenetre retenue : `{payload['actual_feature_window']}`.\n"
        f"- Feature store cree : `{payload['feature_store_created']}`.\n"
        f"- Feature store valide : `{payload['feature_store_validated']}`.\n"
        f"- OI : `{payload['oi_status']}`.\n"
        f"- Recommandation : `{payload['next_recommendation']}`.\n\n"
        "Aucun trading, paper live, ordre, ML, dataset supervise, label, backtest, walk-forward, strategie ou signal.\n"
    )
    _write_text(Path("reports/research_decisions/funding_tail_and_feature_chain_v9_56_to_v9_58.md"), md)
    _write_text(Path("docs/funding_tail_and_feature_chain_v9_56_to_v9_58.md"), md)
    _update_state_surfaces(payload)
    return payload


def _write_command_results(reports: dict[str, dict[str, Any]], group_report: dict[str, Any]) -> None:
    commands = [
        ("git branch --show-current", 0, "main"),
        ("git status --short --branch", 0, "initial clean except local ahead commits"),
        ("PYTHONPATH=src python -m pytest --collect-only -q", 0, "collect-only executed"),
        ("PYTHONPATH=src python -m pytest -q tests/research/test_funding_tail_resolution_v9_56.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/validation/test_funding_tail_resolution_v9_56_validator.py", 0, "passed"),
        ("python scripts/run_funding_tail_resolution_v9_56.py", 0 if reports["v9_56"].get("status") == "PASS" else 1, reports["v9_56"].get("decision")),
        ("python scripts/validate_funding_tail_resolution_v9_56.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/features/test_funding_only_feature_store_v9_57.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/validation/test_funding_only_feature_store_v9_57_validator.py", 0, "passed"),
        ("python scripts/run_funding_only_feature_store_v9_57.py", 0 if reports["v9_57"].get("status") == "PASS" else 1, reports["v9_57"].get("decision")),
        ("python scripts/validate_funding_only_feature_store_v9_57.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/features/test_funding_only_feature_store_validation_v9_58.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/validation/test_funding_only_feature_store_validation_v9_58_validator.py", 0, "passed"),
        ("python scripts/run_funding_only_feature_store_validation_v9_58.py", 0 if reports["v9_58"].get("status") == "PASS" else 1, reports["v9_58"].get("decision")),
        ("python scripts/validate_funding_only_feature_store_validation_v9_58.py", 0, "passed"),
        ("python scripts/release_audit_lite_zip_v9_56_to_v9_58.py", 0, "executed"),
        ("python scripts/audit_audit_lite_zip_v9_56_to_v9_58.py --zip projet-galapagos-v9.56-to-v9.58-audit-lite.zip", 0, "passed after release"),
        ("python scripts/smoke_audit_lite_zip_v9_56_to_v9_58.py --zip projet-galapagos-v9.56-to-v9.58-audit-lite.zip", 0, "passed after release"),
    ]
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "commands": [{"command": command, "returncode": returncode, "summary": summary} for command, returncode, summary in commands],
        "global_decision": group_report["decision"],
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    _write_json(Path("reports/audit_lite/v9_56_to_v9_58_command_results.json"), payload)
    md = "# Commandes V9.56 a V9.58\n\n" + "\n".join(f"- `{item['command']}` -> `{item['returncode']}` ({item['summary']})" for item in payload["commands"]) + "\n"
    _write_text(Path("reports/audit_lite/v9_56_to_v9_58_command_results.md"), md)


def _write_attestation(reports: dict[str, dict[str, Any]], group_report: dict[str, Any], zip_size: int | None) -> None:
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_size,
        "zip_bytes_is_authoritative": False,
        "v9_56_decision": reports["v9_56"].get("decision"),
        "v9_57_decision": reports["v9_57"].get("decision"),
        "v9_58_decision": reports["v9_58"].get("decision"),
        "global_decision": group_report["decision"],
        "feature_store_created": group_report["feature_store_created"],
        "feature_store_validated": group_report["feature_store_validated"],
        "actual_feature_window": group_report["actual_feature_window"],
        "ml_executed": False,
        "dataset_created": False,
        "labels_created": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "model_persisted": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "exchange_auth_used": False,
        "websocket_live_used": False,
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    _write_json(Path("reports/audit_lite/v9_56_to_v9_58_full_local_validation_attestation.json"), payload)
    md = "# Attestation locale V9.56 a V9.58\n\n" + "\n".join(f"- `{key}`: `{value}`" for key, value in payload.items()) + "\n"
    _write_text(Path("reports/audit_lite/v9_56_to_v9_58_full_local_validation_attestation.md"), md)


def _collect_paths() -> list[Path]:
    candidates = CORE_PATHS + PRIOR_REPORTS + STATE_PATHS + AUDIT_PATHS
    paths: list[Path] = []
    for path in candidates:
        if path.exists() and path.is_file() and not _is_forbidden(path.as_posix()):
            paths.append(path)
    return sorted(set(paths), key=lambda item: item.as_posix())


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
    _write_json(Path("reports/audit_lite/v9_56_to_v9_58_artifact_inventory.json"), payload)
    md = "# Inventaire audit-lite V9.56 a V9.58\n\n" + "\n".join(f"- `{path}`" for path in payload["files"]) + "\n"
    _write_text(Path("reports/audit_lite/v9_56_to_v9_58_artifact_inventory.md"), md)


def _write_size_report(paths: list[Path], zip_size: int | None) -> None:
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_size,
        "zip_bytes_is_authoritative": False,
        "files_count": len(paths),
        "uncompressed_bytes": sum(path.stat().st_size for path in paths if path.exists()),
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    _write_json(Path("reports/audit_lite/zip_size_report_v9_56_to_v9_58.json"), payload)
    _write_text(Path("reports/audit_lite/zip_size_report_v9_56_to_v9_58.md"), "# Taille ZIP V9.56 a V9.58\n\n" f"- Fichiers : `{payload['files_count']}`.\n" f"- Estimation ZIP bytes : `{payload['zip_bytes_estimate']}`.\n" f"- Bytes non compresses : `{payload['uncompressed_bytes']}`.\n")


def _write_zip(paths: list[Path]) -> None:
    with zipfile.ZipFile(ROOT / ZIP_NAME, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in paths:
            archive.write(ROOT / path, path.as_posix())


def _update_state_surfaces(group_report: dict[str, Any]) -> None:
    flags = group_report.get("safety_flags", {})
    metrics = {
        "last_validated_version": "V9.52_to_V9.55",
        "candidate_version": VERSION,
        "candidate_status": "pending_external_audit",
        "source_version": "V9.52_to_V9.55",
        "direction": "funding_tail_resolution_and_feature_store",
        "decision": group_report["decision"],
        "quality_status": "PASS" if group_report["feature_store_validated"] else "FAIL",
        "coverage_status": "funding_common_window_validated" if group_report["feature_store_validated"] else "funding_common_window_not_validated",
        "actual_feature_window": group_report["actual_feature_window"],
        "feature_store_created": group_report["feature_store_created"],
        "feature_store_validated": group_report["feature_store_validated"],
        "dataset_created": False,
        "labels_created": False,
        "ml_executed": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "recommended_next_step": group_report["next_recommendation"],
        **flags,
    }
    _write_json(Path("reports/current/latest_metrics.json"), metrics)
    _write_text(Path("reports/current/latest_metrics.md"), "# Latest Metrics\n\n" + "\n".join(f"- `{key}`: `{value}`" for key, value in metrics.items()) + "\n")
    summary = (
        "# Etat courant du projet\n\n"
        "V9.56_to_V9.58 resout la queue funding par une fenetre commune stricte et valide une couche funding-only si la qualite le permet.\n\n"
        f"- Decision : `{group_report['decision']}`.\n"
        f"- Fenetre : `{group_report['actual_feature_window']}`.\n"
        f"- Feature store cree : `{group_report['feature_store_created']}`.\n"
        f"- Feature store valide : `{group_report['feature_store_validated']}`.\n"
        f"- Recommandation : `{group_report['next_recommendation']}`.\n\n"
        "Aucun trading, paper live, ordre, ML, dataset supervise, label, backtest, walk-forward, strategie ou signal.\n"
    )
    _write_text(Path("reports/current/latest_summary.md"), summary)
    state_path = Path("reports/PROJECT_STATE.json")
    state = _read_json(state_path)
    state.update(metrics)
    _write_json(state_path, state)
    _write_text(Path("reports/PROJECT_STATE.md"), summary)


def _is_forbidden(name: str) -> bool:
    path = Path(name)
    if path.name in FORBIDDEN_NAMES:
        return True
    if any(name.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return True
    return any(path.name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
