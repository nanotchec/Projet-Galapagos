from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


VERSION_SCOPE = "V9.6_to_V9.10"
TIMEFRAMES = ["1m", "5m", "15m", "1h"]
FORBIDDEN_SAMPLE_COLUMNS = {
    "prediction",
    "model_score",
    "signal",
    "trading_signal",
    "order",
    "pnl",
    "sharpe",
    "drawdown",
    "equity_curve",
    "profit_factor",
    "backtest",
    "position_size",
    "strategy",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    args = parser.parse_args()
    result = smoke_zip(Path(args.zip_path).resolve())
    _write_reports(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


def smoke_zip(zip_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="galapagos_v9_6_to_v9_10_smoke_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(zip_path) as archive:
            names = archive.namelist()
            archive.extractall(extract_root)
        if any(name.endswith(".sha256.json") or name.endswith(".sha256.txt") for name in names):
            errors.append("ZIP must not contain sidecar or fingerprint files")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(extract_root / "src")
        sys.path.insert(0, str(extract_root / "src"))
        try:
            errors.extend(_import_required_modules(extract_root, env))
            errors.extend(_check_reports(extract_root))
            errors.extend(_check_sample_schemas(extract_root))
        finally:
            if str(extract_root / "src") in sys.path:
                sys.path.remove(str(extract_root / "src"))
        collect = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q"],
            cwd=extract_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if collect.returncode != 0:
            errors.append(f"pytest collect-only failed: {collect.stdout[-1200:]} {collect.stderr[-1200:]}")
    return {
        "version_scope": VERSION_SCOPE,
        "zip": str(zip_path),
        "passed": not errors,
        "errors": errors,
        "tests_inspectable_included": True,
        "full_tests_executed_in_smoke": False,
        "full_tests_note": "Les tests full V9.6-V9.10 sont inclus pour inspection; le smoke audit-lite sample-only execute collect-only et les controles de samples.",
        "sample_only_checks_executed": True,
        "sidecars_expected": False,
        "zip_fingerprints_expected": False,
    }


def _import_required_modules(extract_root: Path, env: dict[str, str]) -> list[str]:
    errors: list[str] = []
    modules = [
        "galapagos.labels.refined_volatility_normalized_labels_v9_6",
        "galapagos.labels.refined_volatility_normalized_labels_v9_6_validation",
        "galapagos.datasets.refined_volnorm_labels_dataset_v9_7",
        "galapagos.datasets.refined_volnorm_labels_dataset_v9_7_validation",
        "galapagos.ml.refined_volnorm_labels_offline_ml_v9_8",
        "galapagos.ml.refined_volnorm_labels_offline_ml_v9_8_validation",
        "galapagos.ml.refined_volnorm_strict_walk_forward_v9_9",
        "galapagos.ml.refined_volnorm_strict_walk_forward_v9_9_validation",
        "galapagos.research.refined_volnorm_research_decision_gate_v9_10",
        "galapagos.research.refined_volnorm_research_decision_gate_v9_10_validation",
    ]
    for module in modules:
        completed = subprocess.run(
            ["python", "-c", f"import {module}"],
            cwd=extract_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            errors.append(f"import failed for {module}: {completed.stderr.strip()}")
    return errors


def _check_reports(extract_root: Path) -> list[str]:
    errors: list[str] = []
    v96 = _read_json(extract_root / "reports/labels/refined_volatility_normalized_labels_v9_6.json")
    v910 = _read_json(extract_root / "reports/research_decisions/refined_volnorm_research_decision_gate_v9_10.json")
    inventory = _read_json(extract_root / "reports/audit_lite/v9_6_to_v9_10_artifact_inventory.json")
    attestation = _read_json(extract_root / "reports/audit_lite/v9_6_to_v9_10_full_local_validation_attestation.json")
    if inventory.get("version_scope") != VERSION_SCOPE:
        errors.append("inventory version_scope mismatch")
    if attestation.get("version_scope") != VERSION_SCOPE:
        errors.append("attestation version_scope mismatch")
    if v96.get("selected_volatility_threshold_multiplier") != 0.5:
        errors.append("V9.6 selected multiplier mismatch")
    if v910.get("research_decision") != "backtest_not_justified_refine_labels_again":
        errors.append("V9.10 decision mismatch")
    for key in ["robust_edge_claimed", "strategy_validated", "backtest_performed", "actionable_signal_produced", "walk_forward_validated_for_trading"]:
        if v910.get("findings", {}).get(key) is not False:
            errors.append(f"V9.10 finding must be false: {key}")
    for key in ["no_trading", "no_backtest", "no_orders", "no_strategy", "no_actionable_signal", "no_persistent_model"]:
        if attestation.get(key) is not True:
            errors.append(f"attestation must confirm {key}=true")
    for key in ["api_key_used", "private_endpoint_used", "sidecars_created", "zip_fingerprints_created"]:
        if attestation.get(key) is not False:
            errors.append(f"attestation must confirm {key}=false")
    return errors


def _check_sample_schemas(extract_root: Path) -> list[str]:
    from galapagos.datasets.refined_volnorm_labels_dataset_v9_7_schemas import DATASET_COLUMNS_V9_7
    from galapagos.labels.refined_volatility_normalized_labels_v9_6_schemas import REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6
    from galapagos.ml.refined_volnorm_labels_offline_ml_v9_8 import ML_SCORE_COLUMNS_V9_8
    from galapagos.ml.refined_volnorm_strict_walk_forward_v9_9 import ML_SCORE_COLUMNS_V9_9, WALK_FORWARD_FOLD_COLUMNS_V9_9

    errors: list[str] = []
    sample_specs = [
        ("labels", "labels_sample.parquet", REFINED_VOLATILITY_NORMALIZED_LABEL_COLUMNS_V9_6),
        ("datasets", "dataset_sample.parquet", DATASET_COLUMNS_V9_7),
        ("ml_scores", "ml-scores_sample.parquet", ML_SCORE_COLUMNS_V9_8),
        ("walk_forward_scores", "walk_forward_scores_sample.parquet", ML_SCORE_COLUMNS_V9_9),
        ("folds", "folds_sample.parquet", WALK_FORWARD_FOLD_COLUMNS_V9_9),
    ]
    for folder, filename, expected_columns in sample_specs:
        for timeframe in TIMEFRAMES:
            path = extract_root / "data/audit_lite/v9_6_to_v9_10" / folder / f"timeframe={timeframe}" / filename
            if not path.exists():
                errors.append(f"missing sample: {path.relative_to(extract_root).as_posix()}")
                continue
            frame = pd.read_parquet(path, engine="pyarrow")
            if frame.empty:
                errors.append(f"empty sample: {path.relative_to(extract_root).as_posix()}")
            if list(frame.columns) != expected_columns:
                errors.append(f"schema mismatch for {path.relative_to(extract_root).as_posix()}")
            forbidden = sorted(set(frame.columns) & FORBIDDEN_SAMPLE_COLUMNS)
            if forbidden:
                errors.append(f"forbidden columns in {path.relative_to(extract_root).as_posix()}: {forbidden}")
    return errors


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_reports(result: dict[str, Any]) -> None:
    report_dir = Path("reports/audit_lite")
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "zip_smoke_v9_6_to_v9_10.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (report_dir / "zip_smoke_v9_6_to_v9_10.md").write_text(
        "# Smoke audit-lite V9.6 -> V9.10\n\n"
        f"- Resultat : `{'PASS' if result['passed'] else 'FAIL'}`.\n"
        f"- Erreurs : `{result['errors']}`.\n"
        "- Smoke sample-only : `oui`.\n"
        "- Tests full executes dans le ZIP : `non`; ils sont inclus pour inspection.\n"
        "- Sidecars/empreintes ZIP attendus : `non`.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
