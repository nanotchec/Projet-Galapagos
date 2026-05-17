from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from _bootstrap import bootstrap_src_path

bootstrap_src_path()

from galapagos.research.ml.dataset import load_ml_dataset
from galapagos.research.ml.feature_sets import extract_features, get_feature_set
from galapagos.research.ml.models import MODEL_REGISTRY, create_model
from galapagos.research.ml.walk_forward import (
    build_date_based_walk_forward_splits,
    build_default_windows,
)
from galapagos.research.report_models import write_research_report
from galapagos.utils.config_loader import load_yaml
from galapagos.utils.version import normalize_version


def main() -> None:
    parser = argparse.ArgumentParser(description="Export ML predictions for ensemble analysis")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--version", default="v1.16")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    v_norm = normalize_version(args.version)
    
    if args.dry_run:
        print(f"DRY RUN: Exporting ML predictions for {args.dataset} using {args.config}")
        return

    config = load_yaml(args.config)
    cost_threshold = float(config.get("cost_threshold", 0.003))
    
    dataset, ds_report = load_ml_dataset(args.dataset, cost_threshold=cost_threshold)
    if dataset is None:
        print(f"Error loading dataset: {ds_report}")
        return

    targets = config.get("targets", {}).get("classification", [])
    feature_set_names = config.get("feature_sets", ["ohlcv_basic"])
    model_names = config.get("models", {}).get("classification", [])
    embargo = config.get("walk_forward", {}).get("embargo_bars", 6)

    if config.get("walk_forward", {}).get("method") == "date_based":
        windows = build_date_based_walk_forward_splits(dataset, config)
    else:
        windows = build_default_windows(len(dataset), embargo)

    all_predictions = []
    
    for target in targets:
        for fs_name in feature_set_names:
            feature_cols, _ = get_feature_set(dataset, fs_name)
            if not feature_cols:
                continue
                
            for model_name in model_names:
                if model_name not in MODEL_REGISTRY:
                    continue
                
                supports_proba = MODEL_REGISTRY[model_name].get("supports_proba", False)
                
                for window in windows:
                    print(f"Processing {target} / {fs_name} / {model_name} / {window.name}...")
                    train_slice = dataset.iloc[window.train_start:window.train_end]
                    test_slice = dataset.iloc[window.test_start:window.test_end]
                    
                    train_mask = train_slice[target].notna()
                    test_mask = test_slice[target].notna()
                    
                    if not train_mask.any() or not test_mask.any():
                        continue
                        
                    x_train = extract_features(train_slice[train_mask], feature_cols).values
                    y_train = train_slice.loc[train_mask, target].values.astype(float)
                    x_test = extract_features(test_slice[test_mask], feature_cols).values
                    y_test = test_slice.loc[test_mask, target].values.astype(float)
                    ts_test = dataset.loc[test_slice.index[test_mask], "timestamp"].values
                    
                    # Forward returns if available
                    ret_cols = ["forward_return_6bar", "forward_return_12bar", "cost_adjusted_forward_return"]
                    forward_returns = {}
                    for rc in ret_cols:
                        if rc in dataset.columns:
                            forward_returns[rc] = dataset.loc[test_slice.index[test_mask], rc].values
                        else:
                            forward_returns[rc] = [None] * len(ts_test)

                    model = create_model(model_name)
                    model.fit(x_train, y_train)
                    
                    y_pred = model.predict(x_test)
                    y_proba = [None] * len(y_pred)
                    if supports_proba and hasattr(model, "predict_proba"):
                        proba = model.predict_proba(x_test)
                        y_proba = proba[:, 1] if proba.shape[1] == 2 else [None] * len(y_pred)
                        
                    for i in range(len(ts_test)):
                        all_predictions.append({
                            "timestamp": ts_test[i],
                            "model_name": model_name,
                            "feature_set": fs_name,
                            "target": target,
                            "split_name": f"test_{window.name}",
                            "predicted_probability": float(y_proba[i]) if y_proba[i] is not None else None,
                            "predicted_label": int(y_pred[i]),
                            "actual_target": int(y_test[i]),
                            "forward_return_6bar": float(forward_returns["forward_return_6bar"][i]) if forward_returns["forward_return_6bar"][i] is not None else None,
                            "forward_return_12bar": float(forward_returns["forward_return_12bar"][i]) if forward_returns["forward_return_12bar"][i] is not None else None,
                            "cost_adjusted_forward_return": float(forward_returns["cost_adjusted_forward_return"][i]) if forward_returns["cost_adjusted_forward_return"][i] is not None else None,
                        })

    if not all_predictions:
        print("No predictions generated.")
        return

    df_preds = pd.DataFrame(all_predictions)
    output_dir = Path("data/gold/ml_predictions/BTC/4h")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / f"ml_predictions_{v_norm}.parquet"
    df_preds.to_parquet(output_path)
    
    report_payload = {
        "version": v_norm.upper(),
        "prediction_count": len(df_preds),
        "models": list(df_preds["model_name"].unique()),
        "targets": list(df_preds["target"].unique()),
        "splits": list(df_preds["split_name"].unique()),
        "output_path": str(output_path),
    }
    
    write_research_report(
        name=f"ml_predictions_export_{v_norm}",
        payload=report_payload,
        title=f"ML Predictions Export {v_norm.upper()}",
        lines=[
            f"Predictions exported to {output_path}.",
            f"Total rows: {len(df_preds)}.",
            f"Targets: {report_payload['targets']}.",
            f"Models: {report_payload['models']}.",
            "Out-of-sample predictions only.",
        ],
        output_dir="reports/research",
    )
    
    print(f"Exported {len(df_preds)} predictions to {output_path}")


if __name__ == "__main__":
    main()
