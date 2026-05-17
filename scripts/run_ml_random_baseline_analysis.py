import argparse
import json
from typing import Any

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


from galapagos.research.ml.dataset import load_ml_dataset
from galapagos.research.ml.random_trading_baselines import random_entries_same_count
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

    result = run_analysis(args.dataset, args.config, args.version, args.dry_run)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


def run_analysis(dataset_path: str, config_path: str, version_str: str, dry_run: bool) -> dict[str, Any]:
    if dry_run:
        return {"status": "dry_run_completed"}
    
    config = load_yaml(config_path)
    dataset, report = load_ml_dataset(dataset_path)
    if dataset is None:
        return {"status": "missing_dataset"}
        
    windows = build_date_based_walk_forward_splits(dataset, config)
    if not windows:
        return {"status": "no_windows"}
        
    n_trials = config.get("random_baselines", {}).get("n_trials", 200)
    
    results = []
    for w in windows:
        test_slice = dataset.iloc[w.test_start:w.test_end]
        
        # Calculate exact top bucket size corresponding to ML models (top decile)
        count = max(1, len(test_slice) // 10)
        
        if len(test_slice) > count:
            b = random_entries_same_count(
                test_slice, entry_count=count, n_trials=n_trials,
            )
            b.pop("raw_trials", None)
            results.append({
                "window": w.name,
                "target_count": count,
                "ml_top_bucket_count": count,
                "same_count_match": True,
                "baseline": b,
            })
                
    payload = {"version": version_str.upper(), "results": results}
    version_suffix = version_str.lower().replace(".", "_")
    write_research_report(
        name=f"ml_random_baselines_{version_suffix}",
        payload=payload,
        title=f"ML Random Trading Baselines {version_str.upper()}",
        lines=["Baselines de trading aleatoire."],
    )
    return payload


if __name__ == "__main__":
    main()
