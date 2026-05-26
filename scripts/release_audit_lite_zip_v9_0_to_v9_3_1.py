from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


ZIP_NAME = "projet-galapagos-v9.0-to-v9.3.1-audit-lite.zip"
VERSION_SCOPE = "V9.0_to_V9.3.1"
SOURCE_VERSION_SCOPE = "V9.0_to_V9.3"
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
    Path("scripts/release_audit_lite_zip_v9_0_to_v9_3_1.py"),
    Path("scripts/audit_audit_lite_zip_v9_0_to_v9_3_1.py"),
    Path("scripts/smoke_audit_lite_zip_v9_0_to_v9_3_1.py"),
    Path("scripts/run_refined_ohlcv_trades_feature_store_v9_0.py"),
    Path("scripts/validate_refined_ohlcv_trades_feature_store_v9_0.py"),
    Path("scripts/run_refined_ohlcv_trades_offline_supervised_dataset_v9_1.py"),
    Path("scripts/validate_refined_ohlcv_trades_offline_supervised_dataset_v9_1.py"),
    Path("scripts/run_refined_ohlcv_trades_offline_ml_research_v9_2.py"),
    Path("scripts/validate_refined_ohlcv_trades_offline_ml_research_v9_2.py"),
    Path("scripts/run_refined_strict_walk_forward_validation_v9_3.py"),
    Path("scripts/validate_refined_strict_walk_forward_validation_v9_3.py"),
]

TEST_PATHS = [
    Path("tests/audit_lite/test_grouped_audit_lite_v9_0_to_v9_3_1.py"),
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

AUDIT_LITE_SOURCE_PATHS = [
    Path("reports/audit_lite/v9_0_to_v9_3_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_0_to_v9_3_full_local_validation_attestation.md"),
    Path("reports/audit_lite/v9_0_to_v9_3_artifact_inventory.json"),
    Path("reports/audit_lite/v9_0_to_v9_3_artifact_inventory.md"),
    Path("reports/audit_lite/v9_0_to_v9_3_parquet_summary.json"),
    Path("reports/audit_lite/v9_0_to_v9_3_parquet_summary.md"),
    Path("reports/audit_lite/zip_size_report_v9_0_to_v9_3.json"),
    Path("reports/audit_lite/zip_size_report_v9_0_to_v9_3.md"),
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
EXCLUDED_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt", ".zip"}
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
    zip_paths = _collect_zip_paths()
    _write_zip(zip_paths)
    _write_zip_size_report(zip_paths)
    result = {
        "zip": ZIP_NAME,
        "zip_bytes": (ROOT / ZIP_NAME).stat().st_size,
        "zip_sha256": _sha256_file(ROOT / ZIP_NAME),
        "version_scope": VERSION_SCOPE,
        "source_version_scope": SOURCE_VERSION_SCOPE,
        "included_files": len(zip_paths),
        "samples_included": len(SAMPLE_PATHS),
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
        *TEST_PATHS,
        *AUDIT_LITE_SOURCE_PATHS,
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
        *TEST_PATHS,
        *STATE_PATHS,
        *AUDIT_LITE_SOURCE_PATHS,
        *SAMPLE_PATHS,
    ]
    paths: list[Path] = []
    for directory in [
        Path("src/galapagos"),
    ]:
        paths.extend(_iter_files(directory))
    for path in explicit:
        if (ROOT / path).is_file() and _is_allowed(path):
            paths.append(path)
    unique = sorted({path for path in paths if (ROOT / path).is_file() and _is_allowed(path)}, key=lambda item: item.as_posix())
    return unique


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
    return path.suffix.casefold() not in EXCLUDED_SUFFIXES


def _write_zip(paths: list[Path]) -> None:
    zip_path = ROOT / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in paths:
            archive.write(ROOT / path, arcname=path.as_posix())


def _write_zip_size_report(paths: list[Path]) -> None:
    zip_path = ROOT / ZIP_NAME
    payload = {
        "version_scope": VERSION_SCOPE,
        "source_version_scope": SOURCE_VERSION_SCOPE,
        "packaging_fix_only": True,
        "zip_name": ZIP_NAME,
        "zip_bytes": zip_path.stat().st_size,
        "zip_sha256": _sha256_file(zip_path),
        "included_files": len(paths),
        "created_at_utc": _utc_now(),
    }
    _write_json(ROOT / "reports/audit_lite/zip_size_report_v9_0_to_v9_3_1.json", payload)
    _write_text(
        ROOT / "reports/audit_lite/zip_size_report_v9_0_to_v9_3_1.md",
        "# Taille ZIP audit-lite V9.0 -> V9.3.1\n\n"
        f"- ZIP : `{ZIP_NAME}`.\n"
        f"- Taille bytes : `{payload['zip_bytes']}`.\n"
        f"- SHA256 : `{payload['zip_sha256']}`.\n"
        "- Correction : packaging audit-lite uniquement, sans modification fonctionnelle V9.0 -> V9.3.\n",
    )


def _write_state_surfaces(manifests: dict[str, dict[str, Any]]) -> None:
    metrics = {
        "last_validated_version": "V8.9.1",
        "candidate_version": VERSION_SCOPE,
        "candidate_status": "pending_external_audit",
        "direction": "grouped audit-lite packaging fix for refined OHLCV + trades V9.0 to V9.3",
        "packaging_fix_only": True,
        "source_candidate_version": SOURCE_VERSION_SCOPE,
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
        "external_validation_required": True,
    }
    state_path = ROOT / "reports/PROJECT_STATE.json"
    state = _read_json(state_path) if state_path.exists() else {}
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(ROOT / "reports/current/latest_metrics.json", metrics)
    _write_text(
        ROOT / "reports/PROJECT_STATE.md",
        "# Etat du Projet : V8.9.1 validee + candidat V9.0_to_V9.3.1\n\n"
        "- **Derniere version validee** : V8.9.1.\n"
        f"- **Version candidate** : {VERSION_SCOPE}.\n"
        "- **Statut candidate** : `pending_external_audit`.\n"
        "- **Direction** : correction packaging audit-lite groupe V9.0 -> V9.3.1.\n\n"
        "V9.0_to_V9.3.1 corrige uniquement le packaging audit-lite groupe : inclusion de `scripts/_bootstrap.py`, des petits manifests/reports d'entree et de tests sample-only autoporteurs.\n\n"
        "Aucun backtest, aucune strategie, aucun signal de trading, aucun paper live, aucun ordre et aucun trading reel.\n",
    )
    _write_text(
        ROOT / "reports/current/latest_metrics.md",
        "# Latest Metrics V9.0 -> V9.3.1\n\n"
        "- Derniere version validee : V8.9.1.\n"
        f"- Candidate : `{VERSION_SCOPE}`.\n"
        "- Correction : packaging audit-lite uniquement.\n"
        f"- Source metier conservee : `{SOURCE_VERSION_SCOPE}`.\n"
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
        "# Latest Summary V9.0 -> V9.3.1\n\n"
        "V8.9.1 est la derniere version validee par audit externe.\n\n"
        "V9.0_to_V9.3.1 est la candidate courante. Elle corrige uniquement le packaging audit-lite groupe V9.0 -> V9.3 : le ZIP inclut `scripts/_bootstrap.py`, les petits manifests/reports d'entree requis et des tests audit-lite sample-only autoporteurs.\n\n"
        "Les resultats metier V9.0, V9.1, V9.2 et V9.3 ne sont pas recalcules ni modifies.\n\n"
        f"Fenetre : `{WINDOW_START}` -> `{WINDOW_END}`, `{TOTAL_DAYS}` jours.\n\n"
        "La candidate reste `pending_external_audit`. Aucun trading, paper live, ordre, backtest, strategie, signal ou modele persistant n'est produit.\n",
    )
    _write_text(
        ROOT / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V8.9.1.\n"
        f"- Candidate : {VERSION_SCOPE}, correction packaging audit-lite groupe V9.0 -> V9.3.\n\n"
        "V9.0_to_V9.3.1 ne modifie pas les resultats metier V9.0 -> V9.3. Elle produit uniquement un ZIP audit-lite corrige et autoporteur pour l'audit externe strict.\n\n"
        "Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live et aucun trading reel.\n",
    )


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
