import argparse
import json

from _bootstrap import bootstrap_src_path

bootstrap_src_path()


from galapagos.research.ml.dataset import load_ml_dataset
from galapagos.research.ml.feature_sets import get_feature_set
from galapagos.research.ml.leakage_audit import audit_ml_leakage
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

    result = run_audit(args.dataset, args.config, args.version, args.dry_run)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


def run_audit(dataset_path: str, config_path: str, version_str: str, dry_run: bool) -> dict:
    if dry_run:
        return {"status": "dry_run_completed"}
        
    config = load_yaml(config_path)
    dataset, report = load_ml_dataset(dataset_path)
    if dataset is None:
        return {"status": "missing_dataset"}
        
    windows = build_date_based_walk_forward_splits(dataset, config)
    if not windows:
        return {"status": "no_windows"}
        
    feature_sets = config.get("feature_sets", ["ohlcv_basic"])
    targets = config.get("targets", {}).get("classification", ["target_up_after_cost_12bar"])
    
    results = []
    global_verdict = "ML_LEAKAGE_AUDIT_PASSED"
    
    for fs in feature_sets:
        feature_cols, _ = get_feature_set(dataset, fs)
        if not feature_cols:
            continue
            
        for t in targets:
            for w in windows:
                train_idx = list(range(w.train_start, w.train_end))
                test_idx = list(range(w.test_start, w.test_end))
                res = audit_ml_leakage(dataset, feature_cols, t, train_idx, test_idx)
                
                results.append({
                    "feature_set": fs,
                    "target": t,
                    "window": w.name,
                    "audit": res,
                })
                if res["status"] != "ML_LEAKAGE_AUDIT_PASSED":
                    global_verdict = "ML_LEAKAGE_RISK_FOUND"
                    
    payload = {
        "version": version_str.upper(),
        "verdict": global_verdict,
        "results": results,
    }
    version_suffix = version_str.lower().replace(".", "_")
    write_research_report(
        name=f"ml_leakage_audit_{version_suffix}",
        payload=payload,
        title=f"ML Leakage Audit {version_str.upper()}",
        lines=[f"Verdict global: {global_verdict}."],
    )
    return payload


if __name__ == "__main__":
    main()
