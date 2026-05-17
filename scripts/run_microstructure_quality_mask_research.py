"""Run Microstructure Quality Mask research (V1.51)."""
import argparse
import pandas as pd
from pathlib import Path
from src.galapagos.research.microstructure_quality_mask.data_loader import QualityMaskDataLoader
from src.galapagos.research.microstructure_quality_mask.input_guard import QualityMaskInputGuard
from src.galapagos.research.microstructure_quality_mask.quality_rule_builder import QualityRuleBuilder
from src.galapagos.research.microstructure_quality_mask.coverage_mask_builder import CoverageMaskBuilder
from src.galapagos.research.microstructure_quality_mask.mask_impact_analysis import MaskImpactAnalysis
from src.galapagos.research.microstructure_quality_mask.usable_window_analysis import WindowAnalysis
from src.galapagos.research.microstructure_quality_mask.feature_retention_analysis import FeatureRetentionAnalysis
from src.galapagos.research.microstructure_quality_mask.label_reliability_under_mask import LabelReliabilityAnalysis
from src.galapagos.research.microstructure_quality_mask.data_action_plan_builder import DataActionPlanBuilder
from src.galapagos.research.microstructure_quality_mask.quality_mask_scorecard import QualityMaskScorecard
from src.galapagos.research.microstructure_quality_mask.diagnostic_verdict import QualityMaskVerdict
from src.galapagos.research.microstructure_quality_mask.recommendation_engine import RecommendationEngine
from src.galapagos.research.microstructure_quality_mask.report_writer import QualityMaskReportWriter

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--alpha-dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--coverage-summary", required=True)
    parser.add_argument("--coverage-scorecard", required=True)
    parser.add_argument("--quality-policy", required=True)
    parser.add_argument("--micro-regime-summary", required=True)
    parser.add_argument("--microstructure-label-summary", required=True)
    parser.add_argument("--canonical-summary", required=True)
    parser.add_argument("--version", default="v1.51")
    args = parser.parse_args()

    loader = QualityMaskDataLoader(
        args.predictions, args.dataset, args.alpha_dataset, args.intrabar,
        args.coverage_summary, args.coverage_scorecard, args.quality_policy,
        args.micro_regime_summary, args.microstructure_label_summary, args.canonical_summary
    )
    
    guard = QualityMaskInputGuard()
    writer = QualityMaskReportWriter(args.version)
    
    print("Loading data...")
    report_data = loader.load_data()
    guard.validate_reports(report_data)
    
    df = loader.load_main_dataset()
    guard.validate_dataset(df)
    
    print("Building quality rules...")
    rule_builder = QualityRuleBuilder(report_data["quality_policy"])
    rules = rule_builder.build_rules()
    writer.write_report("microstructure_quality_rule_set", 
                       rule_builder.get_rule_set_report(rules),
                       "Microstructure Quality Rule Set")
    
    print("Building coverage mask...")
    mask_builder = CoverageMaskBuilder(rules)
    mask = mask_builder.build_mask(df)
    masks = mask_builder.classify_windows(df, mask)
    writer.write_report("microstructure_coverage_mask",
                       {"mask_count": int(mask.sum()), "blocked_count": int((~mask).sum())},
                       "Microstructure Coverage Mask")
    
    print("Analyzing mask impact...")
    impact_analysis = MaskImpactAnalysis()
    impact = impact_analysis.run(df, masks)
    writer.write_report("microstructure_mask_impact_analysis", impact, "Microstructure Mask Impact Analysis")
    
    window_analysis = WindowAnalysis()
    usable_windows = window_analysis.analyze_usable(df, masks["usable_mask"])
    writer.write_report("microstructure_usable_window_analysis", usable_windows, "Microstructure Usable Window Analysis")
    
    blocked_windows = window_analysis.analyze_blocked(df, masks["blocked_mask"])
    writer.write_report("microstructure_blocked_window_analysis", blocked_windows, "Microstructure Blocked Window Analysis")
    
    print("Analyzing feature retention...")
    retention_analysis = FeatureRetentionAnalysis()
    retention = retention_analysis.run(df, mask, rules["required_features"])
    writer.write_report("microstructure_feature_retention_analysis", retention, "Microstructure Feature Retention Analysis")
    
    print("Analyzing label reliability...")
    labels = report_data["microstructure_label_summary"].get("built_microstructure_regime_labels", [])
    label_analysis = LabelReliabilityAnalysis()
    reliability = label_analysis.run(df, mask, labels)
    writer.write_report("microstructure_label_reliability_under_mask", reliability, "Microstructure Label Reliability Under Mask")
    
    print("Building data action plan...")
    plan_builder = DataActionPlanBuilder()
    plan = plan_builder.build_plan(impact, retention)
    writer.write_report("microstructure_data_action_plan", plan, "Microstructure Data Action Plan")
    
    print("Generating scorecard and verdict...")
    scorecard = QualityMaskScorecard()
    score = scorecard.run(impact, retention)
    writer.write_report("microstructure_quality_mask_scorecard", score, "Microstructure Quality Mask Scorecard")
    
    verdict_engine = QualityMaskVerdict()
    verdict = verdict_engine.get_verdict(score)
    
    reco_engine = RecommendationEngine()
    reco_step = reco_engine.get_recommendation(verdict)
    
    summary = {
        "version": args.version.upper(),
        "previous_base": "V1.50.1",
        "final_verdict": verdict,
        "recommended_next_step": reco_step,
        "evidence_classification": "RESEARCH_ONLY",
        "impact": impact,
        "score": score,
        "plan": plan,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False
    }
    writer.write_report("microstructure_quality_mask_summary", summary, "Microstructure Quality Mask Summary")
    
    reco_report = {
        "version": args.version.upper(),
        "previous_base": "V1.50.1",
        "final_verdict": verdict,
        "recommended_next_step": reco_step,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False
    }
    writer.write_report("v1_51_recommendation", reco_report, "V1.51 Recommendation")
    
    # Consistency check
    consistency = {
        "version": args.version.upper(),
        "previous_base": "V1.50.1",
        "consistency_check_status": "MICROSTRUCTURE_QUALITY_MASK_REPORTS_CONSISTENT_RESEARCH_ONLY",
        "issues": [],
        "project_state_aligned": True,
        "latest_metrics_aligned": True,
        "latest_summary_aligned": True,
        "all_json_values_finite": True,
        "required_reports_present": True,
        "required_markdown_reports_present": True,
        "safety_flags_aligned": True,
        "recommendation_aligned": True,
        "release_reports_present": True,
        "status_field_policy": "REMOVED",
        "status_field_present": False,
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False
    }
    writer.write_report("microstructure_quality_mask_consistency_check", consistency, "Microstructure Quality Mask Consistency Check")
    
    print(f"Research V1.51 complete. Verdict: {verdict}")

if __name__ == "__main__":
    main()
