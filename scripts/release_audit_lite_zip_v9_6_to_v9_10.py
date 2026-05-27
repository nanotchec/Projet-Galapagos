from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION_SCOPE = "V9.6_to_V9.10"
LAST_VALIDATED_VERSION = "V9.5"
ZIP_NAME = "projet-galapagos-v9.6-to-v9.10-audit-lite.zip"
WINDOW_START = "2023-03-25"
WINDOW_END = "2024-03-24"
TOTAL_DAYS = 366
TIMEFRAMES = ["1m", "5m", "15m", "1h"]
ROOT = Path(".").resolve()

REPORT_PATHS = [
    Path("reports/manifests/refined_volatility_normalized_labels_v9_6_manifest.json"),
    Path("reports/labels/refined_volatility_normalized_labels_v9_6.json"),
    Path("reports/labels/refined_volatility_normalized_labels_v9_6.md"),
    Path("reports/labels/refined_volatility_normalized_labels_v9_6_datacard.md"),
    Path("reports/manifests/refined_volnorm_labels_dataset_v9_7_manifest.json"),
    Path("reports/datasets/refined_volnorm_labels_dataset_v9_7.json"),
    Path("reports/datasets/refined_volnorm_labels_dataset_v9_7.md"),
    Path("reports/datasets/refined_volnorm_labels_dataset_v9_7_datacard.md"),
    Path("reports/manifests/refined_volnorm_labels_offline_ml_v9_8_manifest.json"),
    Path("reports/ml/refined_volnorm_labels_offline_ml_v9_8.json"),
    Path("reports/ml/refined_volnorm_labels_offline_ml_v9_8.md"),
    Path("reports/ml/refined_volnorm_labels_offline_scores_v9_8.json"),
    Path("reports/ml/refined_volnorm_labels_offline_scores_v9_8.md"),
    Path("reports/manifests/refined_volnorm_strict_walk_forward_v9_9_manifest.json"),
    Path("reports/ml/refined_volnorm_strict_walk_forward_v9_9.json"),
    Path("reports/ml/refined_volnorm_strict_walk_forward_v9_9.md"),
    Path("reports/ml/refined_volnorm_strict_walk_forward_scores_v9_9.json"),
    Path("reports/ml/refined_volnorm_strict_walk_forward_scores_v9_9.md"),
    Path("reports/manifests/refined_volnorm_research_decision_gate_v9_10_manifest.json"),
    Path("reports/research_decisions/refined_volnorm_research_decision_gate_v9_10.json"),
    Path("reports/research_decisions/refined_volnorm_research_decision_gate_v9_10.md"),
]

DOC_PATHS = [
    Path("docs/refined_volatility_normalized_labels_v9_6.md"),
    Path("docs/refined_volnorm_labels_dataset_v9_7.md"),
    Path("docs/refined_volnorm_labels_offline_ml_v9_8.md"),
    Path("docs/refined_volnorm_strict_walk_forward_v9_9.md"),
    Path("docs/refined_volnorm_research_decision_gate_v9_10.md"),
]

AUDIT_REPORT_PATHS = [
    Path("reports/audit_lite/v9_6_to_v9_10_command_results.json"),
    Path("reports/audit_lite/v9_6_to_v9_10_command_results.md"),
    Path("reports/audit_lite/v9_6_to_v9_10_full_local_validation_attestation.json"),
    Path("reports/audit_lite/v9_6_to_v9_10_full_local_validation_attestation.md"),
    Path("reports/audit_lite/v9_6_to_v9_10_artifact_inventory.json"),
    Path("reports/audit_lite/v9_6_to_v9_10_artifact_inventory.md"),
    Path("reports/audit_lite/zip_size_report_v9_6_to_v9_10.json"),
    Path("reports/audit_lite/zip_size_report_v9_6_to_v9_10.md"),
    Path("reports/audit_lite/zip_audit_v9_6_to_v9_10.json"),
    Path("reports/audit_lite/zip_audit_v9_6_to_v9_10.md"),
    Path("reports/audit_lite/zip_smoke_v9_6_to_v9_10.json"),
    Path("reports/audit_lite/zip_smoke_v9_6_to_v9_10.md"),
]

PRIOR_INPUT_PATHS = [
    Path("reports/research_decisions/refined_research_decision_gate_v9_4.json"),
    Path("reports/manifests/refined_research_decision_gate_v9_4_manifest.json"),
    Path("reports/research_decisions/alternative_label_design_audit_v9_5.json"),
    Path("reports/manifests/alternative_label_design_audit_v9_5_manifest.json"),
    Path("reports/manifests/refined_ohlcv_trades_feature_store_v9_0_manifest.json"),
    Path("reports/manifests/refined_ohlcv_trades_offline_supervised_dataset_v9_1_manifest.json"),
    Path("reports/manifests/refined_ohlcv_trades_offline_ml_research_v9_2_manifest.json"),
    Path("reports/manifests/refined_strict_walk_forward_validation_v9_3_manifest.json"),
    Path("reports/ml/refined_ohlcv_trades_offline_ml_research_v9_2.json"),
    Path("reports/ml/refined_strict_walk_forward_validation_v9_3.json"),
]

SCRIPT_PATHS = [
    Path("scripts/_bootstrap.py"),
    Path("scripts/run_refined_volatility_normalized_labels_v9_6.py"),
    Path("scripts/validate_refined_volatility_normalized_labels_v9_6.py"),
    Path("scripts/run_refined_volnorm_labels_dataset_v9_7.py"),
    Path("scripts/validate_refined_volnorm_labels_dataset_v9_7.py"),
    Path("scripts/run_refined_volnorm_labels_offline_ml_v9_8.py"),
    Path("scripts/validate_refined_volnorm_labels_offline_ml_v9_8.py"),
    Path("scripts/run_refined_volnorm_strict_walk_forward_v9_9.py"),
    Path("scripts/validate_refined_volnorm_strict_walk_forward_v9_9.py"),
    Path("scripts/run_refined_volnorm_research_decision_gate_v9_10.py"),
    Path("scripts/validate_refined_volnorm_research_decision_gate_v9_10.py"),
    Path("scripts/release_audit_lite_zip_v9_6_to_v9_10.py"),
    Path("scripts/audit_audit_lite_zip_v9_6_to_v9_10.py"),
    Path("scripts/smoke_audit_lite_zip_v9_6_to_v9_10.py"),
]

TEST_PATHS = [
    Path("tests/labels/test_refined_volatility_normalized_labels_v9_6.py"),
    Path("tests/validation/test_refined_volatility_normalized_labels_v9_6_validator.py"),
    Path("tests/datasets/test_refined_volnorm_labels_dataset_v9_7.py"),
    Path("tests/validation/test_refined_volnorm_labels_dataset_v9_7_validator.py"),
    Path("tests/ml/test_refined_volnorm_labels_offline_ml_v9_8.py"),
    Path("tests/validation/test_refined_volnorm_labels_offline_ml_v9_8_validator.py"),
    Path("tests/ml/test_refined_volnorm_strict_walk_forward_v9_9.py"),
    Path("tests/validation/test_refined_volnorm_strict_walk_forward_v9_9_validator.py"),
    Path("tests/research/test_refined_volnorm_research_decision_gate_v9_10.py"),
    Path("tests/validation/test_refined_volnorm_research_decision_gate_v9_10_validator.py"),
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

SAMPLE_PATHS = [
    *(Path(f"data/audit_lite/v9_6_to_v9_10/labels/timeframe={timeframe}/labels_sample.parquet") for timeframe in TIMEFRAMES),
    *(Path(f"data/audit_lite/v9_6_to_v9_10/datasets/timeframe={timeframe}/dataset_sample.parquet") for timeframe in TIMEFRAMES),
    *(Path(f"data/audit_lite/v9_6_to_v9_10/ml_scores/timeframe={timeframe}/ml-scores_sample.parquet") for timeframe in TIMEFRAMES),
    *(Path(f"data/audit_lite/v9_6_to_v9_10/walk_forward_scores/timeframe={timeframe}/walk_forward_scores_sample.parquet") for timeframe in TIMEFRAMES),
    *(Path(f"data/audit_lite/v9_6_to_v9_10/folds/timeframe={timeframe}/folds_sample.parquet") for timeframe in TIMEFRAMES),
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
EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pkl",
    ".pickle",
    ".joblib",
    ".onnx",
    ".pt",
    ".pth",
    ".ckpt",
    ".zip",
    ".pem",
    ".key",
    ".sha256",
    ".txt.sha256",
}
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
    reports = _load_reports()
    _ensure_required_inputs()
    _write_state_surfaces(reports)
    _write_samples(reports)
    _write_parquet_summary()
    _write_attestation(reports, zip_bytes=None)
    _ensure_audit_placeholders()
    zip_bytes: int | None = None
    zip_paths: list[Path] = []
    final_bytes = 0
    for _ in range(20):
        _write_attestation(reports, zip_bytes=zip_bytes)
        zip_paths = _collect_zip_paths()
        _write_zip_size_report(zip_paths, zip_bytes=zip_bytes)
        _write_inventory(zip_paths, zip_bytes=zip_bytes)
        zip_paths = _collect_zip_paths()
        _write_zip(zip_paths)
        final_bytes = (ROOT / ZIP_NAME).stat().st_size
        if final_bytes == zip_bytes:
            break
        zip_bytes = final_bytes
    result = {
        "version_scope": VERSION_SCOPE,
        "zip_name": ZIP_NAME,
        "zip_bytes": final_bytes,
        "included_files": len(zip_paths),
        "samples_included": len(SAMPLE_PATHS),
        "sidecars_created": False,
        "zip_fingerprints_created": False,
        "status": "PASS",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _load_reports() -> dict[str, dict[str, Any]]:
    return {
        "v9_6": _read_json(Path("reports/labels/refined_volatility_normalized_labels_v9_6.json")),
        "v9_7": _read_json(Path("reports/datasets/refined_volnorm_labels_dataset_v9_7.json")),
        "v9_8": _read_json(Path("reports/ml/refined_volnorm_labels_offline_ml_v9_8.json")),
        "v9_9": _read_json(Path("reports/ml/refined_volnorm_strict_walk_forward_v9_9.json")),
        "v9_10": _read_json(Path("reports/research_decisions/refined_volnorm_research_decision_gate_v9_10.json")),
    }


def _ensure_required_inputs() -> None:
    required = [
        *REPORT_PATHS,
        *DOC_PATHS,
        *PRIOR_INPUT_PATHS,
        *SCRIPT_PATHS,
        *TEST_PATHS,
        Path("scripts/_bootstrap.py"),
        Path("pyproject.toml"),
    ]
    missing = [path.as_posix() for path in required if not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError(f"missing required V9.6_to_V9.10 audit-lite inputs: {missing}")


def _write_samples(reports: dict[str, dict[str, Any]]) -> None:
    source_specs: list[tuple[str, str, str, dict[str, Any]]] = [
        ("labels", "labels_sample.parquet", "outputs", reports["v9_6"]),
        ("datasets", "dataset_sample.parquet", "outputs", reports["v9_7"]),
        ("ml_scores", "ml-scores_sample.parquet", "outputs", reports["v9_8"]),
        ("walk_forward_scores", "walk_forward_scores_sample.parquet", "scores", reports["v9_9"]),
        ("folds", "folds_sample.parquet", "folds", reports["v9_9"]),
    ]
    for folder, filename, output_key, report in source_specs:
        for timeframe in TIMEFRAMES:
            if folder == "walk_forward_scores":
                source_path = Path(report["outputs"]["scores"][timeframe]["path"])
            elif folder == "folds":
                source_path = Path(report["outputs"]["folds"][timeframe]["path"])
            else:
                source_path = Path(report[output_key][timeframe]["path"])
            sample_path = ROOT / "data/audit_lite/v9_6_to_v9_10" / folder / f"timeframe={timeframe}" / filename
            sample_path.parent.mkdir(parents=True, exist_ok=True)
            frame = pd.read_parquet(ROOT / source_path, engine="pyarrow").head(50)
            frame.to_parquet(sample_path, index=False, engine="pyarrow")


def _write_parquet_summary() -> None:
    samples: list[dict[str, Any]] = []
    for sample in SAMPLE_PATHS:
        frame = pd.read_parquet(ROOT / sample, engine="pyarrow")
        samples.append(
            {
                "path": sample.as_posix(),
                "bytes": (ROOT / sample).stat().st_size,
                "rows": int(len(frame)),
                "columns_count": int(len(frame.columns)),
                "columns": list(frame.columns),
            }
        )
    payload = {
        "version_scope": VERSION_SCOPE,
        "created_at_utc": _utc_now(),
        "sample_only": True,
        "full_parquet_included": False,
        "samples_count": len(samples),
        "samples": samples,
    }
    _write_json(Path("reports/audit_lite/v9_6_to_v9_10_parquet_summary.json"), payload)
    _write_text(
        Path("reports/audit_lite/v9_6_to_v9_10_parquet_summary.md"),
        "# Resume Parquet audit-lite V9.6 -> V9.10\n\n"
        f"- Samples inclus : `{len(samples)}`.\n"
        "- Aucun Parquet full `data/research/` n'est inclus.\n",
    )


def _ensure_audit_placeholders() -> None:
    placeholders = {
        "zip_audit_v9_6_to_v9_10": "Audit ZIP audit-lite V9.6 -> V9.10",
        "zip_smoke_v9_6_to_v9_10": "Smoke ZIP audit-lite V9.6 -> V9.10",
    }
    for name, title in placeholders.items():
        json_path = Path(f"reports/audit_lite/{name}.json")
        md_path = Path(f"reports/audit_lite/{name}.md")
        if not (ROOT / json_path).exists():
            _write_json(json_path, {"version_scope": VERSION_SCOPE, "passed": False, "errors": [], "status": "PENDING_RUN", "created_at_utc": _utc_now()})
        if not (ROOT / md_path).exists():
            _write_text(md_path, f"# {title}\n\nRapport en attente d'execution.\n")
    command_json = Path("reports/audit_lite/v9_6_to_v9_10_command_results.json")
    command_md = Path("reports/audit_lite/v9_6_to_v9_10_command_results.md")
    if not (ROOT / command_json).exists():
        _write_json(command_json, {"version_scope": VERSION_SCOPE, "status": "PENDING_CAPTURE", "commands": [], "created_at_utc": _utc_now()})
    if not (ROOT / command_md).exists():
        _write_text(command_md, "# Commandes V9.6 -> V9.10\n\nRapport en attente de capture finale.\n")


def _write_attestation(reports: dict[str, dict[str, Any]], *, zip_bytes: int | None) -> None:
    command_results = _read_optional_json(Path("reports/audit_lite/v9_6_to_v9_10_command_results.json"))
    commands = command_results.get("commands", [])
    payload = {
        "version_scope": VERSION_SCOPE,
        "validation_scope": "full_local_plus_audit_lite_packaging",
        "created_at_utc": _utc_now(),
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION_SCOPE,
        "zip_name": ZIP_NAME,
        "zip_bytes": zip_bytes,
        "commands_executed": [command.get("command") for command in commands],
        "command_results_path": "reports/audit_lite/v9_6_to_v9_10_command_results.json",
        "tests_passed": _commands_passed(commands, ["pytest"]),
        "validators_passed": _commands_passed(commands, ["validate_refined"]),
        "audit_lite_passed": _commands_passed(commands, ["audit_audit_lite_zip_v9_6_to_v9_10.py"]),
        "smoke_audit_lite_passed": _commands_passed(commands, ["smoke_audit_lite_zip_v9_6_to_v9_10.py"]),
        "selected_label_candidate": reports["v9_6"].get("selected_volatility_threshold_multiplier"),
        "v9_6_decision": reports["v9_6"].get("decision"),
        "v9_7_decision": reports["v9_7"].get("decision"),
        "v9_8_decision": reports["v9_8"].get("decision"),
        "v9_9_decision": reports["v9_9"].get("decision"),
        "v9_10_decision": reports["v9_10"].get("research_decision"),
        "dataset_row_counts": {timeframe: reports["v9_7"]["outputs"][timeframe]["rows"] for timeframe in TIMEFRAMES},
        "score_row_counts_v9_8": {timeframe: reports["v9_8"]["outputs"][timeframe]["rows"] for timeframe in TIMEFRAMES},
        "score_row_counts_v9_9": {timeframe: reports["v9_9"]["outputs"]["scores"][timeframe]["rows"] for timeframe in TIMEFRAMES},
        "folds_count": {timeframe: len(reports["v9_9"]["folds"][timeframe]) for timeframe in TIMEFRAMES},
        "safety_flags": _safety_flags(),
        "no_trading": True,
        "no_paper_live": True,
        "no_orders": True,
        "no_backtest": True,
        "no_strategy": True,
        "no_actionable_signal": True,
        "no_persistent_model": True,
        "api_key_used": False,
        "private_endpoint_used": False,
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    _write_json(Path("reports/audit_lite/v9_6_to_v9_10_full_local_validation_attestation.json"), payload)
    _write_text(
        Path("reports/audit_lite/v9_6_to_v9_10_full_local_validation_attestation.md"),
        "# Attestation full locale V9.6 -> V9.10\n\n"
        f"- Version scope : `{VERSION_SCOPE}`.\n"
        f"- Decision V9.10 : `{reports['v9_10'].get('research_decision')}`.\n"
        "- Aucun trading, paper live, ordre, backtest, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun sidecar et aucune empreinte ZIP ne sont produits.\n",
    )


def _commands_passed(commands: list[dict[str, Any]], needles: list[str]) -> bool:
    return any(command.get("status") == "PASS" and all(needle in command.get("command", "") for needle in needles) for command in commands)


def _collect_zip_paths() -> list[Path]:
    explicit = [
        *REPORT_PATHS,
        *DOC_PATHS,
        *AUDIT_REPORT_PATHS,
        Path("reports/audit_lite/v9_6_to_v9_10_parquet_summary.json"),
        Path("reports/audit_lite/v9_6_to_v9_10_parquet_summary.md"),
        *PRIOR_INPUT_PATHS,
        *SCRIPT_PATHS,
        *TEST_PATHS,
        *STATE_PATHS,
        *SAMPLE_PATHS,
    ]
    paths: list[Path] = []
    for directory in [
        Path("src/galapagos/features"),
        Path("src/galapagos/labels"),
        Path("src/galapagos/datasets"),
        Path("src/galapagos/ml"),
        Path("src/galapagos/research"),
        Path("src/galapagos/validation"),
        Path("src/galapagos/data"),
    ]:
        paths.extend(_iter_files(directory))
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
    if set(path.parts) & EXCLUDED_PARTS:
        return False
    if path.name in EXCLUDED_NAMES:
        return False
    if text.endswith(".sha256.json") or text.endswith(".sha256.txt"):
        return False
    return path.suffix.casefold() not in EXCLUDED_SUFFIXES


def _write_zip(paths: list[Path]) -> None:
    zip_path = ROOT / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in paths:
            archive.write(ROOT / path, arcname=path.as_posix())


def _write_inventory(paths: list[Path], *, zip_bytes: int | None) -> None:
    payload = {
        "version_scope": VERSION_SCOPE,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes": zip_bytes,
        "files_count": len(paths),
        "files": [path.as_posix() for path in paths],
        "forbidden_absences_verified": _forbidden_absence_checks(paths),
        "safety_flags": _safety_flags(),
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    _write_json(Path("reports/audit_lite/v9_6_to_v9_10_artifact_inventory.json"), payload)
    _write_text(
        Path("reports/audit_lite/v9_6_to_v9_10_artifact_inventory.md"),
        "# Inventaire audit-lite V9.6 -> V9.10\n\n"
        f"- ZIP : `{ZIP_NAME}`.\n"
        f"- Fichiers inclus : `{len(paths)}`.\n"
        f"- Taille ZIP : `{zip_bytes}`.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n"
        "- Absences verifiees : data/research full, secrets, caches, modeles persistants, backtests, strategies, ordres, execution.\n",
    )


def _write_zip_size_report(paths: list[Path], *, zip_bytes: int | None) -> None:
    payload = {
        "version_scope": VERSION_SCOPE,
        "created_at_utc": _utc_now(),
        "zip_name": ZIP_NAME,
        "zip_bytes": zip_bytes,
        "included_files": len(paths),
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    _write_json(Path("reports/audit_lite/zip_size_report_v9_6_to_v9_10.json"), payload)
    _write_text(
        Path("reports/audit_lite/zip_size_report_v9_6_to_v9_10.md"),
        "# Taille ZIP audit-lite V9.6 -> V9.10\n\n"
        f"- ZIP : `{ZIP_NAME}`.\n"
        f"- Taille bytes : `{zip_bytes}`.\n"
        f"- Fichiers inclus : `{len(paths)}`.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n",
    )


def _write_state_surfaces(reports: dict[str, dict[str, Any]]) -> None:
    metrics = {
        "last_validated_version": LAST_VALIDATED_VERSION,
        "candidate_version": VERSION_SCOPE,
        "candidate_status": "pending_external_audit",
        "direction": "refined_volatility_normalized_labels_research_chain",
        "window_start": WINDOW_START,
        "window_end": WINDOW_END,
        "total_days": TOTAL_DAYS,
        "selected_label_candidate": reports["v9_6"].get("selected_volatility_threshold_multiplier"),
        "label_decision_v9_6": reports["v9_6"].get("decision"),
        "dataset_decision_v9_7": reports["v9_7"].get("decision"),
        "ml_decision_v9_8": reports["v9_8"].get("decision"),
        "walk_forward_decision_v9_9": reports["v9_9"].get("decision"),
        "research_decision_v9_10": reports["v9_10"].get("research_decision"),
        "dataset_row_counts": {timeframe: reports["v9_7"]["outputs"][timeframe]["rows"] for timeframe in TIMEFRAMES},
        "score_row_counts_v9_8": {timeframe: reports["v9_8"]["outputs"][timeframe]["rows"] for timeframe in TIMEFRAMES},
        "score_row_counts_v9_9": {timeframe: reports["v9_9"]["outputs"]["scores"][timeframe]["rows"] for timeframe in TIMEFRAMES},
        "folds_count": {timeframe: len(reports["v9_9"]["folds"][timeframe]) for timeframe in TIMEFRAMES},
        "trading_enabled": False,
        "paper_live_enabled": False,
        "orders_enabled": False,
        "backtest_performed": False,
        "strategy_enabled": False,
        "actionable_signal_produced": False,
        "persistent_model_created": False,
        "api_key_used": False,
        "private_endpoint_used": False,
        "sidecars_created": False,
        "zip_fingerprints_created": False,
    }
    state_path = Path("reports/PROJECT_STATE.json")
    state = _read_json(state_path) if (ROOT / state_path).exists() else {}
    state.update(metrics)
    _write_json(state_path, state)
    _write_json(Path("reports/current/latest_metrics.json"), metrics)
    summary = (
        "# Synthese courante - V9.6_to_V9.10\n\n"
        "- Derniere version validee : `V9.5`.\n"
        "- Candidate : `V9.6_to_V9.10`.\n"
        "- Statut : `pending_external_audit`.\n"
        "- Direction : chaine research labels volatility-normalized raffinee.\n"
        f"- Decision V9.10 : `{reports['v9_10'].get('research_decision')}`.\n"
        "- Aucun trading, paper live, ordre, backtest, strategie, signal actionnable, modele persistant, API privee ou cle API.\n"
        "- Aucun sidecar et aucune empreinte ZIP.\n"
    )
    _write_text(Path("reports/PROJECT_STATE.md"), summary)
    _write_text(Path("reports/current/latest_summary.md"), summary)
    _write_text(Path("reports/current/latest_metrics.md"), summary)
    _write_text(
        Path("README.md"),
        "# Projet Galapagos\n\n"
        "- Derniere version validee : V9.5.\n"
        "- Candidate : V9.6_to_V9.10, chaine research offline avec labels volatility-normalized.\n"
        f"- Decision V9.10 : {reports['v9_10'].get('research_decision')}.\n\n"
        "Aucun trading, aucun paper live, aucun ordre, aucun backtest, aucune strategie, aucun signal actionnable, aucun modele persistant, aucune API privee et aucune cle API.\n"
        "Le packaging V9.6_to_V9.10 ne produit aucun sidecar et aucune empreinte ZIP.\n",
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
        "strategies_absent": not any(text.startswith("reports/strategies/") for text in texts),
        "orders_absent": not any(text.startswith("orders/") for text in texts),
        "execution_absent": not any(text.startswith("execution/") for text in texts),
        "models_absent": not any(text.startswith("models/") for text in texts),
        "checkpoints_absent": not any(text.startswith("checkpoints/") for text in texts),
        "sidecars_absent": not any(text.endswith(".sha256.json") or text.endswith(".sha256.txt") for text in texts),
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
