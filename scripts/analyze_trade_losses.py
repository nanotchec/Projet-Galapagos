from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from datetime import UTC, datetime

import pandas as pd

try:
    from _bootstrap import bootstrap_src_path
    bootstrap_src_path()
except ImportError:
    pass

from galapagos.research.loss_attribution.loader import load_v1_22_1_baseline, load_research_context
from galapagos.research.loss_attribution.analyzer_core import reconstruct_evaluation, results_to_df
from galapagos.research.loss_attribution.policy_breakdown import analyze_policy_performance
from galapagos.research.loss_attribution.cost_attribution import analyze_cost_impact
from galapagos.research.loss_attribution.exit_reason_analysis import analyze_exit_reasons
from galapagos.research.loss_attribution.mae_mfe_analysis import analyze_mae_mfe
from galapagos.research.loss_attribution.holding_time_analysis import analyze_holding_time
from galapagos.research.loss_attribution.regime_loss_analysis import analyze_regimes
from galapagos.research.loss_attribution.confidence_bucket_analysis import analyze_confidence_buckets
from galapagos.research.loss_attribution.tail_risk_analysis import analyze_tail_risk
from galapagos.research.loss_attribution.contribution_decomposition import decompose_contributions
from galapagos.research.loss_attribution.recommendation_engine import generate_recommendations
from galapagos.research.loss_attribution.report_models import save_loss_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="V1.23.1 Loss Attribution Analyzer (Per-Policy)")
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--trade-ledger-report", required=True)
    parser.add_argument("--policies", default="fixed_percent,atr_proxy,horizon_only")
    parser.add_argument("--version", default="v1.23.1")
    
    args = parser.parse_args()
    v_v = args.version.replace(".", "_")
    
    print(f"--- Galapagos {args.version} Loss Attribution Analyzer ---")
    
    # 1. Load context
    print("Loading data...")
    baseline = load_v1_22_1_baseline(args.trade_ledger_report)
    context = load_research_context(args.predictions, args.dataset, args.intrabar)
    
    # 2. Reconstruct Evaluation
    print("Reconstructing evaluation (memory-only)...")
    policy_names = args.policies.split(",")
    raw_results = reconstruct_evaluation(
        args.predictions, context["dataset"], context["intrabar"], policy_names
    )
    
    # Prepare DFs for all policies
    policy_dfs = {}
    for p_name, bundle in raw_results.items():
        policy_dfs[p_name] = results_to_df(bundle["results"], bundle["candidates"])
    
    all_verdicts_by_policy = {p_name: {} for p_name in policy_names}
    
    # 3. Component Analysis (Per Policy)
    print("Running component analyses per policy...")
    
    # Policy Breakdown
    policy_breakdown_reports = {}
    for p_name, df in policy_dfs.items():
        rep = analyze_policy_performance(df, p_name)
        policy_breakdown_reports[p_name] = rep
        all_verdicts_by_policy[p_name]["policy_breakdown"] = rep["verdict"]
    
    save_loss_report(f"loss_policy_breakdown_{v_v}", policy_breakdown_reports)
    md_content = f"# Policy Breakdown\n\n```json\n{json.dumps(policy_breakdown_reports, indent=2)}\n```"
    save_loss_report(f"loss_policy_breakdown_{v_v}", md_content)
    
    # Cost Attribution
    cost_reports = {}
    for p_name, df in policy_dfs.items():
        rep = analyze_cost_impact(df)
        cost_reports[p_name] = rep
        all_verdicts_by_policy[p_name]["cost_attribution"] = rep["verdict"]
    
    cost_summary = {
        "by_policy": cost_reports,
        "verdict": _consensus_verdict([r["verdict"] for r in cost_reports.values()])
    }
    save_loss_report(f"loss_cost_attribution_{v_v}", cost_summary)
    md_content = f"# Cost Attribution\n\n```json\n{json.dumps(cost_summary, indent=2)}\n```"
    save_loss_report(f"loss_cost_attribution_{v_v}", md_content)
    
    # Exit Reason
    exit_reports = {}
    for p_name, df in policy_dfs.items():
        rep = analyze_exit_reasons(df)
        exit_reports[p_name] = rep
        all_verdicts_by_policy[p_name]["exit_reasons"] = rep["verdict"]
        
    exit_summary = {
        "by_policy": exit_reports,
        "verdict": _consensus_verdict([r["verdict"] for r in exit_reports.values()])
    }
    save_loss_report(f"loss_exit_reason_analysis_{v_v}", exit_summary)
    md_content = f"# Exit Reason Analysis\n\n```json\n{json.dumps(exit_summary, indent=2)}\n```"
    save_loss_report(f"loss_exit_reason_analysis_{v_v}", md_content)
    
    # MAE/MFE
    mae_reports = {}
    for p_name, df in policy_dfs.items():
        rep = analyze_mae_mfe(df)
        mae_reports[p_name] = rep
        all_verdicts_by_policy[p_name]["mae_mfe"] = rep["verdict"]
        
    mae_summary = {
        "by_policy": mae_reports,
        "verdict": _consensus_verdict([r["verdict"] for r in mae_reports.values()])
    }
    save_loss_report(f"loss_mae_mfe_analysis_{v_v}", mae_summary)
    md_content = f"# MAE/MFE Analysis\n\n```json\n{json.dumps(mae_summary, indent=2)}\n```"
    save_loss_report(f"loss_mae_mfe_analysis_{v_v}", md_content)
    
    # Holding Time
    hold_reports = {}
    for p_name, df in policy_dfs.items():
        rep = analyze_holding_time(df)
        hold_reports[p_name] = rep
        all_verdicts_by_policy[p_name]["holding_time"] = rep["verdict"]
        
    hold_summary = {
        "by_policy": hold_reports,
        "verdict": _consensus_verdict([r["verdict"] for r in hold_reports.values()])
    }
    save_loss_report(f"loss_holding_time_analysis_{v_v}", hold_summary)
    md_content = f"# Holding Time Analysis\n\n```json\n{json.dumps(hold_summary, indent=2)}\n```"
    save_loss_report(f"loss_holding_time_analysis_{v_v}", md_content)
    
    # Regimes
    regime_reports = {}
    for p_name, df in policy_dfs.items():
        rep = analyze_regimes(df, context["dataset"])
        regime_reports[p_name] = rep
        all_verdicts_by_policy[p_name]["regimes"] = rep["verdict"]
        
    regime_summary = {
        "by_policy": regime_reports,
        "verdict": _consensus_verdict([r["verdict"] for r in regime_reports.values()])
    }
    save_loss_report(f"loss_regime_analysis_{v_v}", regime_summary)
    md_content = f"# Regime Analysis\n\n```json\n{json.dumps(regime_summary, indent=2)}\n```"
    save_loss_report(f"loss_regime_analysis_{v_v}", md_content)
    
    # Confidence
    conf_reports = {}
    for p_name, df in policy_dfs.items():
        rep = analyze_confidence_buckets(df)
        conf_reports[p_name] = rep
        verdict = rep.get("verdict", "PROBABILITY_EDGE_TOO_WEAK")
        all_verdicts_by_policy[p_name]["confidence"] = verdict
        
    conf_summary = {
        "by_policy": conf_reports,
        "verdict": _consensus_verdict([r.get("verdict", "PROBABILITY_EDGE_TOO_WEAK") for r in conf_reports.values()])
    }
    save_loss_report(f"loss_confidence_bucket_analysis_{v_v}", conf_summary)
    md_content = f"# Confidence Bucket Analysis\n\n```json\n{json.dumps(conf_summary, indent=2)}\n```"
    save_loss_report(f"loss_confidence_bucket_analysis_{v_v}", md_content)
    
    # Tail Risk
    tail_reports = {}
    for p_name, df in policy_dfs.items():
        rep = analyze_tail_risk(df)
        tail_reports[p_name] = rep
        all_verdicts_by_policy[p_name]["tail_risk"] = rep["verdict"]
        
    tail_summary = {
        "by_policy": tail_reports,
        "verdict": _consensus_verdict([r["verdict"] for r in tail_reports.values()])
    }
    save_loss_report(f"loss_tail_risk_analysis_{v_v}", tail_summary)
    md_content = f"# Tail Risk Analysis\n\n```json\n{json.dumps(tail_summary, indent=2)}\n```"
    save_loss_report(f"loss_tail_risk_analysis_{v_v}", md_content)
    
    # 4. Synthesis
    print("Synthesizing results...")
    decomposition = decompose_contributions(all_verdicts_by_policy)
    save_loss_report(f"loss_contribution_decomposition_{v_v}", decomposition)
    md_content = f"# Contribution Decomposition\n\n```json\n{json.dumps(decomposition, indent=2)}\n```"
    save_loss_report(f"loss_contribution_decomposition_{v_v}", md_content)
    
    reco = generate_recommendations(decomposition)
    save_loss_report("v1_23_1_recommendation", reco)
    md_content = f"# V1.23.1 Recommendation\n\n```json\n{json.dumps(reco, indent=2)}\n```"
    save_loss_report("v1_23_1_recommendation", md_content)
    
    # Markdown documentation snippet
    md_path = Path(f"reports/research/loss_summary_{v_v}.md")
    md_lines = [
        f"# Loss Attribution Summary - {args.version}",
        "",
        f"Primary Global Driver: **{decomposition['global_ranked_loss_drivers'][0]['driver']}**",
        f"Evidence: **{decomposition['evidence']}**",
        "",
        "## Per-Policy Primary Drivers",
    ]
    for p_name, drivers in decomposition["by_policy_loss_drivers"].items():
        md_lines.append(f"- **{p_name}**: `{drivers[0]['driver']}`")
    
    md_lines.extend([
        "",
        "## Recommendation",
        f"**{reco['primary_recommendation']}**",
        ""
    ])
    md_path.write_text("\n".join(md_lines))
    
    print(f"--- Analysis {args.version} Complete ---")
    print(f"Summary: {md_path}")

def _consensus_verdict(verdicts: list[str]) -> str:
    """Determine the most frequent verdict among policies."""
    if not verdicts:
        return "UNKNOWN"
    from collections import Counter
    counts = Counter(verdicts)
    return counts.most_common(1)[0][0]

if __name__ == "__main__":
    main()
