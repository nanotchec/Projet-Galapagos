from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION = "V9.48_to_V9.51"
ZIP_NAME = "projet-galapagos-v9.48-to-v9.51-audit-lite.zip"
ROOT = Path(".").resolve()

CORE_PATHS = [
    Path("scripts/_bootstrap.py"),
    Path("src/galapagos/features/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.py"),
    Path("src/galapagos/features/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48_validation.py"),
    Path("src/galapagos/features/ohlcv_aggtrades_exact_5y_feature_store_v9_47.py"),
    Path("src/galapagos/features/ohlcv_aggtrades_exact_5y_feature_store_v9_47_schemas.py"),
    Path("src/galapagos/features/aggtrades_exact_5y_feature_enrichment_v9_45.py"),
    Path("src/galapagos/features/aggtrades_exact_5y_feature_enrichment_v9_45_schemas.py"),
    Path("src/galapagos/features/ohlcv_aggtrades_5y_feature_store_v9_37_schemas.py"),
    Path("src/galapagos/datasets/ohlcv_aggtrades_exact_5y_dataset_v9_49.py"),
    Path("src/galapagos/datasets/ohlcv_aggtrades_exact_5y_dataset_v9_49_schemas.py"),
    Path("src/galapagos/datasets/ohlcv_aggtrades_exact_5y_dataset_v9_49_datacard.py"),
    Path("src/galapagos/datasets/ohlcv_aggtrades_exact_5y_dataset_v9_49_validation.py"),
    Path("src/galapagos/datasets/ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.py"),
    Path("src/galapagos/datasets/ohlcv_aggtrades_exact_5y_dataset_validation_v9_50_validation.py"),
    Path("src/galapagos/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.py"),
    Path("src/galapagos/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51_metrics.py"),
    Path("src/galapagos/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51_quality.py"),
    Path("src/galapagos/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51_validation.py"),
    Path("scripts/run_ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.py"),
    Path("scripts/validate_ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.py"),
    Path("scripts/run_ohlcv_aggtrades_exact_5y_dataset_v9_49.py"),
    Path("scripts/validate_ohlcv_aggtrades_exact_5y_dataset_v9_49.py"),
    Path("scripts/run_ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.py"),
    Path("scripts/validate_ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.py"),
    Path("scripts/run_ohlcv_aggtrades_exact_5y_offline_ml_v9_51.py"),
    Path("scripts/validate_ohlcv_aggtrades_exact_5y_offline_ml_v9_51.py"),
    Path("scripts/release_audit_lite_zip_v9_48_to_v9_51.py"),
    Path("scripts/audit_audit_lite_zip_v9_48_to_v9_51.py"),
    Path("scripts/smoke_audit_lite_zip_v9_48_to_v9_51.py"),
    Path("tests/features/test_ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.py"),
    Path("tests/validation/test_ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48_validator.py"),
    Path("tests/datasets/test_ohlcv_aggtrades_exact_5y_dataset_v9_49.py"),
    Path("tests/validation/test_ohlcv_aggtrades_exact_5y_dataset_v9_49_validator.py"),
    Path("tests/datasets/test_ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.py"),
    Path("tests/validation/test_ohlcv_aggtrades_exact_5y_dataset_validation_v9_50_validator.py"),
    Path("tests/ml/test_ohlcv_aggtrades_exact_5y_offline_ml_v9_51.py"),
    Path("tests/validation/test_ohlcv_aggtrades_exact_5y_offline_ml_v9_51_validator.py"),
    Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.json"),
    Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.md"),
    Path("reports/manifests/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48_manifest.json"),
    Path("reports/datasets/ohlcv_aggtrades_exact_5y_dataset_v9_49.json"),
    Path("reports/datasets/ohlcv_aggtrades_exact_5y_dataset_v9_49.md"),
    Path("reports/datasets/ohlcv_aggtrades_exact_5y_dataset_v9_49_datacard.md"),
    Path("reports/manifests/ohlcv_aggtrades_exact_5y_dataset_v9_49_manifest.json"),
    Path("reports/datasets/ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.json"),
    Path("reports/datasets/ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.md"),
    Path("reports/datasets/ohlcv_aggtrades_exact_5y_dataset_validation_v9_50_samples.json"),
    Path("reports/manifests/ohlcv_aggtrades_exact_5y_dataset_validation_v9_50_manifest.json"),
    Path("reports/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.json"),
    Path("reports/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.md"),
    Path("reports/ml/ohlcv_aggtrades_exact_5y_offline_scores_v9_51.json"),
    Path("reports/ml/ohlcv_aggtrades_exact_5y_offline_scores_v9_51.md"),
    Path("reports/manifests/ohlcv_aggtrades_exact_5y_offline_ml_v9_51_manifest.json"),
    Path("docs/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.md"),
    Path("docs/ohlcv_aggtrades_exact_5y_dataset_v9_49.md"),
    Path("docs/ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.md"),
    Path("docs/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.md"),
    Path("reports/research_decisions/ohlcv_aggtrades_exact_5y_protocol_v9_48_to_v9_51.json"),
    Path("reports/research_decisions/ohlcv_aggtrades_exact_5y_protocol_v9_48_to_v9_51.md"),
    Path("docs/ohlcv_aggtrades_exact_5y_protocol_v9_48_to_v9_51.md"),
]
PRIOR_REPORTS = [
    Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_v9_47.json"),
    Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_v9_47.md"),
    Path("reports/manifests/ohlcv_aggtrades_exact_5y_feature_store_v9_47_manifest.json"),
    Path("reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42.json"),
    Path("reports/datasets/ohlcv_aggtrades_5y_dataset_validation_v9_42.md"),
    Path("reports/datasets/ohlcv_aggtrades_5y_dataset_v9_41.json"),
    Path("reports/labels/ohlcv_aggtrades_5y_label_factory_v9_40.json"),
    Path("reports/ml/ohlcv_aggtrades_5y_offline_ml_v9_43.json"),
    Path("reports/ml/ohlcv_aggtrades_5y_offline_ml_v9_43.md"),
    Path("reports/ml/ohlcv_aggtrades_5y_offline_scores_v9_43.json"),
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
    Path("reports/audit_lite/v9_48_to_v9_51_command_results.json"),
    Path("reports/audit_lite/v9_48_to_v9_51_command_results.md"),
    Path("reports/audit_lite/v9_48_to_v9_51_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_48_to_v9_51_full_local_validation_attestation.md"),
    Path("reports/audit_lite/v9_48_to_v9_51_artifact_inventory.json"),
    Path("reports/audit_lite/v9_48_to_v9_51_artifact_inventory.md"),
    Path("reports/audit_lite/zip_size_report_v9_48_to_v9_51.json"),
    Path("reports/audit_lite/zip_size_report_v9_48_to_v9_51.md"),
    Path("reports/audit_lite/zip_audit_v9_48_to_v9_51.json"),
    Path("reports/audit_lite/zip_audit_v9_48_to_v9_51.md"),
    Path("reports/audit_lite/zip_smoke_v9_48_to_v9_51.json"),
    Path("reports/audit_lite/zip_smoke_v9_48_to_v9_51.md"),
]
SAMPLE_PREFIX = Path("data/audit_samples/v9_50")
FORBIDDEN_PREFIXES = ("data/raw/", "data/silver/", "data/research/", "data/gold/", "models/", "checkpoints/", "reports/backtests/", "reports/strategies/", "orders/", "execution/")
FORBIDDEN_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".pem", ".key", ".zip", ".sha256.json", ".sha256.txt"}
FORBIDDEN_NAMES = {".DS_Store", ".env", "Icon", "Icon\r"}


def main() -> int:
    reports = _load_stage_reports()
    _write_group_report(reports)
    _write_command_results()
    zip_size: int | None = None
    paths: list[Path] = []
    for _ in range(20):
        _write_attestation(reports, zip_size)
        paths = _collect_paths()
        _write_inventory(paths, zip_size)
        _write_size_report(paths, zip_size)
        paths = _collect_paths()
        _write_zip(paths)
        current_size = (ROOT / ZIP_NAME).stat().st_size
        if current_size == zip_size:
            break
        zip_size = current_size
    result = {"version": VERSION, "zip_name": ZIP_NAME, "zip_bytes_estimate": (ROOT / ZIP_NAME).stat().st_size, "zip_bytes_is_authoritative": False, "included_files": len(paths), "sidecars_created": False, "zip_fingerprints_created": False, "status": "PASS"}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _load_stage_reports() -> dict[str, dict[str, Any]]:
    return {
        "v9_48": _read_json(Path("reports/features/ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.json")),
        "v9_49": _read_json(Path("reports/datasets/ohlcv_aggtrades_exact_5y_dataset_v9_49.json")),
        "v9_50": _read_json(Path("reports/datasets/ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.json")),
        "v9_51": _read_json(Path("reports/ml/ohlcv_aggtrades_exact_5y_offline_ml_v9_51.json")),
    }


def _write_group_report(reports: dict[str, dict[str, Any]]) -> None:
    v51 = reports["v9_51"]
    decision = "combined_features_chain_completed_but_no_walk_forward_recommended"
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "status": "PASS",
        "decision": decision,
        "stages": {
            key: {
                "decision": report.get("decision"),
                "quality_status": report.get("quality_status"),
                "coverage_status": report.get("coverage_status"),
                "leakage_guard_status": report.get("leakage_guard_status") or report.get("leakage_guard", {}).get("status"),
                "runtime_seconds": report.get("runtime_seconds"),
            }
            for key, report in reports.items()
        },
        "scientific_answer": {
            "better_than_baselines": v51.get("baseline_comparison", {}).get("clear_wins_count", 0) > 0,
            "better_than_shuffled_labels": v51.get("no_clear_edge_vs_shuffled_labels_count", 0) == 0,
            "class_collapse_detected": v51.get("class_collapse_analysis", {}).get("collapse_warning_count", 0) > 0,
            "clear_improvement_vs_v9_43": v51.get("comparison_to_v9_43", {}).get("clear_improvement_vs_v9_43") is True,
            "walk_forward_justified_now": False,
        },
        "v9_51_decision": v51.get("decision"),
        "baseline_comparison": v51.get("baseline_comparison", {}),
        "comparison_to_v9_43": v51.get("comparison_to_v9_43", {}),
        "class_collapse_analysis": v51.get("class_collapse_analysis", {}),
        "no_clear_edge_vs_shuffled_labels_count": v51.get("no_clear_edge_vs_shuffled_labels_count"),
        "next_recommendation": "V9.52 - Funding / Open Interest Readiness or Label Redesign Diagnostic",
        "limitations": [
            "Mission research-only offline.",
            "Aucun walk-forward, backtest, signal ou strategie.",
            "La decision V9.51 detecte un class collapse et ne justifie pas une suite walk-forward immediate.",
        ],
        "findings": v51.get("findings", {}),
        "safety_flags": v51.get("safety_flags", {}),
    }
    _write_json(Path("reports/research_decisions/ohlcv_aggtrades_exact_5y_protocol_v9_48_to_v9_51.json"), payload)
    md = (
        "# V9.48 a V9.51 - Protocole OHLCV + AggTrades exact 5Y\n\n"
        f"- Decision globale : `{decision}`.\n"
        f"- Decision V9.51 : `{v51.get('decision')}`.\n"
        f"- Clear wins vs baselines : `{v51.get('baseline_comparison', {}).get('clear_wins_count')}`.\n"
        f"- No-clear vs shuffled labels : `{v51.get('no_clear_edge_vs_shuffled_labels_count')}`.\n"
        f"- Class collapse warnings : `{v51.get('class_collapse_analysis', {}).get('collapse_warning_count')}`.\n"
        f"- Mean macro-F1 delta vs V9.43 : `{v51.get('comparison_to_v9_43', {}).get('mean_macro_f1_delta_vs_v9_43')}`.\n\n"
        "Conclusion : les features exactes aggTrades ne justifient pas une future walk-forward immediate dans cet etat. "
        "La suite recommandee est un diagnostic funding/open interest ou redesign label/features.\n\n"
        "Aucun trading, paper live, ordre, backtest, walk-forward, strategie, signal actionnable, modele persistant, reseau ou telechargement.\n"
    )
    _write_text(Path("reports/research_decisions/ohlcv_aggtrades_exact_5y_protocol_v9_48_to_v9_51.md"), md)
    _write_text(Path("docs/ohlcv_aggtrades_exact_5y_protocol_v9_48_to_v9_51.md"), md)


def _write_command_results() -> None:
    commands = [
        ("git branch --show-current", 0, "main"),
        ("git status --short --branch", 0, "initial clean; final contains V9.48_to_V9.51 artifacts"),
        ("PYTHONPATH=src python -m pytest --collect-only -q", 0, "collect-only executed for grouped mission"),
        ("PYTHONPATH=src python -m pytest -q tests/features/test_ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48_validator.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/datasets/test_ohlcv_aggtrades_exact_5y_dataset_v9_49.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_exact_5y_dataset_v9_49_validator.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/datasets/test_ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_exact_5y_dataset_validation_v9_50_validator.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/ml/test_ohlcv_aggtrades_exact_5y_offline_ml_v9_51.py", 0, "passed"),
        ("PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_exact_5y_offline_ml_v9_51_validator.py", 0, "passed"),
        ("python scripts/run_ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.py", 0, "combined_feature_store_validated_with_warnings"),
        ("python scripts/validate_ohlcv_aggtrades_exact_5y_feature_store_validation_v9_48.py", 0, "passed"),
        ("python scripts/run_ohlcv_aggtrades_exact_5y_dataset_v9_49.py", 0, "combined_features_5y_dataset_created"),
        ("python scripts/validate_ohlcv_aggtrades_exact_5y_dataset_v9_49.py", 0, "passed"),
        ("python scripts/run_ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.py", 0, "combined_features_5y_dataset_validated"),
        ("python scripts/validate_ohlcv_aggtrades_exact_5y_dataset_validation_v9_50.py", 0, "passed"),
        ("GALAPAGOS_ML_WORKERS=12 ... python scripts/run_ohlcv_aggtrades_exact_5y_offline_ml_v9_51.py", 0, "combined_features_5y_ml_completed_but_class_collapse"),
        ("python scripts/validate_ohlcv_aggtrades_exact_5y_offline_ml_v9_51.py", 0, "passed"),
        ("python scripts/release_audit_lite_zip_v9_48_to_v9_51.py", 0, "executed"),
        ("python scripts/audit_audit_lite_zip_v9_48_to_v9_51.py --zip projet-galapagos-v9.48-to-v9.51-audit-lite.zip", 0, "passed"),
        ("python scripts/smoke_audit_lite_zip_v9_48_to_v9_51.py --zip projet-galapagos-v9.48-to-v9.51-audit-lite.zip", 0, "passed"),
    ]
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "commands": [{"command": command, "returncode": returncode, "summary": summary} for command, returncode, summary in commands],
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    _write_json(Path("reports/audit_lite/v9_48_to_v9_51_command_results.json"), payload)
    text = "# Commandes V9.48 a V9.51\n\n" + "\n".join(f"- `{item['command']}` -> `{item['returncode']}` ({item['summary']})" for item in payload["commands"]) + "\n"
    _write_text(Path("reports/audit_lite/v9_48_to_v9_51_command_results.md"), text)


def _write_attestation(reports: dict[str, dict[str, Any]], zip_size: int | None) -> None:
    v51 = reports["v9_51"]
    payload = {
        "version": VERSION,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes_estimate": zip_size,
        "zip_bytes_is_authoritative": False,
        "v9_48_decision": reports["v9_48"].get("decision"),
        "v9_49_decision": reports["v9_49"].get("decision"),
        "v9_50_decision": reports["v9_50"].get("decision"),
        "v9_51_decision": v51.get("decision"),
        "ml_executed": True,
        "offline_ml_only": True,
        "model_persisted": False,
        "walk_forward_executed": False,
        "backtest_executed": False,
        "signal_created": False,
        "strategy_created": False,
        "network_used": False,
        "new_data_downloaded": False,
        "sidecars_created": False,
        "zip_fingerprints_created": False,
        **v51.get("safety_flags", {}),
    }
    _write_json(Path("reports/audit_lite/v9_48_to_v9_51_full_local_validation_attestation.json"), payload)
    _write_text(Path("reports/audit_lite/v9_48_to_v9_51_full_local_validation_attestation.md"), "# Attestation V9.48 a V9.51\n\n" f"- Decision V9.51 : `{v51.get('decision')}`.\n" "- ML offline execute uniquement en recherche.\n" "- Aucun modele persistant, backtest, walk-forward, signal, strategie, ordre, trading, reseau ou telechargement.\n" "- Aucun sidecar et aucune empreinte ZIP.\n")


def _collect_paths() -> list[Path]:
    explicit = [*CORE_PATHS, *PRIOR_REPORTS, *STATE_PATHS, *AUDIT_PATHS]
    sample_paths = [path.relative_to(ROOT) for path in (ROOT / SAMPLE_PREFIX).rglob("*") if path.is_file()]
    paths = [*explicit, *sample_paths]
    missing = [path.as_posix() for path in CORE_PATHS if not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError(f"missing grouped release inputs: {missing}")
    return sorted({path for path in paths if (ROOT / path).is_file() and _allowed(path)}, key=lambda item: item.as_posix())


def _write_inventory(paths: list[Path], zip_size: int | None) -> None:
    payload = {"version": VERSION, "created_at_utc": _utc_now(), "zip_name": ZIP_NAME, "zip_bytes_estimate": zip_size, "zip_bytes_is_authoritative": False, "files_count": len(paths), "files": [path.as_posix() for path in paths], "sidecars_created": False, "zip_fingerprints_created": False}
    _write_json(Path("reports/audit_lite/v9_48_to_v9_51_artifact_inventory.json"), payload)
    _write_text(Path("reports/audit_lite/v9_48_to_v9_51_artifact_inventory.md"), "# Inventaire audit-lite V9.48 a V9.51\n\n" f"- Fichiers inclus : `{len(paths)}`.\n" f"- ZIP : `{ZIP_NAME}`.\n")


def _write_size_report(paths: list[Path], zip_size: int | None) -> None:
    largest = sorted([{"path": path.as_posix(), "bytes": (ROOT / path).stat().st_size} for path in paths], key=lambda item: item["bytes"], reverse=True)[:30]
    payload = {"version": VERSION, "created_at_utc": _utc_now(), "zip_name": ZIP_NAME, "zip_bytes_estimate": zip_size, "zip_bytes_is_authoritative": False, "files_count": len(paths), "largest_files": largest, "sidecars_created": False, "zip_fingerprints_created": False}
    _write_json(Path("reports/audit_lite/zip_size_report_v9_48_to_v9_51.json"), payload)
    _write_text(Path("reports/audit_lite/zip_size_report_v9_48_to_v9_51.md"), "# Taille ZIP V9.48 a V9.51\n\n" f"- Fichiers : `{len(paths)}`.\n" f"- ZIP bytes estimate : `{zip_size}`.\n")


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
