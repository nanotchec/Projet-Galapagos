from __future__ import annotations

from pathlib import Path

import pandas as pd

from galapagos.research.ml.dataset import load_ml_dataset


def load_ensemble_inputs(
    dataset_path: str | Path,
    predictions_path: str | Path,
) -> pd.DataFrame | None:
    """Load and merge dataset and model predictions."""
    if not Path(predictions_path).exists():
        return None
        
    dataset, report = load_ml_dataset(dataset_path)
    if dataset is None:
        print(f"Error loading dataset: {report}")
        return None
        
    preds = pd.read_parquet(predictions_path)
    
    # FILTER OOS ONLY (Critical for ensemble validity)
    if "split_name" in preds.columns:
        preds = preds[preds["split_name"].str.contains("test", na=False)]
        if len(preds) == 0:
            print("Warning: No OOS predictions found (test_ split).")
    
    dataset["timestamp"] = pd.to_datetime(dataset["timestamp"], utc=True)
    preds["timestamp"] = pd.to_datetime(preds["timestamp"], utc=True)
    
    # We want a wide format for models
    # timestamp, model_1_prob, model_2_prob, target, alpha_score, ...
    
    # Filter only relevant columns from dataset
    base_cols = ["timestamp", "combined_alpha_score", "ohlcv_only_alpha_score",
                 "macro_regime_score", "derivatives_regime_score"]
    # Add any other relevant columns
    for col in dataset.columns:
        is_target = col.startswith("target_up_after_cost_")
        is_return = col.startswith("forward_return_")
        is_cost_adj = (col == "cost_adjusted_forward_return")
        if (is_target or is_return or is_cost_adj) and col not in base_cols:
            base_cols.append(col)
                
    df_base = dataset[base_cols].copy()
    
    # Pivot predictions
    # Pivot to get: timestamp | model1_prob | model2_prob | ...
    pivot_cols = ["timestamp", "model_name", "target", "predicted_probability"]
    df_preds_pivot = preds[pivot_cols].pivot_table(
        index="timestamp",
        columns=["model_name", "target"],
        values="predicted_probability"
    )
    # Flatten columns
    df_preds_pivot.columns = [f"{m}_{t}" for m, t in df_preds_pivot.columns]
    df_preds_pivot = df_preds_pivot.reset_index()
    
    # Merge
    merged = pd.merge(df_base, df_preds_pivot, on="timestamp", how="inner")
    
    return merged
