import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


from galapagos.research.ml.dataset import load_ml_dataset
from galapagos.research.ml.feature_sets import extract_features, get_feature_set
from galapagos.research.ml.models import MODEL_REGISTRY, create_model
from galapagos.research.ml.permutation import run_permutation_test
from galapagos.research.ml.walk_forward import build_date_based_walk_forward_splits
from galapagos.research.report_models import write_research_report
from galapagos.utils.config_loader import load_yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--version", default="v1.15.1")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = run_permutation(args.dataset, args.config, args.version, args.dry_run)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


def run_permutation(dataset_path: str, config_path: str, version_str: str, dry_run: bool) -> dict:
    if dry_run:
        return {"status": "dry_run_completed"}
    
    config = load_yaml(config_path)
    dataset, report = load_ml_dataset(dataset_path)
    if dataset is None:
        return {"status": "missing_dataset"}
        
    windows = build_date_based_walk_forward_splits(dataset, config)
    if not windows:
        return {"status": "no_windows"}
        
    n_permutations = config.get("permutation", {}).get("n_permutations", 50)
    
    # We will test only the best model from V1.15 context:
    # random_forest on alpha_scores target_up_after_cost_12bar
    target = "target_up_after_cost_12bar"
    feature_set = "alpha_scores"
    model_name = "random_forest"
    
    if target not in dataset.columns or model_name not in MODEL_REGISTRY:
        return {"status": "missing_prerequisites"}
        
    feature_cols, _ = get_feature_set(dataset, feature_set)
    if not feature_cols:
        return {"status": "no_features"}
        
    results = []
    model = create_model(model_name)
    
    for w in windows:
        train_slice = dataset.iloc[w.train_start:w.train_end]
        test_slice = dataset.iloc[w.test_start:w.test_end]
        
        train_mask = train_slice[target].notna()
        test_mask = test_slice[target].notna()
        
        x_train = extract_features(train_slice[train_mask], feature_cols).values
        y_train = train_slice.loc[train_mask, target].values.astype(float)
        x_test = extract_features(test_slice[test_mask], feature_cols).values
        y_test = test_slice.loc[test_mask, target].values.astype(float)
        
        if len(x_train) > 100 and len(x_test) > 50:
            res = run_permutation_test(
                model, x_train, y_train, x_test, y_test,
                n_permutations=n_permutations,
            )
            results.append({
                "window": w.name,
                "target": target,
                "model": model_name,
                "feature_set": feature_set,
                "permutation": res,
            })
            
    payload = {"version": version_str.upper(), "results": results}
    version_suffix = version_str.lower().replace(".", "_")
    write_research_report(
        name=f"ml_permutation_tests_{version_suffix}",
        payload=payload,
        title=f"ML Permutation Tests {version_str.upper()}",
        lines=["Tests de permutation pour valider la robustesse de l'edge."],
    )
    return payload


if __name__ == "__main__":
    main()
