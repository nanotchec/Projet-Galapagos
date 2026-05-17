import json, os, glob, math

f = "reports/research/v1_46_recommendation.json"
new_f = "reports/research/v1_46_1_recommendation.json"

keep_flags = {
    "final_verdict": "REGIME_DATA_QUALITY_INCONCLUSIVE",
    "recommended_next_step": "improve data enrichment / regime labels before new modeling",
    "evidence_classification": "RESEARCH_ONLY",
    "no_new_filter": True,
    "no_strategy_validated": True,
    "no_preregistration_yet": True,
    "no_paper_live": True,
    "no_real_trading": True,
    "holdout_executed": False,
    "codex_cli_called": False,
    "release_ready_for_external_review": True,
    "best_regime_label_candidates": ["vol_regime"],
    "weak_regime_label_candidates": ["trend_regime"],
    "high_priority_enrichment_gaps": ["microstructure"],
}

required_versions = {
    "version": "V1.46.1",
    "previous_base": "V1.46",
    "feature_ablation_base_version": "V1.45.1",
    "regime_aware_feature_base_version": "V1.44.4",
    "regime_feature_base_version": "V1.43.4",
    "payoff_target_base_version": "V1.42.3",
    "payoff_failure_base_version": "V1.41",
    "ev_degradation_base_version": "V1.39",
    "canonical_base_version": "V1.37.2",
}

with open(f, "r") as fh:
    data = json.load(fh)

for k, v in required_versions.items():
    if k in data:
        data[k] = v
for k, v in keep_flags.items():
    if k in data:
        data[k] = v
data["version"] = "V1.46.1"

with open(new_f, "w") as fh:
    json.dump(data, fh, indent=2)

md_f = new_f.replace(".json", ".md")
with open("reports/research/v1_46_recommendation.md", "r") as fh:
    content = fh.read()
content = content.replace("V1.46", "V1.46.1").replace("v1_46", "v1_46_1")
with open(md_f, "w") as mdfh:
    mdfh.write(content)
