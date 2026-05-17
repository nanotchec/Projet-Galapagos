"""Reporting utilities for trade ledger evaluation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def generate_v1_19_2_reports(
    policy_metrics: dict[str, Any],
    comparison: dict[str, Any],
    audit_signals: dict[str, Any],
    ledger_audit: dict[str, Any],
    eval_audit: dict[str, Any],
    version: str = "v1_19_2",
):
    """Generate comprehensive research reports for V1.19.2 evaluation."""
    v_norm = version.replace(".", "_")
    reports_dir = Path("reports/research")
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 1. Trade Signal Loader Report
    loader_data = {
        "version": version,
        "audit": audit_signals,
        "status": "COMPLETE",
    }
    with open(reports_dir / f"trade_signal_loader_{v_norm}.json", "w") as f:
        json.dump(loader_data, f, indent=2)

    with open(reports_dir / f"trade_signal_loader_{v_norm}.md", "w") as f:
        f.write(f"# Trade Signal Loader - {version}\n\n")
        f.write(f"- **Raw Signals**: {audit_signals.get('raw_signal_rows')}\n")
        f.write(f"- **Unique Timestamps**: {audit_signals.get('unique_signal_timestamps')}\n")
        f.write(f"- **Policy**: {audit_signals.get('selected_signal_policy')}\n")

    # 2. Trade Ledger Build Report
    ledger_data = {
        "version": version,
        "audit": ledger_audit,
        "status": "COMPLETE",
    }
    with open(reports_dir / f"trade_ledger_build_{v_norm}.json", "w") as f:
        json.dump(ledger_data, f, indent=2)

    with open(reports_dir / f"trade_ledger_build_{v_norm}.md", "w") as f:
        f.write(f"# Trade Ledger Build - {version}\n\n")
        for p_name, audit in ledger_audit.items():
            f.write(f"## Policy: {p_name}\n")
            f.write(f"- **Candidates**: {audit.get('candidates_count')}\n")
            f.write(f"- **Next Candle Entry**: {audit.get('next_candle_entry_count')}\n")
            f.write(f"- **Fallback Entry**: {audit.get('fallback_entry_count')}\n\n")

    # 3. Trade Intrabar Evaluation Report
    intrabar_eval_data = {
        "version": version,
        "audit": eval_audit,
        "status": "COMPLETE",
    }
    with open(reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.json", "w") as f:
        json.dump(intrabar_eval_data, f, indent=2)

    with open(reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.md", "w") as f:
        f.write(f"# Trade Intrabar Evaluation - {version}\n\n")
        f.write("> [!WARNING]\n")
        f.write("> Coverage is extremely low (approx 1.73%). Results are not robust.\n\n")
        for p_name, audit in eval_audit.items():
            f.write(f"## Policy: {p_name}\n")
            f.write(f"- **Evaluated**: {audit.get('evaluated_count')}\n")
            f.write(f"- **Missing Intrabar**: {audit.get('missing_intrabar_count')}\n")
            f.write(f"- **Coverage Mean**: {audit.get('coverage_mean', 0.0):.2%}\n\n")

    # 4. Trade Policy Metrics Report
    with open(reports_dir / f"trade_policy_metrics_{v_norm}.json", "w") as f:
        json.dump({"version": version, "metrics": policy_metrics}, f, indent=2)

    with open(reports_dir / f"trade_policy_metrics_{v_norm}.md", "w") as f:
        f.write(f"# Trade Policy Metrics - {version}\n\n")
        for name, m in policy_metrics.items():
            f.write(f"## Policy: {name}\n")
            f.write(f"- **Evaluated Ratio**: {m.get('evaluated_ratio', 0.0):.2%}\n")
            f.write(f"- **Sample Limited**: {m.get('intrabar_sample_limited')}\n")
            f.write(f"- **Win Rate**: {m.get('win_rate', 0.0):.2%}\n")
            mn = m.get('mean_pnl_after_cost_pct', 0.0)
            md = m.get('median_pnl_after_cost_pct', 0.0)
            f.write(f"- **Mean PnL (After Cost)**: {mn:.4%}\n")
            f.write(f"- **Median PnL (After Cost)**: {md:.4%}\n\n")

    # 5. Trade Policy Comparison Report
    with open(reports_dir / f"trade_policy_comparison_{v_norm}.json", "w") as f:
        json.dump({"version": version, "comparison": comparison}, f, indent=2)

    with open(reports_dir / f"trade_policy_comparison_{v_norm}.md", "w") as f:
        f.write(f"# Trade Policy Comparison - {version}\n\n")
        f.write(f"- **Verdict**: `{comparison.get('verdict')}`\n")
        f.write(f"- **Comparison Valid**: {comparison.get('policy_comparison_valid')}\n")
        f.write(f"- **Best Observed Policy**: {comparison.get('best_policy')}\n")
        if comparison.get("warnings"):
            f.write(f"- **Warnings**: {', '.join(comparison.get('warnings'))}\n")

    # 6. Global Ledger Eval Summary (JSON)
    summary_data = {
        "version": version,
        "signal_audit": audit_signals,
        "ledger_audit": ledger_audit,
        "eval_audit": eval_audit,
        "policy_metrics": policy_metrics,
        "comparison": comparison,
        "simulation_input_type": "real_signal_candidates_with_deterministic_research_policies",
        "is_real_trade_simulation": False,
        "ready_for_reviewer": False,
    }
    with open(reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.json", "w") as f:
        json.dump(summary_data, f, indent=2)

    # 7. Markdown Summary
    eval_count = sum(m.get('evaluated_count', 0) for m in policy_metrics.values())
    total_candidates = audit_signals.get('unique_signal_timestamps', 0)
    metrics_len = len(policy_metrics)
    eval_ratio = eval_count / (total_candidates * metrics_len) if total_candidates > 0 else 0
    
    md_content = f"""# Trade Ledger Intrabar Evaluation Summary - {version}

## Data Coverage Honesty
> [!IMPORTANT]
> **Evaluated Ratio**: {eval_ratio:.2%}
> The intrabar sample is too short to draw robust conclusions. 
> {eval_count // len(policy_metrics)} candidates were evaluated out of {total_candidates}.

## Final Verdict
- **Comparison Verdict**: `{comparison.get('verdict')}`
- **Policy Comparison Valid**: {comparison.get('policy_comparison_valid')}
- **Best Policy (Observed)**: {comparison.get('best_policy')}

## Policy Performance (After Cost)
"""
    for name, m in policy_metrics.items():
        md_content += f"""
### {name}
- **Win Rate**: {m.get('win_rate', 0.0):.2%}
- **Median PnL**: {m.get('median_pnl_after_cost_pct', 0.0):.4%}
- **MAE (Mean)**: {m.get('mean_mae_pct', 0.0):.2%}
"""

    msg = f"Le système {version} ne peut toujours pas passer d'ordre réel. " \
          "La couverture intrabar est insuffisante pour valider une politique de trading."
    md_content += f"\n## Conclusion\n{msg}\n"
    with open(reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.md", "w") as f:
        f.write(md_content)

    # 8. Recommendation Report
    reco = {
        "primary_recommendation": "Extend 5m intrabar history before conclusions",
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True,
        "verdict": comparison.get("verdict"),
        "do_not_do_next": ["Do not activate reviewer", "Do not trade live"],
        "caveat_30d_intrabar_sample": True,
    }
    with open(reports_dir / f"{v_norm}_recommendation.json", "w") as f:
        json.dump(reco, f, indent=2)

    # Markdown reco
    ec_pm = eval_count // len(policy_metrics)
    reco_md = f"""# {version} Recommendation

**Primary**: {reco['primary_recommendation']}

- **Verdict**: `{reco['verdict']}`
- **Ready for Reviewer**: `false`
- **Holdout**: `not executed`
- **Caveat**: Intrabar sample covers {ec_pm}/{total_candidates} candidates.

**DO NOT**:
- Activate LLM Reviewer.
- Execute Holdout.
- Trade live.
"""
    with open(reports_dir / f"{v_norm}_recommendation.md", "w") as f:
        f.write(reco_md)

def generate_v1_20_1_reports(
    policy_metrics: dict[str, Any],
    comparison: dict[str, Any],
    audit_signals: dict[str, Any],
    ledger_audit: dict[str, Any],
    eval_audit: dict[str, Any],
    version: str = "v1_20_1",
    intrabar_metadata: dict[str, Any] | None = None,
):
    """Generate comprehensive research reports for V1.20.1 evaluation with lineage."""
    v_norm = version.replace(".", "_")
    reports_dir = Path("reports/research")
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 1. Trade Intrabar Evaluation Report (Updated with lineage info)
    intrabar_eval_data = {
        "version": version,
        "audit": eval_audit,
        "intrabar_source": intrabar_metadata or {},
        "status": "COMPLETE",
    }
    with open(reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.json", "w") as f:
        json.dump(intrabar_eval_data, f, indent=2)

    with open(reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.md", "w") as f:
        f.write(f"# Trade Intrabar Evaluation - {version}\n\n")
        if intrabar_metadata:
            f.write("## Intrabar Source Metadata\n")
            f.write(f"- **File**: `{intrabar_metadata.get('file_path')}`\n")
            f.write(f"- **Rows**: {intrabar_metadata.get('rows')}\n")
            ts_first = intrabar_metadata.get('first_timestamp')
            ts_last = intrabar_metadata.get('last_timestamp')
            f.write(f"- **Range**: {ts_first} to {ts_last}\n\n")
        
        eval_count = sum(a.get('evaluated_count', 0) for a in eval_audit.values())
        total_count = sum(a.get('candidates_count', 1) for a in ledger_audit.values())
        ratio = eval_count / total_count if total_count > 0 else 0
        
        f.write("> [!WARNING]\n")
        f.write(f"> Coverage is still low ({ratio:.2%}). Results are not robust.\n\n")
        
        for p_name, audit in eval_audit.items():
            f.write(f"## Policy: {p_name}\n")
            f.write(f"- **Evaluated**: {audit.get('evaluated_count')}\n")
            f.write(f"- **Missing Intrabar**: {audit.get('missing_intrabar_count')}\n")
            f.write(f"- **Coverage Mean**: {audit.get('coverage_mean', 0.0):.2%}\n\n")

    # 2. Re-use other reports from 1.19.2 logic
    generate_v1_19_2_reports(
        policy_metrics, comparison, audit_signals, ledger_audit, eval_audit, version=version
    )
    
    # 3. Enhanced Global Ledger Eval Summary (JSON)
    summary_data = {
        "version": version,
        "signal_audit": audit_signals,
        "ledger_audit": ledger_audit,
        "eval_audit": eval_audit,
        "policy_metrics": policy_metrics,
        "comparison": comparison,
        "intrabar_metadata": intrabar_metadata or {},
        "simulation_input_type": "real_signal_candidates_with_deterministic_research_policies",
        "is_real_trade_simulation": False,
        "ready_for_reviewer": False,
    }
    with open(reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.json", "w") as f:
        json.dump(summary_data, f, indent=2)

def generate_v1_21_reports(
    policy_metrics: dict[str, Any],
    comparison: dict[str, Any],
    audit_signals: dict[str, Any],
    ledger_audit: dict[str, Any],
    eval_audit: dict[str, Any],
    version: str = "v1_21",
    intrabar_metadata: dict[str, Any] | None = None,
):
    """Generate comprehensive research reports for V1.21 with 20% target logic."""
    v_norm = version.replace(".", "_")
    reports_dir = Path("reports/research")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Coverage Analysis
    eval_count = sum(a.get('evaluated_count', 0) for a in eval_audit.values())
    total_count = sum(a.get('candidates_count', 1) for a in ledger_audit.values())
    ratio = eval_count / total_count if total_count > 0 else 0
    target_ratio = 0.20
    is_target_reached = ratio >= target_ratio
    
    # Adjust comparison validity
    if is_target_reached:
        comparison['policy_comparison_valid'] = "preliminary"
        if comparison.get('verdict') == "TRADE_LEDGER_INTRABAR_SAMPLE_TOO_SHORT":
            comparison['verdict'] = "TRADE_LEDGER_PRELIMINARY_COMPARISON_AVAILABLE"
        if comparison.get('all_negative'):
            comparison['verdict'] = "ALL_POLICIES_NEGATIVE_AFTER_COSTS"

    # 2. Evaluation Report
    with open(reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.md", "w") as f:
        f.write(f"# Trade Intrabar Evaluation - {version}\n\n")
        f.write(f"- **Evaluated Ratio**: {ratio:.2%} (Target: {target_ratio:.0%})\n")
        f.write(f"- **Target Reached**: {is_target_reached}\n\n")
        
        for p_name, audit in eval_audit.items():
            f.write(f"## Policy: {p_name}\n")
            f.write(f"- **Evaluated**: {audit.get('evaluated_count')}\n")
            f.write(f"- **Coverage Mean**: {audit.get('coverage_mean', 0.0):.2%}\n\n")

    # 3. Policy Comparison Report
    with open(reports_dir / f"trade_policy_comparison_{v_norm}.md", "w") as f:
        f.write(f"# Trade Policy Comparison - {version}\n\n")
        f.write(f"- **Verdict**: `{comparison.get('verdict')}`\n")
        f.write(f"- **Validity**: `{comparison.get('policy_comparison_valid')}`\n\n")
        
        f.write("| Policy | Win Rate | Mean PnL (AC) | Median PnL (AC) |\n")
        f.write("|---|---:|---:|---:|\n")
        for name, m in policy_metrics.items():
            wr = m.get('win_rate', 0.0)
            mn = m.get('mean_pnl_after_cost_pct', 0.0)
            md = m.get('median_pnl_after_cost_pct', 0.0)
            f.write(f"| {name} | {wr:.2%} | {mn:.4%} | {md:.4%} |\n")

    # 4. Recommendation
    reco_txt = "Extend to 50%" if is_target_reached else "Continue extension to 20%"
    reco_md = f"""# {version} Recommendation

- **Verdict**: `{comparison.get('verdict')}`
- **Coverage**: {ratio:.2%} (Target 20%: {'OK' if is_target_reached else 'KO'})
- **Ready for Reviewer**: `false`
- **Primary Recommendation**: {reco_txt}

**DO NOT**:
- Activate LLM Reviewer.
- Execute Holdout.
- Trade live.
"""
    with open(reports_dir / "v1_21_recommendation.md", "w") as f:
        f.write(reco_md)
        
    # 5. Full Summary JSON
    summary_data = {
        "version": version,
        "signal_audit": audit_signals,
        "policy_metrics": policy_metrics,
        "comparison": comparison,
        "intrabar_metadata": intrabar_metadata or {},
        "target_reached": is_target_reached,
        "evaluated_ratio": ratio
    }
    with open(reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.json", "w") as f:
        json.dump(summary_data, f, indent=2)

def generate_v1_21_1_reports(
    policy_metrics: dict[str, Any],
    comparison: dict[str, Any],
    audit_signals: dict[str, Any],
    ledger_audit: dict[str, Any],
    eval_audit: dict[str, Any],
    version: str = "v1_21_1",
    intrabar_metadata: dict[str, Any] | None = None,
    gap_analysis: dict[str, Any] | None = None,
):
    """Generate comprehensive research reports for V1.21.1 with gap-aware logic."""
    v_norm = version.replace(".", "_")
    reports_dir = Path("reports/research")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Coverage Analysis
    eval_count = sum(a.get('evaluated_count', 0) for a in eval_audit.values())
    total_count = sum(a.get('candidates_count', 1) for a in ledger_audit.values())
    ratio = eval_count / total_count if total_count > 0 else 0
    target_ratio = 0.20
    is_target_reached = ratio >= target_ratio
    
    # Gap info from analysis or metadata
    has_gaps = False
    if (gap_analysis and gap_analysis.get("gap_signals", 0) > 0) or \
       (intrabar_metadata and intrabar_metadata.get("gaps_count", 0) > 0):
        has_gaps = True

    # Adjust comparison validity
    if is_target_reached:
        if has_gaps:
            comparison['policy_comparison_valid'] = "preliminary_gap_aware"
            if comparison.get('verdict') == "TRADE_LEDGER_INTRABAR_SAMPLE_TOO_SHORT":
                comparison['verdict'] = "TRADE_LEDGER_PRELIMINARY_GAP_AWARE_COMPARISON_AVAILABLE"
            if comparison.get('all_negative'):
                comparison['verdict'] = "ALL_POLICIES_NEGATIVE_AFTER_COSTS_GAP_AWARE"
        else:
            comparison['policy_comparison_valid'] = "preliminary"
            if comparison.get('verdict') == "TRADE_LEDGER_INTRABAR_SAMPLE_TOO_SHORT":
                comparison['verdict'] = "TRADE_LEDGER_PRELIMINARY_COMPARISON_AVAILABLE"
            if comparison.get('all_negative'):
                comparison['verdict'] = "ALL_POLICIES_NEGATIVE_AFTER_COSTS"

    # 2. Evaluation Report
    with open(reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.md", "w") as f:
        f.write(f"# Trade Intrabar Evaluation - {version}\n\n")
        f.write(f"- **Evaluated Ratio**: {ratio:.2%} (Target: {target_ratio:.0%})\n")
        f.write(f"- **Target Reached**: {is_target_reached}\n")
        if has_gaps:
            f.write("- **Gap-Aware Status**: `REQUIRED` (Gaps detected)\n")
            if gap_analysis:
                f.write(f"- **Gap Impact**: `{gap_analysis.get('verdict')}`\n")
                gs = gap_analysis.get('gap_signals')
                gr = gap_analysis.get('gap_ratio')
                f.write(f"- **Signals in Gap**: {gs} ({gr:.2%})\n")
        f.write("\n")
        
        for p_name, audit in eval_audit.items():
            f.write(f"## Policy: {p_name}\n")
            f.write(f"- **Evaluated**: {audit.get('evaluated_count')}\n")
            f.write(f"- **Coverage Mean**: {audit.get('coverage_mean', 0.0):.2%}\n\n")

    # 3. Policy Comparison Report
    with open(reports_dir / f"trade_policy_comparison_{v_norm}.md", "w") as f:
        f.write(f"# Trade Policy Comparison - {version}\n\n")
        f.write(f"- **Verdict**: `{comparison.get('verdict')}`\n")
        f.write(f"- **Validity**: `{comparison.get('policy_comparison_valid')}`\n\n")
        
        f.write("| Policy | Win Rate | Mean PnL (AC) | Median PnL (AC) |\n")
        f.write("|---|---:|---:|---:|\n")
        for name, m in policy_metrics.items():
            wr = m.get('win_rate', 0.0)
            mn = m.get('mean_pnl_after_cost_pct', 0.0)
            md = m.get('median_pnl_after_cost_pct', 0.0)
            f.write(f"| {name} | {wr:.2%} | {mn:.4%} | {md:.4%} |\n")

    # 4. Recommendation
    if has_gaps:
        primary_reco = "Fill major gaps (e.g., 202 days in 2025) before stronger conclusions"
    else:
        primary_reco = "Extend to 50%" if is_target_reached else "Continue extension to 20%"
    
    reco_md = f"""# {version} Recommendation

- **Verdict**: `{comparison.get('verdict')}`
- **Coverage**: {ratio:.2%} (Target 20%: {'OK' if is_target_reached else 'KO'})
- **Gap-Aware**: {'YES' if has_gaps else 'NO'}
- **Ready for Reviewer**: `false`
- **Primary Recommendation**: {primary_reco}

**DO NOT**:
- Activate LLM Reviewer.
- Execute Holdout.
- Trade live.
"""
    with open(reports_dir / f"{v_norm}_recommendation.md", "w") as f:
        f.write(reco_md)

    reco_json = {
        "version": version,
        "verdict": comparison.get('verdict'),
        "ready_for_reviewer": False,
        "holdout": "not executed",
        "primary_recommendation": primary_reco,
        "gap_aware_required": has_gaps
    }
    with open(reports_dir / f"{v_norm}_recommendation.json", "w") as f:
        json.dump(reco_json, f, indent=2)
        
    # 5. Full Summary JSON
    summary_data = {
        "version": version,
        "signal_audit": audit_signals,
        "policy_metrics": policy_metrics,
        "comparison": comparison,
        "intrabar_metadata": intrabar_metadata or {},
        "gap_analysis": gap_analysis or {},
        "target_reached": is_target_reached,
        "evaluated_ratio": ratio,
        "continuous_backtest_valid": not has_gaps,
        "comparison_valid": comparison.get('policy_comparison_valid')
    }
    with open(reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.json", "w") as f:
        json.dump(summary_data, f, indent=2)

def generate_v1_21_2_reports(
    policy_metrics: dict[str, Any],
    comparison: dict[str, Any],
    audit_signals: dict[str, Any],
    ledger_audit: dict[str, Any],
    eval_audit: dict[str, Any],
    version: str = "v1_21_2",
    intrabar_metadata: dict[str, Any] | None = None,
    gap_analysis: dict[str, Any] | None = None,
):
    """Generate comprehensive research reports for V1.21.2 with candidate-aware gap metrics."""
    v_norm = version.replace(".", "_")
    reports_dir = Path("reports/research")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Coverage Analysis
    eval_count = sum(a.get('evaluated_count', 0) for a in eval_audit.values())
    total_count = sum(a.get('candidates_count', 1) for a in ledger_audit.values())
    ratio = eval_count / total_count if total_count > 0 else 0
    target_ratio = 0.20
    is_target_reached = ratio >= target_ratio
    
    # Gap info
    has_gaps = False
    if gap_analysis:
        unique_gap_ratio = gap_analysis.get("unique_signal_timestamps_gap_ratio", 0)
        if unique_gap_ratio > 0.01:
            has_gaps = True
    elif intrabar_metadata and intrabar_metadata.get("gaps_count", 0) > 0:
        has_gaps = True

    # Adjust comparison validity
    if is_target_reached:
        if has_gaps:
            comparison['policy_comparison_valid'] = "preliminary_gap_aware"
            verdict = comparison.get('verdict', '')
            if verdict in ["TRADE_LEDGER_INTRABAR_SAMPLE_TOO_SHORT", 
                          "ALL_POLICIES_NEGATIVE_AFTER_COSTS"]:
                comparison['verdict'] += "_GAP_AWARE"
            if comparison.get('all_negative') and "GAP_AWARE" not in comparison.get('verdict', ''):
                comparison['verdict'] = "ALL_POLICIES_NEGATIVE_AFTER_COSTS_GAP_AWARE"
        else:
            if comparison.get('policy_comparison_valid') != "preliminary_continuous":
                comparison['policy_comparison_valid'] = "preliminary"

    # 2. Evaluation Report
    with open(reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.md", "w") as f:
        f.write(f"# Trade Intrabar Evaluation - {version}\n\n")
        f.write(f"- **Evaluated Ratio**: {ratio:.2%} (Target: {target_ratio:.0%})\n")
        f.write(f"- **Target Reached**: {is_target_reached}\n")
        if has_gaps:
            f.write("- **Gap-Aware Status**: `REQUIRED`\n")
            if gap_analysis:
                f.write(f"- **Gap Impact**: `{gap_analysis.get('verdict')}`\n")
                uts_gap = gap_analysis.get('unique_signal_timestamps_in_gap')
                uts_ratio = gap_analysis.get('unique_signal_timestamps_gap_ratio')
                f.write(f"- **Unique Timestamps in Gap**: {uts_gap} ({uts_ratio:.2%})\n")
        f.write("\n")
        for p_name, audit in eval_audit.items():
            f.write(f"## Policy: {p_name}\n")
            f.write(f"- **Evaluated**: {audit.get('evaluated_count')}\n")
            f.write(f"- **Coverage Mean**: {audit.get('coverage_mean', 0.0):.2%}\n\n")

    # 3. Policy Comparison Report (MD + JSON)
    best_policy = comparison.get('best_policy')
    all_negative = comparison.get('all_negative', True)
    all_median_negative = all(
        m.get('median_pnl_after_cost_pct', 0) < 0 for m in policy_metrics.values()
    )
    
    comparison_json = {
        "version": version,
        "verdict": comparison.get('verdict'),
        "policy_comparison_valid": comparison.get('policy_comparison_valid'),
        "continuous_backtest_valid": not has_gaps,
        "gap_aware_required": has_gaps,
        "evaluated_ratio": ratio,
        "target_reached": is_target_reached,
        "best_policy": best_policy,
        "all_negative": all_negative,
        "all_median_negative": all_median_negative,
        "warnings": comparison.get('warnings', []),
        "policy_metrics_summary": {
            name: {
                "win_rate": m.get('win_rate'),
                "mean_pnl_ac": m.get('mean_pnl_after_cost_pct'),
                "median_pnl_ac": m.get('median_pnl_after_cost_pct')
            } for name, m in policy_metrics.items()
        }
    }
    with open(reports_dir / f"trade_policy_comparison_{v_norm}.json", "w") as f:
        json.dump(comparison_json, f, indent=2)

    with open(reports_dir / f"trade_policy_comparison_{v_norm}.md", "w") as f:
        f.write(f"# Trade Policy Comparison - {version}\n\n")
        f.write(f"- **Verdict**: `{comparison.get('verdict')}`\n")
        f.write(f"- **Validity**: `{comparison.get('policy_comparison_valid')}`\n")
        f.write(f"- **Continuous Backtest Valid**: {not has_gaps}\n\n")
        
        f.write("| Policy | Win Rate | Mean PnL (AC) | Median PnL (AC) |\n")
        f.write("|---|---:|---:|---:|\n")
        for name, m in policy_metrics.items():
            wr = m.get('win_rate', 0.0)
            mn = m.get('mean_pnl_after_cost_pct', 0.0)
            md = m.get('median_pnl_after_cost_pct', 0.0)
            f.write(f"| {name} | {wr:.2%} | {mn:.4%} | {md:.4%} |\n")

    # 4. Recommendation
    if has_gaps:
        primary_reco = "Fill major gaps before stronger conclusions"
    else:
        primary_reco = "Continue expansion"
    reco_json = {
        "version": version,
        "verdict": comparison.get('verdict'),
        "ready_for_reviewer": False,
        "holdout": "not executed",
        "primary_recommendation": primary_reco,
        "gap_aware_required": has_gaps
    }
    with open(reports_dir / f"{v_norm}_recommendation.json", "w") as f:
        json.dump(reco_json, f, indent=2)

    reco_md = f"""# {version} Recommendation
- **Verdict**: `{comparison.get('verdict')}`
- **Gap-Aware**: {'YES' if has_gaps else 'NO'}
- **Ready for Reviewer**: `false`
- **Primary Recommendation**: {primary_reco}
"""
    with open(reports_dir / f"{v_norm}_recommendation.md", "w") as f:
        f.write(reco_md)
        
    # 5. Full Summary JSON
    summary_data = {
        "version": version,
        "signal_audit": audit_signals,
        "policy_metrics": policy_metrics,
        "comparison": comparison,
        "intrabar_metadata": intrabar_metadata or {},
        "gap_analysis": gap_analysis or {},
        "target_reached": is_target_reached,
        "evaluated_ratio": ratio,
        "continuous_backtest_valid": not has_gaps,
        "comparison_valid": comparison.get('policy_comparison_valid'),
        "ready_for_reviewer": False
    }
    with open(reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.json", "w") as f:
        json.dump(summary_data, f, indent=2)
def generate_v1_21_5_reports(
    policy_metrics: dict[str, Any],
    comparison: dict[str, Any],
    audit_signals: dict[str, Any],
    ledger_audit: dict[str, Any],
    eval_audit: dict[str, Any],
    version: str = "v1_21_5",
    intrabar_metadata: dict[str, Any] | None = None,
    gap_analysis: dict[str, Any] | None = None,
):
    """Generate comprehensive research reports for V1.21.5."""
    # Enforce gap-aware logic strictly for V1.21.5
    has_gaps = False
    if gap_analysis:
        unique_gap_ratio = gap_analysis.get("unique_signal_timestamps_gap_ratio", 0)
        if unique_gap_ratio > 0:
            has_gaps = True
    elif intrabar_metadata and intrabar_metadata.get("gaps_count", 0) > 0:
        has_gaps = True

    if has_gaps:
        comparison['policy_comparison_valid'] = "preliminary_gap_aware"
        verdict = comparison.get('verdict', '')
        if "GAP_AWARE" not in verdict:
             if verdict == "ALL_POLICIES_NEGATIVE_AFTER_COSTS":
                 comparison['verdict'] = "ALL_POLICIES_NEGATIVE_AFTER_COSTS_GAP_AWARE"
             else:
                 comparison['verdict'] += "_GAP_AWARE"
    
    generate_v1_21_2_reports(
        policy_metrics=policy_metrics,
        comparison=comparison,
        audit_signals=audit_signals,
        ledger_audit=ledger_audit,
        eval_audit=eval_audit,
        version=version,
        intrabar_metadata=intrabar_metadata,
        gap_analysis=gap_analysis
    )

def generate_v1_22_reports(
    policy_metrics: dict[str, Any],
    comparison: dict[str, Any],
    audit_signals: dict[str, Any],
    ledger_audit: dict[str, Any],
    eval_audit: dict[str, Any],
    version: str = "v1_22",
    intrabar_metadata: dict[str, Any] | None = None,
    gap_analysis: dict[str, Any] | None = None,
):
    """Generate comprehensive research reports for V1.22."""
    # Check for gaps
    has_gaps = False
    if gap_analysis:
        # Check if any candidates or signals remain in gaps
        gap_ratio = gap_analysis.get("trade_candidates_gap_ratio", 0)
        if gap_ratio > 0.01: # 1% threshold for "gap-aware" requirement
            has_gaps = True
    elif intrabar_metadata and intrabar_metadata.get("gaps_count", 0) > 0:
        has_gaps = True

    if has_gaps:
        comparison['policy_comparison_valid'] = "preliminary_gap_aware"
        verdict = comparison.get('verdict', '')
        if "GAP_AWARE" not in verdict:
             if verdict == "ALL_POLICIES_NEGATIVE_AFTER_COSTS":
                 comparison['verdict'] = "ALL_POLICIES_NEGATIVE_AFTER_COSTS_GAP_AWARE"
             else:
                 comparison['verdict'] += "_GAP_AWARE"
    else:
        # Gap filled!
        comparison['policy_comparison_valid'] = "preliminary_continuous"
        if comparison.get('all_negative'):
            comparison['verdict'] = "ALL_POLICIES_NEGATIVE_AFTER_COSTS_CONTINUOUS"

    generate_v1_21_2_reports(
        policy_metrics=policy_metrics,
        comparison=comparison,
        audit_signals=audit_signals,
        ledger_audit=ledger_audit,
        eval_audit=eval_audit,
        version=version,
        intrabar_metadata=intrabar_metadata,
        gap_analysis=gap_analysis
    )
    
    # Re-enforce validity after the sub-call
    if not has_gaps:
        v_norm = version.replace(".", "_")
        json_path = Path("reports/research") / f"trade_ledger_intrabar_eval_{v_norm}.json"
        if json_path.exists():
            with open(json_path) as f:
                data = json.load(f)
            data["comparison_valid"] = "preliminary_continuous"
            data["continuous_backtest_valid"] = True
            with open(json_path, "w") as f:
                json.dump(data, f, indent=2)
def generate_v1_22_1_reports(
    policy_metrics: dict[str, Any],
    comparison: dict[str, Any],
    audit_signals: dict[str, Any],
    ledger_audit: dict[str, Any],
    eval_audit: dict[str, Any],
    version: str = "v1_22_1",
    intrabar_metadata: dict[str, Any] | None = None,
    gap_analysis: dict[str, Any] | None = None,
):
    """Generate comprehensive research reports for V1.22.1."""
    # Check for gaps
    has_gaps = False
    if gap_analysis:
        gap_ratio = gap_analysis.get("trade_candidates_gap_ratio", 0)
        if gap_ratio > 0.001: 
            has_gaps = True
    elif intrabar_metadata and intrabar_metadata.get("gaps_count", 0) > 0:
        has_gaps = True

    if has_gaps:
        comparison['policy_comparison_valid'] = "preliminary_gap_aware"
    else:
        comparison['policy_comparison_valid'] = "preliminary_continuous"
        if comparison.get('all_negative'):
            comparison['verdict'] = "ALL_POLICIES_NEGATIVE_AFTER_COSTS_CONTINUOUS"

    generate_v1_21_2_reports(
        policy_metrics=policy_metrics,
        comparison=comparison,
        audit_signals=audit_signals,
        ledger_audit=ledger_audit,
        eval_audit=eval_audit,
        version=version,
        intrabar_metadata=intrabar_metadata,
        gap_analysis=gap_analysis
    )
    
    # Enforce validity in JSON
    v_norm = version.replace(".", "_")
    reports_dir = Path("reports/research")
    json_path = reports_dir / f"trade_ledger_intrabar_eval_{v_norm}.json"
    if json_path.exists():
        with open(json_path) as f:
            data = json.load(f)
        data["comparison_valid"] = comparison['policy_comparison_valid']
        data["continuous_backtest_valid"] = not has_gaps
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)

    # Update Recommendation specifically for V1.22.1
    reco_json_path = reports_dir / f"{v_norm}_recommendation.json"
    reco_md_path = reports_dir / f"{v_norm}_recommendation.md"
    
    primary_reco = "Run loss attribution on continuous intrabar dataset."
    reco_payload = {
        "version": version,
        "primary_recommendation": primary_reco,
        "secondary_recommendations": [
            "Analyze why all policies remain negative after costs.",
            "Compare entry quality, exits, costs, holding duration, regimes.",
            "Do not activate LLM reviewer.",
            "Do not execute holdout.",
            "Do not trade live."
        ],
        "ready_for_reviewer": False,
        "holdout_executed": False,
        "no_real_trading": True,
        "verdict": comparison.get("verdict")
    }
    with open(reco_json_path, "w") as f:
        json.dump(reco_payload, f, indent=2)
        
    reco_md = f"""# {version} Recommendation
1. **Primary**: {primary_reco}
2. **Analysis**: Why all policies remain negative after costs?
3. **Reviewer**: DO NOT activate.
4. **Holdout**: DO NOT execute.
5. **Real Trading**: DO NOT trade live.
"""
    reco_md_path.write_text(reco_md)
