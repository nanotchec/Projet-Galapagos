from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.ml.calibration import calibration_analysis
from galapagos.research.ml.dataset import load_ml_dataset
from galapagos.research.ml.feature_importance import extract_feature_importance
from galapagos.research.ml.feature_sets import (
    FEATURE_SETS,
    extract_features,
    get_feature_set,
)
from galapagos.research.ml.models import (
    MODEL_REGISTRY,
    SKLEARN_AVAILABLE,
    create_model,
)
from galapagos.research.ml.report import build_ml_summary
from galapagos.research.ml.walk_forward import (
    build_default_windows,
    run_walk_forward,
)
from galapagos.research.report_models import write_research_report
from galapagos.utils.config_loader import load_yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--version", default="v1.15.1")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = run_ml_lab(
        dataset_path=args.dataset,
        config_path=args.config,
        version_str=args.version,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


def run_ml_lab(
    *, dataset_path: str, config_path: str, version_str: str = "v1.15.1", dry_run: bool = False,
) -> dict:
    config = load_yaml(config_path)
    cost_threshold = float(config.get("cost_threshold", 0.003))

    if dry_run:
        dataset_exists = Path(dataset_path).exists()
        return {
            "version": version_str.upper(),
            "dry_run": True,
            "status": "dry_run_completed",
            "sklearn_available": SKLEARN_AVAILABLE,
            "dataset_path": dataset_path,
            "dataset_exists": dataset_exists,
            "config_path": config_path,
            "models_available": sorted(MODEL_REGISTRY.keys()),
            "feature_sets_available": sorted(FEATURE_SETS.keys()),
            "holdout_executed": False,
            "codex_cli_called": False,
            "real_orders_possible": False,
        }

    dataset, ds_report = load_ml_dataset(dataset_path, cost_threshold=cost_threshold)
    if dataset is None:
        return {
            "version": version_str.upper(),
            "status": "missing_dataset",
            "dataset_report": ds_report,
            "holdout_executed": False,
            "codex_cli_called": False,
        }

    targets = config.get("targets", {}).get("classification", [])
    feature_set_names = config.get("feature_sets", ["ohlcv_basic"])
    model_names = config.get("models", {}).get("classification", [])
    embargo = config.get("walk_forward", {}).get("embargo_bars", 6)
    min_train = config.get("walk_forward", {}).get("min_train_rows", 200)
    min_test = config.get("walk_forward", {}).get("min_test_rows", 50)

    # Filter models to available ones
    model_names = [m for m in model_names if m in MODEL_REGISTRY]
    if not model_names:
        model_names = list(MODEL_REGISTRY.keys())[:1]

    all_results = []
    importance_results = []
    calibration_results = []

    for target in targets:
        for fs_name in feature_set_names:
            for model_name in model_names:
                result = run_walk_forward(
                    dataset,
                    target_col=target,
                    feature_set_name=fs_name,
                    model_name=model_name,
                    embargo_bars=embargo,
                    min_train_rows=min_train,
                    min_test_rows=min_test,
                )
                all_results.append(result)

                # Feature importance on last window
                if result.get("status") == "completed":
                    feat_cols, _ = get_feature_set(dataset, fs_name)
                    if feat_cols:
                        windows = build_default_windows(len(dataset), embargo)
                        if windows:
                            last_w = windows[-1]
                            train = dataset.iloc[last_w.train_start:last_w.train_end]
                            mask = train[target].notna()
                            x_t = extract_features(train[mask], feat_cols).values
                            y_t = train.loc[mask, target].values.astype(float)
                            if len(x_t) >= min_train:
                                m = create_model(model_name)
                                try:
                                    m.fit(x_t, y_t)
                                    imp = extract_feature_importance(m, feat_cols)
                                    imp["target"] = target
                                    imp["model"] = model_name
                                    imp["feature_set"] = fs_name
                                    importance_results.append(imp)
                                except Exception:  # noqa: BLE001
                                    pass

                                # Calibration on test
                                test = dataset.iloc[last_w.test_start:last_w.test_end]
                                tmask = test[target].notna()
                                x_te = extract_features(test[tmask], feat_cols).values
                                y_te = test.loc[tmask, target].values.astype(float)
                                if len(x_te) >= min_test and hasattr(m, "predict_proba"):
                                    try:
                                        proba = m.predict_proba(x_te)
                                        if proba.shape[1] == 2:
                                            cal = calibration_analysis(y_te, proba[:, 1])
                                            cal["target"] = target
                                            cal["model"] = model_name
                                            calibration_results.append(cal)
                                    except Exception:  # noqa: BLE001
                                        pass

    summary = build_ml_summary(
        all_results, sklearn_available=SKLEARN_AVAILABLE, dataset_report=ds_report,
    )
    
    version_suffix = version_str.lower().replace(".", "_")
    summary["version"] = version_str.upper()
    
    summary["experiments"] = all_results
    summary["feature_importance"] = importance_results
    summary["calibration"] = calibration_results

    # Write reports
    write_research_report(
        name=f"ml_baseline_{version_suffix}", payload=summary,
        title=f"ML Baseline Lab {version_str}",
        lines=[
            f"sklearn: {SKLEARN_AVAILABLE}.",
            f"Dataset: {ds_report.get('rows')} lignes.",
            f"Verdict: {summary['verdict']}.",
            f"Best: {summary.get('best_result', {}).get('key', 'none')}.",
            "Holdout non execute, Codex CLI non appele, aucun ordre reel.",
        ],
    )
    if importance_results:
        write_research_report(
            name=f"ml_feature_importance_{version_suffix}",
            payload={"results": importance_results},
            title=f"ML Feature Importance {version_str}",
            lines=["Feature importance par modele et feature set."],
        )
    if calibration_results:
        write_research_report(
            name=f"ml_calibration_{version_suffix}",
            payload={"results": calibration_results},
            title=f"ML Calibration {version_str}",
            lines=["Calibration des probabilites par modele."],
        )
    write_research_report(
        name=f"ml_walk_forward_{version_suffix}",
        payload={"windows": [r for r in all_results if r.get("windows")]},
        title=f"ML Walk-Forward {version_str}",
        lines=["Resultats walk-forward par fenetre."],
    )
    return summary


if __name__ == "__main__":
    main()
