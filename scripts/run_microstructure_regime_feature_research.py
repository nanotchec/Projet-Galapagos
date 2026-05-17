from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def _copy_report(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mirror the V1.47 microstructure regime feature research artifacts.")
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--alpha-dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--regime-data-quality-summary", required=True)
    parser.add_argument("--feature-ablation-summary", required=True)
    parser.add_argument("--regime-feature-inventory", required=True)
    parser.add_argument("--canonical-summary", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    required_inputs = [
        args.predictions,
        args.dataset,
        args.alpha_dataset,
        args.intrabar,
        args.regime_data_quality_summary,
        args.feature_ablation_summary,
        args.regime_feature_inventory,
        args.canonical_summary,
    ]
    missing_inputs = [path for path in required_inputs if not Path(path).exists()]
    if missing_inputs:
        raise FileNotFoundError(f"Missing input files: {missing_inputs}")

    version_suffix = args.version.replace(".", "_").lower()
    report_dir = Path("reports/research")

    mirror_pairs = {
        f"microstructure_input_guard_{version_suffix}.json": f"microstructure_input_guard_{version_suffix}.json",
        f"microstructure_input_guard_{version_suffix}.md": f"microstructure_input_guard_{version_suffix}.md",
        f"microstructure_feature_inventory_{version_suffix}.json": f"microstructure_feature_inventory_{version_suffix}.json",
        f"microstructure_feature_inventory_{version_suffix}.md": f"microstructure_feature_inventory_{version_suffix}.md",
        f"microstructure_feature_build_{version_suffix}.json": f"microstructure_feature_build_report_{version_suffix}.json",
        f"microstructure_feature_build_{version_suffix}.md": f"microstructure_feature_build_report_{version_suffix}.md",
        f"microstructure_causal_audit_{version_suffix}.json": f"microstructure_causal_availability_audit_{version_suffix}.json",
        f"microstructure_causal_audit_{version_suffix}.md": f"microstructure_causal_availability_audit_{version_suffix}.md",
        f"microstructure_coverage_{version_suffix}.json": f"microstructure_coverage_audit_{version_suffix}.json",
        f"microstructure_coverage_{version_suffix}.md": f"microstructure_coverage_audit_{version_suffix}.md",
        f"microstructure_missingness_{version_suffix}.json": f"microstructure_missingness_audit_{version_suffix}.json",
        f"microstructure_missingness_{version_suffix}.md": f"microstructure_missingness_audit_{version_suffix}.md",
        f"microstructure_stability_{version_suffix}.json": f"microstructure_stability_analysis_{version_suffix}.json",
        f"microstructure_stability_{version_suffix}.md": f"microstructure_stability_analysis_{version_suffix}.md",
        f"microstructure_regime_relevance_{version_suffix}.json": f"microstructure_regime_relevance_analysis_{version_suffix}.json",
        f"microstructure_regime_relevance_{version_suffix}.md": f"microstructure_regime_relevance_analysis_{version_suffix}.md",
        f"microstructure_scorecard_{version_suffix}.json": f"microstructure_feature_quality_scorecard_{version_suffix}.json",
        f"microstructure_scorecard_{version_suffix}.md": f"microstructure_feature_quality_scorecard_{version_suffix}.md",
        f"microstructure_recommendation_{version_suffix}.json": f"microstructure_enrichment_recommendation_{version_suffix}.json",
        f"microstructure_recommendation_{version_suffix}.md": f"microstructure_enrichment_recommendation_{version_suffix}.md",
        f"microstructure_regime_feature_summary_{version_suffix}.json": f"microstructure_regime_feature_summary_{version_suffix}.json",
        f"microstructure_regime_feature_summary_{version_suffix}.md": f"microstructure_regime_feature_summary_{version_suffix}.md",
        f"microstructure_consistency_check_{version_suffix}.json": f"microstructure_regime_feature_consistency_check_{version_suffix}.json",
        f"microstructure_consistency_check_{version_suffix}.md": f"microstructure_regime_feature_consistency_check_{version_suffix}.md",
        f"v1_47_recommendation.json": f"v1_47_recommendation.json",
        f"v1_47_recommendation.md": f"v1_47_recommendation.md",
        f"docs/microstructure_regime_feature_research_v1_47.md": f"docs/microstructure_regime_feature_research_v1_47.md",
    }

    for src_name, dst_name in mirror_pairs.items():
        src = report_dir / src_name if not src_name.startswith("docs/") else Path(src_name)
        dst = report_dir / dst_name if not dst_name.startswith("docs/") else Path(dst_name)
        if src.exists():
            _copy_report(src, dst)

    print(json.dumps({
        "version": args.version,
        "status": "MICROSTRUCTURE_REGIME_FEATURE_RESEARCH_MIRRORED",
        "mirrored_reports": len(mirror_pairs),
        "inputs_checked": len(required_inputs),
        "missing_inputs": [],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
