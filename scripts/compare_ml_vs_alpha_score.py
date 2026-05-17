from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


from galapagos.research.ml.dataset import load_ml_dataset
from galapagos.research.ml.feature_sets import extract_features, get_feature_set
from galapagos.research.ml.models import SKLEARN_AVAILABLE, create_model
from galapagos.research.report_models import write_research_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        default="data/gold/research_dataset/BTC/4h/research_dataset_with_alpha_scores.parquet",
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--version", default="v1.15.1")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = compare_ml_vs_alpha(args.dataset, args.config, args.version, dry_run=args.dry_run)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


def compare_ml_vs_alpha(dataset_path: str, config_path: str, version_str: str, *, dry_run: bool = False) -> dict:
    if dry_run:
        return {"status": "dry_run_completed", "dataset_exists": Path(dataset_path).exists()}

    from galapagos.research.ml.top_bucket_analysis import analyze_top_bucket
    from galapagos.research.ml.walk_forward import build_date_based_walk_forward_splits
    from galapagos.utils.config_loader import load_yaml
    
    config = load_yaml(config_path)
    dataset, ds_report = load_ml_dataset(dataset_path)
    if dataset is None:
        return {"status": "missing_dataset", "report": ds_report}

    target = "target_up_after_cost_12bar"
    if target not in dataset.columns:
        return {"status": "missing_target"}
        
    forward_col = "forward_return_12bar"

    windows = build_date_based_walk_forward_splits(dataset, config)
    if not windows:
        return {"status": "no_windows"}

    comparisons = []
    for w in windows:
        train = dataset.iloc[w.train_start:w.train_end]
        test = dataset.iloc[w.test_start:w.test_end]
        mask_train = train[target].notna() & train[forward_col].notna()
        mask_test = test[target].notna() & test[forward_col].notna()
        y_test = test.loc[mask_test, target].values.astype(float)
        f_test = test.loc[mask_test, forward_col].values.astype(float)
        
        if len(y_test) < 50:
            continue

        # Alpha score baseline using top bucket
        alpha_col = "combined_alpha_score"
        alpha_bucket = {"status": "no_alpha_score"}
        if alpha_col in test.columns:
            alpha_vals = test.loc[mask_test, alpha_col].fillna(0).values
            # Alpha top bucket
            alpha_bucket = analyze_top_bucket(alpha_vals, f_test)

        # Best ML model (Random Forest on alpha_scores)
        ml_bucket = {"status": "no_sklearn"}
        if SKLEARN_AVAILABLE:
            feat_cols, _ = get_feature_set(dataset, "alpha_scores")
            if feat_cols:
                x_train = extract_features(train[mask_train], feat_cols).values
                y_train = train.loc[mask_train, target].values.astype(float)
                x_test_f = extract_features(test[mask_test], feat_cols).values
                model = create_model("random_forest")
                try:
                    model.fit(x_train, y_train)
                    proba = model.predict_proba(x_test_f)
                    if proba.shape[1] == 2:
                        y_proba = proba[:, 1]
                        ml_bucket = analyze_top_bucket(y_proba, f_test)
                except Exception as e:  # noqa: BLE001
                    ml_bucket = {"status": "error", "error": str(e)}

        comparisons.append({
            "window": w.name,
            "test_rows": len(y_test),
            "alpha_score_top_10": alpha_bucket.get("top_10", {}),
            "ml_top_10": ml_bucket.get("top_10", {}),
        })

    # Verdict counts
    windows_tested = len(comparisons)
    windows_ml_beats_alpha_score = 0
    windows_ml_positive_after_cost = 0
    
    for c in comparisons:
        ml_ret = c.get("ml_top_10", {}).get("cost_adjusted_return", -1)
        alpha_ret = c.get("alpha_score_top_10", {}).get("cost_adjusted_return", -1)
        if ml_ret > alpha_ret and ml_ret > 0:
            windows_ml_beats_alpha_score += 1
        if ml_ret > 0:
            windows_ml_positive_after_cost += 1

    all_windows_ml_beats_alpha_score = (windows_ml_beats_alpha_score == windows_tested) and (windows_tested > 0)
    all_windows_ml_positive_after_cost = (windows_ml_positive_after_cost == windows_tested) and (windows_tested > 0)
    some_windows_ml_beats_alpha_score = windows_ml_beats_alpha_score > 0
    some_windows_ml_positive_after_cost = windows_ml_positive_after_cost > 0

    payload = {
        "version": version_str.upper(),
        "comparisons": comparisons,
        "ml_beats_alpha_score_and_costs": all_windows_ml_beats_alpha_score, # kept for backward compat, but stricter now
        "windows_tested": windows_tested,
        "windows_ml_beats_alpha_score": windows_ml_beats_alpha_score,
        "windows_ml_positive_after_cost": windows_ml_positive_after_cost,
        "all_windows_ml_beats_alpha_score": all_windows_ml_beats_alpha_score,
        "all_windows_ml_positive_after_cost": all_windows_ml_positive_after_cost,
        "some_windows_ml_beats_alpha_score": some_windows_ml_beats_alpha_score,
        "some_windows_ml_positive_after_cost": some_windows_ml_positive_after_cost,
        "holdout_executed": False,
        "codex_cli_called": False,
    }
    version_suffix = version_str.lower().replace(".", "_")
    write_research_report(
        name=f"ml_vs_alpha_score_{version_suffix}", payload=payload,
        title=f"ML vs Alpha Score {version_str.upper()}",
        lines=[
            f"ML bat alpha sur {windows_ml_beats_alpha_score}/{windows_tested} fenetres.",
            f"ML positif apres couts sur {windows_ml_positive_after_cost}/{windows_tested} fenetres.",
            "ML ne doit pas etre considere robuste si X < 2 ou si une fenetre recente echoue.",
            "Holdout non execute, aucun ordre reel.",
        ],
    )
    return payload


if __name__ == "__main__":
    main()
