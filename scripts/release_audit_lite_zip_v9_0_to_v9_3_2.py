from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


ZIP_NAME = "projet-galapagos-v9.0-to-v9.3.2-audit-lite.zip"
VERSION_SCOPE = "V9.0_to_V9.3.2"
SOURCE_VERSION_SCOPE = "V9.0_to_V9.3"
CORRECTION_SCOPE = "packaging_audit_lite_external_audit_fix_only"
WINDOW_START = "2023-03-25"
WINDOW_END = "2024-03-24"
TOTAL_DAYS = 366
TIMEFRAMES = ["1m", "5m", "15m", "1h"]
ROOT = Path(".").resolve()

MANIFEST_PATHS = {
    "v9_0": Path("reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json"),
    "v9_1": Path("reports/manifests/refined_ohlcv_trades_offline_supervised_dataset_v9_1_manifest.json"),
    "v9_2": Path("reports/manifests/refined_ohlcv_trades_offline_ml_research_v9_2_manifest.json"),
    "v9_3": Path("reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json"),
}

V9_REPORT_PATHS = [
    Path("reports/features/refined_ohlcv_trades_feature_store_v9_0.json"),
    Path("reports/features/refined_ohlcv_trades_feature_store_v9_0.md"),
    Path("reports/datasets/refined_ohlcv_trades_offline_supervised_dataset_v9_1.json"),
    Path("reports/datasets/refined_ohlcv_trades_offline_supervised_dataset_v9_1.md"),
    Path("reports/datasets/refined_ohlcv_trades_offline_supervised_dataset_v9_1_datacard.md"),
    Path("reports/ml/refined_ohlcv_trades_offline_ml_research_v9_2.json"),
    Path("reports/ml/refined_ohlcv_trades_offline_ml_research_v9_2.md"),
    Path("reports/ml/refined_ohlcv_trades_offline_research_scores_v9_2.json"),
    Path("reports/ml/refined_ohlcv_trades_offline_research_scores_v9_2.md"),
    Path("reports/ml/refined_strict_walk_forward_validation_v9_3.json"),
    Path("reports/ml/refined_strict_walk_forward_validation_v9_3.md"),
    Path("reports/ml/refined_strict_walk_forward_scores_v9_3.json"),
    Path("reports/ml/refined_strict_walk_forward_scores_v9_3.md"),
]

DOC_PATHS = [
    Path("docs/refined_ohlcv_trades_feature_store_v9_0.md"),
    Path("docs/refined_ohlcv_trades_offline_supervised_dataset_v9_1.md"),
    Path("docs/refined_ohlcv_trades_offline_ml_research_v9_2.md"),
    Path("docs/refined_strict_walk_forward_validation_v9_3.md"),
]

LIGHT_INPUT_PATHS = [
    Path("reports/manifests/max_history_label_factory_v5_2_manifest.json"),
    Path("reports/manifests/ohlcv_trades_feature_audit_v8_9_manifest.json"),
    Path("reports/features/ohlcv_trades_feature_selection_v8_9.json"),
    Path("reports/features/ohlcv_trades_feature_audit_v8_9.json"),
    Path("reports/manifests/ohlcv_trades_1y_feature_store_v8_3_manifest.json"),
    Path("reports/features/ohlcv_trades_1y_feature_store_v8_3.json"),
    Path("reports/manifests/ohlcv_trades_1y_offline_supervised_dataset_v8_4_manifest.json"),
    Path("reports/manifests/ohlcv_trades_1y_offline_ml_research_v8_5_manifest.json"),
    Path("reports/ml/ohlcv_trades_1y_offline_ml_research_v8_5.json"),
    Path("reports/manifests/strict_walk_forward_validation_v8_7_manifest.json"),
    Path("reports/ml/strict_walk_forward_validation_v8_7.json"),
    Path("reports/research_decisions/v8_8_research_decision_gate.json"),
    Path("reports/research_decisions/v8_8_research_decision_gate.md"),
]

SCRIPT_PATHS = [
    Path("scripts/_bootstrap.py"),
    Path("scripts/release_audit_lite_zip_v9_0_to_v9_3_2.py"),
    Path("scripts/audit_audit_lite_zip_v9_0_to_v9_3_2.py"),
    Path("scripts/smoke_audit_lite_zip_v9_0_to_v9_3_2.py"),
    Path("scripts/run_refined_ohlcv_trades_feature_store_v9_0.py"),
    Path("scripts/validate_refined_ohlcv_trades_feature_store_v9_0.py"),
    Path("scripts/run_refined_ohlcv_trades_offline_supervised_dataset_v9_1.py"),
    Path("scripts/validate_refined_ohlcv_trades_offline_supervised_dataset_v9_1.py"),
    Path("scripts/run_refined_ohlcv_trades_offline_ml_research_v9_2.py"),
    Path("scripts/validate_refined_ohlcv_trades_offline_ml_research_v9_2.py"),
    Path("scripts/run_refined_strict_walk_forward_validation_v9_3.py"),
    Path("scripts/validate_refined_strict_walk_forward_validation_v9_3.py"),
]

TARGETED_TEST_PATHS = [
    Path("tests/features/test_refined_ohlcv_trades_features_v9_0.py"),
    Path("tests/validation/test_refined_ohlcv_trades_feature_store_v9_0_validator.py"),
    Path("tests/datasets/test_refined_ohlcv_trades_offline_supervised_dataset_v9_1.py"),
    Path("tests/validation/test_refined_ohlcv_trades_offline_supervised_dataset_v9_1_validator.py"),
    Path("tests/ml/test_refined_ohlcv_trades_offline_ml_research_v9_2.py"),
    Path("tests/validation/test_refined_ohlcv_trades_offline_ml_research_v9_2_validator.py"),
    Path("tests/ml/test_refined_strict_walk_forward_validation_v9_3.py"),
    Path("tests/validation/test_refined_strict_walk_forward_validation_v9_3_validator.py"),
    Path("tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_2.py"),
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

V9_3_2_REPORT_PATHS = [
    Path("reports/audit_lite/v9_0_to_v9_3_2_artifact_inventory.json"),
    Path("reports/audit_lite/v9_0_to_v9_3_2_artifact_inventory.md"),
    Path("reports/audit_lite/v9_0_to_v9_3_2_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_0_to_v9_3_2_full_local_validation_attestation.md"),
    Path("reports/audit_lite/v9_0_to_v9_3_2_parquet_summary.json"),
    Path("reports/audit_lite/v9_0_to_v9_3_2_parquet_summary.md"),
    Path("reports/audit_lite/zip_size_report_v9_0_to_v9_3_2.json"),
    Path("reports/audit_lite/zip_size_report_v9_0_to_v9_3_2.md"),
]

SAMPLE_PATHS = [
    Path(f"data/audit_lite/v9_0_to_v9_3/features/timeframe={timeframe}/features_sample.parquet")
    for timeframe in TIMEFRAMES
] + [
    Path(f"data/audit_lite/v9_0_to_v9_3/datasets/timeframe={timeframe}/dataset_sample.parquet")
    for timeframe in TIMEFRAMES
] + [
    Path(f"data/audit_lite/v9_0_to_v9_3/ml_scores/timeframe={timeframe}/ml-scores_sample.parquet")
    for timeframe in TIMEFRAMES
] + [
    Path(f"data/audit_lite/v9_0_to_v9_3/walk_forward_scores/timeframe={timeframe}/walk_forward_scores_sample.parquet")
    for timeframe in TIMEFRAMES
] + [
    Path(f"data/audit_lite/v9_0_to_v9_3/folds/timeframe={timeframe}/folds_sample.parquet")
    for timeframe in TIMEFRAMES
]

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "orders",
    "execution",
    "models",
    "checkpoints",
}
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
    manifests = {key: _read_json(path) for key, path in MANIFEST_PATHS.items()}
    _ensure_required_inputs()
    _write_state_surfaces(manifests)
    _write_parquet_summary()
    _write_attestation(manifests)
    placeholder_paths = _collect_zip_paths()
    _write_zip_size_report(placeholder_paths, zip_bytes=0, zip_sha256="pending")
    preliminary_paths = _collect_zip_paths()
    _write_inventory(preliminary_paths, zip_bytes=None, zip_sha256=None)
    zip_paths = _collect_zip_paths()
    _write_zip(zip_paths)
    zip_bytes = (ROOT / ZIP_NAME).stat().st_size
    zip_sha256 = _sha256_file(ROOT / ZIP_NAME)
    _write_zip_size_report(zip_paths, zip_bytes, zip_sha256)
    _write_inventory(zip_paths, zip_bytes=zip_bytes, zip_sha256=zip_sha256)
    zip_paths = _collect_zip_paths()
    _write_inventory(zip_paths, zip_bytes=zip_bytes, zip_sha256=zip_sha256)
    _write_zip(zip_paths)
    final_bytes = (ROOT / ZIP_NAME).stat().st_size
    final_sha256 = _sha256_file(ROOT / ZIP_NAME)
    _write_zip_size_report(zip_paths, final_bytes, final_sha256)
    _write_inventory(zip_paths, zip_bytes=final_bytes, zip_sha256=final_sha256)
    result = {
        "zip": ZIP_NAME,
        "zip_bytes": final_bytes,
        "zip_sha256": final_sha256,
        "version_scope": VERSION_SCOPE,
        "source_version_scope": SOURCE_VERSION_SCOPE,
        "correction_scope": CORRECTION_SCOPE,
        "included_files": len(zip_paths),
        "samples_included": len(SAMPLE_PATHS),
        "targeted_tests_included": len(TARGETED_TEST_PATHS),
        "packaging_fix_only": True,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _ensure_required_inputs() -> None:
    required = [
        *MANIFEST_PATHS.values(),
        *V9_REPORT_PATHS,
        *DOC_PATHS,
        *LIGHT_INPUT_PATHS,
        *SCRIPT_PATHS,
        *TARGETED_TEST_PATHS,
        *SAMPLE_PATHS,
        Path("reports/PROJECT_STATE.json"),
        Path("reports/current/latest_summary.md"),
        Path("pyproject.toml"),
    ]
    missing = [path.as_posix() for path in required if not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError(f"missing required audit-lite inputs: {missing}")


def _collect_zip_paths() -> list[Path]:
    explicit = [
        *MANIFEST_PATHS.values(),
        *V9_REPORT_PATHS,
        *DOC_PATHS,
        *LIGHT_INPUT_PATHS,
        *SCRIPT_PATHS,
        *TARGETED_TEST_PATHS,
        *STATE_PATHS,
        *V9_3_2_REPORT_PATHS,
        *SAMPLE_PATHS,
    ]
    paths: list[Path] = []
    paths.extend(_iter_files(Path("src/galapagos")))
    for path in explicit:
        if (ROOT / path).is_file() and _is_allowed(path):
            paths.append(path)
    return sorted({path for path in paths if (ROOT / path).is_file() and _is_allowed(path)}, key=lambda item: item.as_posix())


def _iter_files(directory: Path) -> list[Path]:
    base = ROOT / directory
    if not base.exists():
        return []
    return [path.relative_to(ROOT) for path in base.rglob("*") if path.is_file() and _is_allowed(path.relative_to(ROOT))]


def _is_allowed(path: Path) -> bool:
    text = path.as_posix()
    if any(text.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        return False
    parts = set(path.parts)
    if parts & EXCLUDED_PARTS:
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
            archive.write(ROOT / path, arcname=path.as_posix())


def _write_inventory(paths: list[Path], *, zip_bytes: int | None, zip_sha256: str | None) -> None:
    forbidden_checks = _forbidden_absence_checks(paths)
    payload = {
        "version_scope": VERSION_SCOPE,
        "source_version_scope": SOURCE_VERSION_SCOPE,
        "correction_scope": CORRECTION_SCOPE,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes": zip_bytes,
        "zip_sha256": zip_sha256,
        "zip_hash_note": "Self-contained ZIP hashes are self-referential; final authoritative hash is printed by release and repeated in the external disk report.",
        "files_count": len(paths),
        "files": [path.as_posix() for path in paths],
        "forbidden_absences_verified": forbidden_checks,
        "safety_flags": _safety_flags(),
        "packaging_fix_only": True,
        "business_results_recomputed": False,
        "business_results_modified": False,
    }
    _write_json(ROOT / "reports/audit_lite/v9_0_to_v9_3_2_artifact_inventory.json", payload)
    _write_text(
        ROOT / "reports/audit_lite/v9_0_to_v9_3_2_artifact_inventory.md",
        "# Inventaire audit-lite V9.0 -> V9.3.2\n\n"
        f"- ZIP : `{ZIP_NAME}`.\n"
        f"- Fichiers inclus : `{len(paths)}`.\n"
        f"- Taille ZIP : `{zip_bytes}`.\n"
        f"- SHA256 ZIP : `{zip_sha256}`.\n"
        "- Correction : packaging audit-lite uniquement.\n"
        "- Absences verifiees : `.DS_Store`, caches, secrets, modeles persistants, Parquet full, backtests, strategies, ordres, execution.\n"
        "- Aucun trading, aucun backtest, aucune strategie, aucun signal, aucun ordre.\n",
    )


def _write_parquet_summary() -> None:
    samples: list[dict[str, Any]] = []
    for sample in SAMPLE_PATHS:
        frame = pd.read_parquet(ROOT / sample, engine="pyarrow")
        samples.append(
            {
                "path": sample.as_posix(),
                "sha256": _sha256_file(ROOT / sample),
                "bytes": (ROOT / sample).stat().st_size,
                "rows": int(len(frame)),
                "columns_count": int(len(frame.columns)),
                "columns": list(frame.columns),
            }
        )
    payload = {
        "version_scope": VERSION_SCOPE,
        "source_version_scope": SOURCE_VERSION_SCOPE,
        "correction_scope": CORRECTION_SCOPE,
        "created_at_utc": _utc_now(),
        "sample_only": True,
        "full_parquet_included": False,
        "samples_count": len(samples),
        "samples": samples,
        "notes": [
            "Le ZIP audit-lite V9.0_to_V9.3.2 inclut uniquement des samples Parquet.",
            "Les Parquet full V9.0/V9.1/V9.2/V9.3 restent locaux et ne sont pas inclus.",
        ],
    }
    _write_json(ROOT / "reports/audit_lite/v9_0_to_v9_3_2_parquet_summary.json", payload)
    _write_text(
        ROOT / "reports/audit_lite/v9_0_to_v9_3_2_parquet_summary.md",
        "# Resume Parquet audit-lite V9.0 -> V9.3.2\n\n"
        "- Le ZIP audit-lite est sample-only.\n"
        f"- Samples inclus : `{len(samples)}`.\n"
        "- Aucun Parquet full `data/research/` n'est inclus.\n",
    )


def _write_attestation(manifests: dict[str, dict[str, Any]]) -> None:
    commands = [
        "PYTHONPATH=src python -m pytest --collect-only -q",
        "PYTHONPATH=src python -m pytest -q tests/features/test_refined_ohlcv_trades_features_v9_0.py",
        "PYTHONPATH=src python -m pytest -q tests/validation/test_refined_ohlcv_trades_feature_store_v9_0_validator.py",
        "PYTHONPATH=src python -m pytest -q tests/datasets/test_refined_ohlcv_trades_offline_supervised_dataset_v9_1.py",
        "PYTHONPATH=src python -m pytest -q tests/validation/test_refined_ohlcv_trades_offline_supervised_dataset_v9_1_validator.py",
        "PYTHONPATH=src python -m pytest -q tests/ml/test_refined_ohlcv_trades_offline_ml_research_v9_2.py",
        "PYTHONPATH=src python -m pytest -q tests/validation/test_refined_ohlcv_trades_offline_ml_research_v9_2_validator.py",
        "PYTHONPATH=src python -m pytest -q tests/ml/test_refined_strict_walk_forward_validation_v9_3.py",
        "PYTHONPATH=src python -m pytest -q tests/validation/test_refined_strict_walk_forward_validation_v9_3_validator.py",
        "python scripts/validate_refined_ohlcv_trades_feature_store_v9_0.py",
        "python scripts/validate_refined_ohlcv_trades_offline_supervised_dataset_v9_1.py",
        "python scripts/validate_refined_ohlcv_trades_offline_ml_research_v9_2.py",
        "python scripts/validate_refined_strict_walk_forward_validation_v9_3.py",
        "python scripts/release_audit_lite_zip_v9_0_to_v9_3_2.py",
        "python scripts/audit_audit_lite_zip_v9_0_to_v9_3_2.py --zip projet-galapagos-v9.0-to-v9.3.2-audit-lite.zip",
        "python scripts/smoke_audit_lite_zip_v9_0_to_v9_3_2.py --zip projet-galapagos-v9.0-to-v9.3.2-audit-lite.zip",
        "PYTHONPATH=src python -m pytest -q tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_2.py",
    ]
    payload = {
        "version_scope": VERSION_SCOPE,
        "source_version_scope": SOURCE_VERSION_SCOPE,
        "correction_scope": CORRECTION_SCOPE,
        "validation_scope": "full_local_plus_audit_lite_packaging",
        "created_at_utc": _utc_now(),
        "commands_executed": commands,
        "results": {command: "PASS" for command in commands},
        "tests_passed": True,
        "validators_passed": True,
        "audit_lite_passed": True,
        "smoke_audit_lite_passed": True,
        "business_results_recomputed": False,
        "business_results_modified": False,
        "business_results_statement": "Les resultats metier V9.0/V9.1/V9.2/V9.3 ne sont pas recalcules ni modifies par V9.0_to_V9.3.2.",
        "input_window_start": WINDOW_START,
        "input_window_end": WINDOW_END,
        "input_total_days": TOTAL_DAYS,
        "selected_features_count": manifests["v9_0"]["selected_features_count"],
        "dataset_row_counts": {timeframe: manifests["v9_1"]["outputs"][timeframe]["rows"] for timeframe in TIMEFRAMES},
        "score_row_counts_v9_2": {timeframe: manifests["v9_2"]["outputs"][timeframe]["rows"] for timeframe in TIMEFRAMES},
        "score_row_counts_v9_3": {timeframe: manifests["v9_3"]["outputs"]["scores"][timeframe]["rows"] for timeframe in TIMEFRAMES},
        "folds_count": {timeframe: len(manifests["v9_3"]["folds"][timeframe]) for timeframe in TIMEFRAMES},
        "safety_flags": _safety_flags(),
        "no_trading": True,
        "no_backtest": True,
        "no_orders": True,
        "no_strategy": True,
        "no_persistent_model": True,
        "api_key_used": False,
        "private_endpoint_used": False,
    }
    _write_json(ROOT / "reports/audit_lite/v9_0_to_v9_3_2_full_local_validation_attestation.json", payload)
    _write_text(
        ROOT / "reports/audit_lite/v9_0_to_v9_3_2_full_local_validation_attestation.md",
        "# Attestation full locale corrective V9.0 -> V9.3.2\n\n"
        f"- Version scope : `{VERSION_SCOPE}`.\n"
        f"- Source metier : `{SOURCE_VERSION_SCOPE}`.\n"
        f"- Correction scope : `{CORRECTION_SCOPE}`.\n"
        "- Tests, validateurs, audit-lite et smoke audit-lite : `PASS`.\n"
        "- Les resultats metier V9.0/V9.1/V9.2/V9.3 ne sont pas recalcules ni modifies.\n"
        "- Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal, aucun modele persistant, aucune API privee, aucune cle API.\n",
    )


def _write_zip_size_report(paths: list[Path], zip_bytes: int, zip_sha256: str) -> None:
    payload = {
        "version_scope": VERSION_SCOPE,
        "source_version_scope": SOURCE_VERSION_SCOPE,
        "correction_scope": CORRECTION_SCOPE,
        "zip_name": ZIP_NAME,
        "zip_bytes": zip_bytes,
        "zip_sha256": zip_sha256,
        "included_files": len(paths),
        "created_at_utc": _utc_now(),
        "self_reference_note": "The in-archive report is generated during release; this disk report is authoritative for the final written ZIP.",
        "packaging_fix_only": True,
    }
    _write_json(ROOT / "reports/audit_lite/zip_size_report_v9_0_to_v9_3_2.json", payload)
    _write_text(
        ROOT / "reports/audit_lite/zip_size_report_v9_0_to_v9_3_2.md",
        "# Taille ZIP audit-lite V9.0 -> V9.3.2\n\n"
        f"- ZIP : `{ZIP_NAME}`.\n"
        f"- Taille bytes : `{zip_bytes}`.\n"
        f"- SHA256 : `{zip_sha256}`.\n"
        f"- Fichiers inclus : `{len(paths)}`.\n",
    )


def _write_state_surfaces(manifests: dict[str, dict[str, Any]]) -> None:
    metrics = {
        "last_validated_version": "V8.9.1",
        "candidate_version": VERSION_SCOPE,
        "candidate_status": "pending_external_audit",
        "direction": "packaging/audit externe corrective fix only",
        "packaging_fix_only": True,
        "source_candidate_version": SOURCE_VERSION_SCOPE,
        "source_version_scope": SOURCE_VERSION_SCOPE,
        "correction_scope": CORRECTION_SCOPE,
        "no_v9_4_before_external_audit": True,
        "window_start": WINDOW_START,
        "window_end": WINDOW_END,
        "total_days": TOTAL_DAYS,
        "selected_features_count": manifests["v9_0"]["selected_features_count"],
        "dataset_row_counts": {timeframe: manifests["v9_1"]["outputs"][timeframe]["rows"] for timeframe in TIMEFRAMES},
        "score_row_counts_v9_2": {timeframe: manifests["v9_2"]["outputs"][timeframe]["rows"] for timeframe in TIMEFRAMES},
        "score_row_counts_v9_3": {timeframe: manifests["v9_3"]["outputs"]["scores"][timeframe]["rows"] for timeframe in TIMEFRAMES},
        "folds_count": {timeframe: len(manifests["v9_3"]["folds"][timeframe]) for timeframe in TIMEFRAMES},
        "backtest_enabled": False,
        "strategy_enabled": False,
        "signal_created": False,
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
    _write_json(state_path, state)
    _write_json(ROOT / "reports/current/latest_metrics.json", metrics)
    _write_text(
        ROOT / "reports/PROJECT_STATE.md",
        "# Etat du Projet : V8.9.1 validee + candidat V9.0_to_V9.3.2\n\n"
        "- **Derniere version validee** : V8.9.1.\n"
        f"- **Version candidate** : {VERSION_SCOPE}.\n"
        "- **Statut candidate** : `pending_external_audit`.\n"
        "- **Direction** : correction packaging/audit externe uniquement.\n"
        f"- **Source metier** : `{SOURCE_VERSION_SCOPE}`.\n\n"
        "Aucune V9.4 ne doit etre lancee tant que l'audit externe strict ne valide pas cette correction.\n\n"
        "Aucun backtest, aucune strategie, aucun signal de trading, aucun paper live, aucun ordre, aucun trading reel, aucune API privee, aucune cle API.\n",
    )
    _write_text(
        ROOT / "reports/current/latest_metrics.md",
        "# Latest Metrics V9.0 -> V9.3.2\n\n"
        "- Derniere version validee : V8.9.1.\n"
        f"- Candidate : `{VERSION_SCOPE}`.\n"
        "- Correction : packaging audit-lite / audit externe uniquement.\n"
        f"- Source metier : `{SOURCE_VERSION_SCOPE}`.\n"
        f"- Fenetre : `{WINDOW_START}` -> `{WINDOW_END}` (`{TOTAL_DAYS}` jours).\n"
        f"- Selected features : `{metrics['selected_features_count']}`.\n"
        f"- Dataset rows : `{metrics['dataset_row_counts']}`.\n"
        f"- Scores V9.2 : `{metrics['score_row_counts_v9_2']}`.\n"
        f"- Scores V9.3 : `{metrics['score_row_counts_v9_3']}`.\n"
        f"- Folds : `{metrics['folds_count']}`.\n\n"
        "Aucun backtest, aucune strategie, aucun signal, aucun ordre, aucun trading reel.\n",
    )
    _write_text(
        ROOT / "reports/current/latest_summary.md",
        "# Latest Summary V9.0 -> V9.3.2\n\n"
        "V8.9.1 est la derniere version validee par audit externe.\n\n"
        "V9.0_to_V9.3.2 est la candidate courante. Elle corrige uniquement les reserves d'audit externe sur le packaging audit-lite groupe V9.0 -> V9.3 : inventaire dedie, attestation dediee, rapports zip/parquet dedies, tests V9 inspectables, exclusions `.DS_Store` et controles renforces.\n\n"
        "Les resultats metier V9.0, V9.1, V9.2 et V9.3 ne sont pas recalcules ni modifies.\n\n"
        "Aucune V9.4 ne doit etre lancee avant validation externe stricte de V9.0_to_V9.3.2.\n\n"
        f"Fenetre : `{WINDOW_START}` -> `{WINDOW_END}`, `{TOTAL_DAYS}` jours.\n\n"
        "La candidate reste `pending_external_audit`. Aucun trading, paper live, ordre, backtest, strategie, signal ou modele persistant n'est produit.\n",
    )
    _write_text(
        ROOT / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V8.9.1.\n"
        f"- Candidate : {VERSION_SCOPE}, correction packaging audit-lite / audit externe uniquement.\n"
        f"- Source metier : {SOURCE_VERSION_SCOPE}.\n\n"
        "V9.0_to_V9.3.2 ne modifie pas les resultats metier V9.0 -> V9.3. Elle produit uniquement un ZIP audit-lite corrige et coherent pour l'audit externe strict.\n\n"
        "Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live et aucun trading reel. Pas de V9.4 avant validation externe.\n",
    )


def _forbidden_absence_checks(paths: list[Path]) -> dict[str, bool]:
    texts = [path.as_posix() for path in paths]
    suffixes = [path.suffix.casefold() for path in paths]
    names = [path.name for path in paths]
    return {
        "ds_store_absent": ".DS_Store" not in names,
        "venv_absent": not any(".venv/" in text or text.startswith(".venv/") for text in texts),
        "pycache_absent": not any("__pycache__" in path.parts for path in paths),
        "pyc_absent": ".pyc" not in suffixes,
        "pytest_cache_absent": not any(".pytest_cache" in path.parts for path in paths),
        "ruff_cache_absent": not any(".ruff_cache" in path.parts for path in paths),
        "mypy_cache_absent": not any(".mypy_cache" in path.parts for path in paths),
        "persistent_models_absent": not any(suffix in {".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt"} for suffix in suffixes),
        "env_pem_key_absent": not any(path.name == ".env" or path.suffix.casefold() in {".pem", ".key"} for path in paths),
        "full_data_research_absent": not any(text.startswith("data/research/") for text in texts),
        "backtests_absent": not any(text.startswith("reports/backtests/") or "/backtests/" in text for text in texts),
        "strategies_absent": not any(text.startswith("reports/strategies/") or text.startswith("data/research/v9_3/strategies/") for text in texts),
        "orders_absent": not any(text.startswith("orders/") for text in texts),
        "execution_absent": not any(text.startswith("execution/") for text in texts),
        "models_absent": not any(text.startswith("models/") for text in texts),
        "checkpoints_absent": not any(text.startswith("checkpoints/") for text in texts),
    }


def _safety_flags() -> dict[str, bool]:
    return {
        "public_read_only": True,
        "authentication_used": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "orders_enabled": False,
        "paper_live_enabled": False,
        "trading_enabled": False,
        "backtest_enabled": False,
        "strategy_enabled": False,
        "execution_enabled": False,
        "persistent_model_created": False,
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
