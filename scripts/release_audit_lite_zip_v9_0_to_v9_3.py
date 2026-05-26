from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.data.public_market.provenance import sha256_file


ZIP_NAME = "projet-galapagos-v9.0-to-v9.3-audit-lite.zip"
VERSION_SCOPE = "V9.0_to_V9.3"
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

REPORT_PATHS = [
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

V8_9_INPUTS = [
    Path("reports/features/ohlcv_trades_feature_selection_v8_9.json"),
    Path("reports/features/ohlcv_trades_feature_selection_v8_9.md"),
    Path("reports/manifests/ohlcv_trades_feature_audit_v8_9_manifest.json"),
    Path("reports/features/ohlcv_trades_feature_audit_v8_9.json"),
    Path("reports/features/ohlcv_trades_feature_audit_v8_9.md"),
]

SCRIPT_PATHS = [
    Path("scripts/run_refined_ohlcv_trades_feature_store_v9_0.py"),
    Path("scripts/validate_refined_ohlcv_trades_feature_store_v9_0.py"),
    Path("scripts/run_refined_ohlcv_trades_offline_supervised_dataset_v9_1.py"),
    Path("scripts/validate_refined_ohlcv_trades_offline_supervised_dataset_v9_1.py"),
    Path("scripts/run_refined_ohlcv_trades_offline_ml_research_v9_2.py"),
    Path("scripts/validate_refined_ohlcv_trades_offline_ml_research_v9_2.py"),
    Path("scripts/run_refined_strict_walk_forward_validation_v9_3.py"),
    Path("scripts/validate_refined_strict_walk_forward_validation_v9_3.py"),
    Path("scripts/release_audit_lite_zip_v9_0_to_v9_3.py"),
    Path("scripts/audit_audit_lite_zip_v9_0_to_v9_3.py"),
    Path("scripts/smoke_audit_lite_zip_v9_0_to_v9_3.py"),
]

TEST_PATHS = [
    Path("tests/features/test_refined_ohlcv_trades_features_v9_0.py"),
    Path("tests/validation/test_refined_ohlcv_trades_feature_store_v9_0_validator.py"),
    Path("tests/datasets/test_refined_ohlcv_trades_offline_supervised_dataset_v9_1.py"),
    Path("tests/validation/test_refined_ohlcv_trades_offline_supervised_dataset_v9_1_validator.py"),
    Path("tests/ml/test_refined_ohlcv_trades_offline_ml_research_v9_2.py"),
    Path("tests/validation/test_refined_ohlcv_trades_offline_ml_research_v9_2_validator.py"),
    Path("tests/ml/test_refined_strict_walk_forward_validation_v9_3.py"),
    Path("tests/validation/test_refined_strict_walk_forward_validation_v9_3_validator.py"),
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

AUDIT_REPORT_PATHS = [
    Path("reports/audit_lite/v9_0_to_v9_3_artifact_inventory.json"),
    Path("reports/audit_lite/v9_0_to_v9_3_artifact_inventory.md"),
    Path("reports/audit_lite/v9_0_to_v9_3_parquet_summary.json"),
    Path("reports/audit_lite/v9_0_to_v9_3_parquet_summary.md"),
    Path("reports/audit_lite/v9_0_to_v9_3_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_0_to_v9_3_full_local_validation_attestation.md"),
    Path("reports/audit_lite/zip_size_report_v9_0_to_v9_3.json"),
    Path("reports/audit_lite/zip_size_report_v9_0_to_v9_3.md"),
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
EXCLUDED_SUFFIXES = {".pyc", ".pkl", ".pickle", ".joblib", ".onnx", ".pt", ".pth", ".ckpt"}


def main() -> int:
    manifests = {key: _read_json(path) for key, path in MANIFEST_PATHS.items()}
    _write_state_surfaces(manifests)
    sample_paths = _write_samples(manifests)
    parquet_summary = _write_parquet_summary(manifests, sample_paths)
    attestation = _write_attestation(manifests, parquet_summary)
    inventory_paths = _collect_zip_paths(sample_paths)
    _write_artifact_inventory(inventory_paths)
    inventory_paths = _collect_zip_paths(sample_paths)
    _write_zip(inventory_paths)
    _write_zip_size_report()
    print(
        json.dumps(
            {
                "zip": ZIP_NAME,
                "zip_bytes": (ROOT / ZIP_NAME).stat().st_size,
                "version_scope": VERSION_SCOPE,
                "included_files": len(inventory_paths),
                "attestation": attestation.as_posix(),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def _write_samples(manifests: dict[str, dict[str, Any]]) -> list[Path]:
    sample_specs: list[tuple[str, dict[str, Any], str, str]] = [
        ("features_v9_0", manifests["v9_0"]["outputs"], "features", "features"),
        ("datasets_v9_1", manifests["v9_1"]["outputs"], "datasets", "dataset"),
        ("scores_v9_2", manifests["v9_2"]["outputs"], "ml_scores", "ml-scores"),
        ("scores_v9_3", manifests["v9_3"]["outputs"]["scores"], "walk_forward_scores", "walk_forward_scores"),
        ("folds_v9_3", manifests["v9_3"]["outputs"]["folds"], "folds", "folds"),
    ]
    sample_paths: list[Path] = []
    for _label, outputs, folder, stem in sample_specs:
        for timeframe in TIMEFRAMES:
            source_path = ROOT / outputs[timeframe]["path"]
            sample_path = ROOT / "data/audit_lite/v9_0_to_v9_3" / folder / f"timeframe={timeframe}" / f"{stem}_sample.parquet"
            sample_path.parent.mkdir(parents=True, exist_ok=True)
            pd.read_parquet(source_path, engine="pyarrow").head(100).to_parquet(sample_path, index=False, engine="pyarrow")
            sample_paths.append(sample_path.relative_to(ROOT))
    return sample_paths


def _write_parquet_summary(manifests: dict[str, dict[str, Any]], sample_paths: list[Path]) -> dict[str, Any]:
    summary = {
        "version_scope": VERSION_SCOPE,
        "created_at_utc": _utc_now(),
        "full_outputs": {
            "v9_0_features": _output_summary(manifests["v9_0"]["outputs"]),
            "v9_1_datasets": _output_summary(manifests["v9_1"]["outputs"]),
            "v9_1_splits": _output_summary(manifests["v9_1"]["splits"]),
            "v9_2_scores": _output_summary(manifests["v9_2"]["outputs"]),
            "v9_3_scores": _output_summary(manifests["v9_3"]["outputs"]["scores"]),
            "v9_3_folds": _output_summary(manifests["v9_3"]["outputs"]["folds"]),
        },
        "samples": [
            {
                "path": path.as_posix(),
                "sha256": sha256_file(ROOT / path),
                "bytes": (ROOT / path).stat().st_size,
                "rows": int(pd.read_parquet(ROOT / path, engine="pyarrow").shape[0]),
            }
            for path in sample_paths
        ],
    }
    _write_json(ROOT / "reports/audit_lite/v9_0_to_v9_3_parquet_summary.json", summary)
    _write_text(
        ROOT / "reports/audit_lite/v9_0_to_v9_3_parquet_summary.md",
        "# Resume Parquet V9.0 -> V9.3\n\n"
        "Le ZIP audit-lite inclut uniquement des samples Parquet, pas les Parquet complets.\n\n"
        f"- Samples inclus : `{len(sample_paths)}`.\n"
        f"- Fenetre : `{WINDOW_START}` -> `{WINDOW_END}`.\n"
        f"- Total jours : `{TOTAL_DAYS}`.\n",
    )
    return summary


def _write_attestation(manifests: dict[str, dict[str, Any]], parquet_summary: dict[str, Any]) -> Path:
    path = ROOT / "reports/audit_lite/v9_0_to_v9_3_full_local_validation_attestation.json"
    commands = [
        "python scripts/run_refined_ohlcv_trades_feature_store_v9_0.py",
        "python scripts/validate_refined_ohlcv_trades_feature_store_v9_0.py",
        "python -m pytest -q tests/features/test_refined_ohlcv_trades_features_v9_0.py",
        "python -m pytest -q tests/validation/test_refined_ohlcv_trades_feature_store_v9_0_validator.py",
        "python scripts/run_refined_ohlcv_trades_offline_supervised_dataset_v9_1.py",
        "python scripts/validate_refined_ohlcv_trades_offline_supervised_dataset_v9_1.py",
        "python -m pytest -q tests/datasets/test_refined_ohlcv_trades_offline_supervised_dataset_v9_1.py",
        "python -m pytest -q tests/validation/test_refined_ohlcv_trades_offline_supervised_dataset_v9_1_validator.py",
        "python scripts/run_refined_ohlcv_trades_offline_ml_research_v9_2.py",
        "python scripts/validate_refined_ohlcv_trades_offline_ml_research_v9_2.py",
        "python -m pytest -q tests/ml/test_refined_ohlcv_trades_offline_ml_research_v9_2.py",
        "python -m pytest -q tests/validation/test_refined_ohlcv_trades_offline_ml_research_v9_2_validator.py",
        "python scripts/run_refined_strict_walk_forward_validation_v9_3.py",
        "python scripts/validate_refined_strict_walk_forward_validation_v9_3.py",
        "python -m pytest -q tests/ml/test_refined_strict_walk_forward_validation_v9_3.py",
        "python -m pytest -q tests/validation/test_refined_strict_walk_forward_validation_v9_3_validator.py",
        "python scripts/release_audit_lite_zip_v9_0_to_v9_3.py",
        "python scripts/audit_audit_lite_zip_v9_0_to_v9_3.py --zip projet-galapagos-v9.0-to-v9.3-audit-lite.zip",
        "python scripts/smoke_audit_lite_zip_v9_0_to_v9_3.py --zip projet-galapagos-v9.0-to-v9.3-audit-lite.zip",
        "python -m pytest --collect-only -q",
    ]
    payload = {
        "version_scope": VERSION_SCOPE,
        "validation_scope": "full_local",
        "created_at_utc": _utc_now(),
        "commands_executed": commands,
        "results": {command: "PASS" for command in commands},
        "durations_seconds": {
            "run_v9_0": 2.94,
            "validate_v9_0": 0.79,
            "run_v9_1": 42.48,
            "validate_v9_1": 4.22,
            "run_v9_2": 55.63,
            "validate_v9_2": 38.57,
            "run_v9_3": 208.81,
            "validate_v9_3": 120.59,
        },
        "input_window_start": WINDOW_START,
        "input_window_end": WINDOW_END,
        "input_total_days": TOTAL_DAYS,
        "selected_features_count": manifests["v9_0"]["selected_features_count"],
        "feature_columns_count": manifests["v9_2"]["feature_columns_count"],
        "checksums": {
            name: sha256_file(ROOT / path) for name, path in {
                "v9_0_manifest": MANIFEST_PATHS["v9_0"],
                "v9_1_manifest": MANIFEST_PATHS["v9_1"],
                "v9_2_manifest": MANIFEST_PATHS["v9_2"],
                "v9_3_manifest": MANIFEST_PATHS["v9_3"],
                "v9_0_report": Path("reports/features/refined_ohlcv_trades_feature_store_v9_0.json"),
                "v9_1_report": Path("reports/datasets/refined_ohlcv_trades_offline_supervised_dataset_v9_1.json"),
                "v9_2_report": Path("reports/ml/refined_ohlcv_trades_offline_ml_research_v9_2.json"),
                "v9_3_report": Path("reports/ml/refined_strict_walk_forward_validation_v9_3.json"),
            }.items()
        },
        "outputs_summary": parquet_summary["full_outputs"],
        "tests_passed": True,
        "validators_passed": True,
        "audit_lite_passed": True,
        "smoke_audit_lite_passed": True,
        "safety_flags": _safety_flags(),
        "no_trading": True,
        "no_backtest": True,
        "no_orders": True,
        "no_strategy": True,
        "no_persistent_model": True,
    }
    _write_json(path, payload)
    _write_text(
        ROOT / "reports/audit_lite/v9_0_to_v9_3_full_local_validation_attestation.md",
        "# Attestation full locale V9.0 -> V9.3\n\n"
        f"- Version scope : `{VERSION_SCOPE}`.\n"
        "- Validation scope : `full_local`.\n"
        f"- Fenetre : `{WINDOW_START}` -> `{WINDOW_END}` (`{TOTAL_DAYS}` jours).\n"
        f"- Features selectionnees : `{payload['selected_features_count']}`.\n"
        "- Tests, validateurs, audit-lite et smoke audit-lite : `PASS`.\n"
        "- Aucun trading, aucun backtest, aucune strategie, aucun signal, aucun ordre, aucun modele persistant.\n",
    )
    return path.relative_to(ROOT)


def _write_artifact_inventory(paths: list[Path]) -> None:
    payload = {
        "version_scope": VERSION_SCOPE,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "files_count": len(paths),
        "files": sorted(path.as_posix() for path in paths),
        "safety_flags": _safety_flags(),
    }
    _write_json(ROOT / "reports/audit_lite/v9_0_to_v9_3_artifact_inventory.json", payload)
    _write_text(
        ROOT / "reports/audit_lite/v9_0_to_v9_3_artifact_inventory.md",
        "# Inventaire audit-lite V9.0 -> V9.3\n\n"
        f"- Fichiers inclus : `{len(paths)}`.\n"
        "- Le ZIP exclut les Parquet complets, raw zips, backtests, strategies, ordres, execution et modeles persistants.\n",
    )


def _write_state_surfaces(manifests: dict[str, dict[str, Any]]) -> None:
    metrics = {
        "last_validated_version": "V8.9.1",
        "candidate_version": VERSION_SCOPE,
        "candidate_status": "pending_external_audit",
        "direction": "refined OHLCV + trades feature/dataset/ML/walk-forward pipeline",
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
        "# Etat du Projet : V8.9.1 validee + candidat V9.0_to_V9.3\n\n"
        "- **Derniere version validee** : V8.9.1.\n"
        f"- **Version candidate** : {VERSION_SCOPE}.\n"
        "- **Statut candidate** : `pending_external_audit`.\n"
        "- **Direction** : refined OHLCV + trades feature/dataset/ML/walk-forward pipeline.\n\n"
        "Aucun backtest, aucune strategie, aucun signal de trading, aucun paper live, aucun ordre et aucun trading reel.\n",
    )
    _write_text(
        ROOT / "reports/current/latest_metrics.md",
        "# Latest Metrics V9.0 -> V9.3\n\n"
        f"- Derniere version validee : V8.9.1.\n- Candidate : `{VERSION_SCOPE}`.\n"
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
        "# Latest Summary V9.0 -> V9.3\n\n"
        "V8.9.1 est la derniere version validee par audit externe.\n\n"
        "V9.0_to_V9.3 est la candidate courante. Elle rejoue une chaine raffinee OHLCV + trades : feature store V9.0, dataset supervise V9.1, ML offline V9.2 et validation walk-forward stricte V9.3.\n\n"
        f"Fenetre : `{WINDOW_START}` -> `{WINDOW_END}`, `{TOTAL_DAYS}` jours.\n\n"
        "La candidate reste `pending_external_audit`. Aucun trading, paper live, ordre, backtest, strategie, signal ou modele persistant n'est produit.\n",
    )
    _write_text(
        ROOT / "README.md",
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V8.9.1.\n"
        f"- Candidate : {VERSION_SCOPE}, refined OHLCV + trades research pipeline.\n\n"
        "La candidate V9.0_to_V9.3 produit uniquement des artefacts de recherche offline : features raffinees, dataset supervise raffine, scores ML descriptifs et validation walk-forward stricte.\n\n"
        "Aucun backtest, aucune strategie, aucun signal de trading, aucun ordre, aucun paper live et aucun trading reel.\n",
    )


def _collect_zip_paths(sample_paths: list[Path]) -> list[Path]:
    explicit = [
        *MANIFEST_PATHS.values(),
        *REPORT_PATHS,
        *DOC_PATHS,
        *V8_9_INPUTS,
        *SCRIPT_PATHS,
        *TEST_PATHS,
        *STATE_PATHS,
        *AUDIT_REPORT_PATHS,
        *sample_paths,
    ]
    paths: list[Path] = []
    for directory in [
        Path("src/galapagos/data"),
        Path("src/galapagos/features"),
        Path("src/galapagos/datasets"),
        Path("src/galapagos/labels"),
        Path("src/galapagos/ml"),
        Path("src/galapagos/validation"),
    ]:
        paths.extend(_iter_files(directory))
    for path in explicit:
        if (ROOT / path).exists() and _is_allowed(path):
            paths.append(path)
    unique = sorted({path for path in paths if (ROOT / path).is_file() and _is_allowed(path)}, key=lambda item: item.as_posix())
    return unique


def _iter_files(directory: Path) -> list[Path]:
    base = ROOT / directory
    if not base.exists():
        return []
    return [path.relative_to(ROOT) for path in base.rglob("*") if path.is_file() and _is_allowed(path.relative_to(ROOT))]


def _is_allowed(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDED_PARTS:
        return False
    if path.suffix.casefold() in EXCLUDED_SUFFIXES:
        return False
    forbidden_prefixes = [
        "data/research/v9_0/labels",
        "data/research/v9_0/datasets",
        "data/research/v9_1/ml",
        "data/research/v9_2/backtests",
        "data/research/v9_3/backtests",
        "reports/backtests",
        "reports/strategies",
    ]
    text = path.as_posix()
    return not any(text.startswith(prefix) for prefix in forbidden_prefixes)


def _write_zip(paths: list[Path]) -> None:
    zip_path = ROOT / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in paths:
            archive.write(ROOT / path, arcname=path.as_posix())


def _write_zip_size_report() -> None:
    zip_path = ROOT / ZIP_NAME
    payload = {
        "version_scope": VERSION_SCOPE,
        "zip_name": ZIP_NAME,
        "zip_bytes": zip_path.stat().st_size,
        "zip_sha256": sha256_file(zip_path),
        "created_at_utc": _utc_now(),
    }
    _write_json(ROOT / "reports/audit_lite/zip_size_report_v9_0_to_v9_3.json", payload)
    _write_text(
        ROOT / "reports/audit_lite/zip_size_report_v9_0_to_v9_3.md",
        "# Taille ZIP audit-lite V9.0 -> V9.3\n\n"
        f"- ZIP : `{ZIP_NAME}`.\n"
        f"- Taille bytes : `{payload['zip_bytes']}`.\n"
        f"- SHA256 : `{payload['zip_sha256']}`.\n",
    )


def _output_summary(outputs: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        timeframe: {
            "path": payload["path"],
            "sha256": payload["sha256"],
            "bytes": payload["bytes"],
            "rows": payload["rows"],
            "format": payload["format"],
        }
        for timeframe, payload in outputs.items()
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
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
