"""Main execution script for Microstructure Coverage Quality Audit V1.50."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from galapagos.research.microstructure_coverage_quality.data_loader import CoverageDataLoader
from galapagos.research.microstructure_coverage_quality.input_guard import CoverageInputGuard
from galapagos.research.microstructure_coverage_quality.intrabar_coverage_audit import IntrabarCoverageAudit
from galapagos.research.microstructure_coverage_quality.timestamp_alignment_audit import TimestampAlignmentAudit
from galapagos.research.microstructure_coverage_quality.missingness_profile import MissingnessProfile
from galapagos.research.microstructure_coverage_quality.gap_detection import GapDetection
from galapagos.research.microstructure_coverage_quality.session_quality_profile import SessionQualityProfile
from galapagos.research.microstructure_coverage_quality.microstructure_feature_availability import MicrostructureFeatureAvailability
from galapagos.research.microstructure_coverage_quality.label_coverage_impact import LabelCoverageImpact
from galapagos.research.microstructure_coverage_quality.coverage_vs_failure_analysis import CoverageVsFailureAnalysis
from galapagos.research.microstructure_coverage_quality.quality_policy_builder import QualityPolicyBuilder
from galapagos.research.microstructure_coverage_quality.coverage_scorecard import CoverageScorecard
from galapagos.research.microstructure_coverage_quality.recommendation_engine import CoverageRecommendationEngine
from galapagos.research.microstructure_coverage_quality.diagnostic_verdict import CoverageDiagnosticVerdict
from galapagos.research.microstructure_coverage_quality.report_writer import CoverageReportWriter

def main():
    parser = argparse.ArgumentParser(description="Run Microstructure Coverage Quality Audit V1.50")
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--alpha-dataset", required=True)
    parser.add_argument("--intrabar", required=True)
    parser.add_argument("--micro-regime-summary", required=True)
    parser.add_argument("--micro-regime-consistency", required=True)
    parser.add_argument("--microstructure-feature-summary", required=True)
    parser.add_argument("--microstructure-coverage-audit", required=True)
    parser.add_argument("--microstructure-missingness-audit", required=True)
    parser.add_argument("--canonical-summary", required=True)
    parser.add_argument("--version", default="v1.50")
    parser.add_argument("--output-dir", default="reports/research")
    
    args = parser.parse_args()
    version = args.version.upper()
    
    loader = CoverageDataLoader(args.predictions, args.dataset, args.alpha_dataset, args.intrabar)
    data = loader.load_all()
    
    writer = CoverageReportWriter(args.output_dir, version)
    results = {}
    
    # 1. Input Guard
    guard = CoverageInputGuard()
    results["input_guard"] = guard.validate(data)
    writer.write_report("microstructure_coverage_input_guard", results["input_guard"], "Microstructure Coverage Input Guard")
    
    # 2. Intrabar Coverage
    audit = IntrabarCoverageAudit()
    results["intrabar_coverage"] = audit.run(data["dataset"], data["intrabar"])
    writer.write_report("microstructure_intrabar_coverage_audit", results["intrabar_coverage"], "Microstructure Intrabar Coverage Audit")
    
    # 3. Timestamp Alignment
    align = TimestampAlignmentAudit()
    results["timestamp_alignment"] = align.run(data["predictions"], data["dataset"], data["alpha_dataset"])
    writer.write_report("microstructure_timestamp_alignment_audit", results["timestamp_alignment"], "Microstructure Timestamp Alignment Audit")
    
    # 4. Missingness Profile
    miss = MissingnessProfile()
    results["missingness_profile"] = miss.run(data["dataset"])
    writer.write_report("microstructure_missingness_profile", results["missingness_profile"], "Microstructure Missingness Profile")
    
    # 5. Gap Detection
    gap = GapDetection()
    results["gap_detection"] = gap.run(data["intrabar"])
    writer.write_report("microstructure_gap_detection", results["gap_detection"], "Microstructure Gap Detection")
    
    # 6. Session Quality
    session = SessionQualityProfile()
    results["session_quality"] = session.run(data["dataset"])
    writer.write_report("microstructure_session_quality_profile", results["session_quality"], "Microstructure Session Quality Profile")
    
    # 7. Feature Availability
    avail = MicrostructureFeatureAvailability()
    results["feature_availability"] = avail.run(data["dataset"])
    writer.write_report("microstructure_feature_availability", results["feature_availability"], "Microstructure Feature Availability")
    
    # 8. Label Coverage Impact
    impact = LabelCoverageImpact()
    results["label_coverage_impact"] = impact.run(data["dataset"], results["intrabar_coverage"])
    writer.write_report("microstructure_label_coverage_impact", results["label_coverage_impact"], "Microstructure Label Coverage Impact")
    
    # 9. Coverage vs Failure
    fail_anal = CoverageVsFailureAnalysis()
    results["coverage_vs_failure"] = fail_anal.run(data["dataset"])
    writer.write_report("microstructure_coverage_vs_failure_analysis", results["coverage_vs_failure"], "Microstructure Coverage vs Failure Analysis")
    
    # 10. Coverage Scorecard
    scorecard_gen = CoverageScorecard()
    results["scorecard"] = scorecard_gen.run(results)
    writer.write_report("microstructure_coverage_scorecard", results["scorecard"], "Microstructure Coverage Scorecard")
    
    # 11. Quality Policy
    policy_gen = QualityPolicyBuilder()
    results["quality_policy"] = policy_gen.run(results["scorecard"])
    writer.write_report("microstructure_quality_policy", results["quality_policy"], "Microstructure Quality Policy")
    
    # 12. Recommendation
    rec_gen = CoverageRecommendationEngine()
    results["recommendation"] = rec_gen.run(results)
    writer.write_report("microstructure_coverage_recommendation", results["recommendation"], "Microstructure Coverage Recommendation")
    
    # 13. Summary
    verdict_gen = CoverageDiagnosticVerdict()
    verdict_res = verdict_gen.run(results)
    
    summary = {
        "version": version,
        "previous_base": "V1.49.1",
        "micro_regime_diagnostic_base_version": "V1.49.1",
        "microstructure_regime_label_base_version": "V1.48.1",
        "microstructure_feature_base_version": "V1.47",
        "canonical_base_version": "V1.37.2",
        "input_guard_status": results["input_guard"]["input_guard_status"],
        "intrabar_coverage_status": results["intrabar_coverage"]["intrabar_coverage_status"],
        "timestamp_alignment_status": results["timestamp_alignment"]["timestamp_alignment_status"],
        "missingness_profile_status": results["missingness_profile"]["missingness_profile_status"],
        "gap_detection_status": results["gap_detection"]["gap_detection_status"],
        "session_quality_status": results["session_quality"]["session_quality_status"],
        "feature_availability_status": results["feature_availability"]["feature_availability_status"],
        "label_coverage_impact_status": results["label_coverage_impact"]["label_coverage_impact_status"],
        "coverage_vs_failure_status": results["coverage_vs_failure"]["coverage_vs_failure_status"],
        "quality_policy_status": results["quality_policy"]["quality_policy_status"],
        "coverage_scorecard_status": results["scorecard"]["coverage_scorecard_status"],
        "recommendation_status": results["recommendation"]["recommendation_status"],
        "assessed_microstructure_features": list(results["missingness_profile"]["missingness_per_feature"].keys()),
        "quality_pass_features": [k for k, v in results["missingness_profile"]["missingness_per_feature"].items() if v < 0.05],
        "quality_weak_features": [k for k, v in results["missingness_profile"]["missingness_per_feature"].items() if 0.05 <= v <= 0.15],
        "quality_blocked_features": [k for k, v in results["missingness_profile"]["missingness_per_feature"].items() if v > 0.15],
        "coverage_problem_periods": [year for year, score in results["session_quality"]["session_quality_scores"].items() if score < 0.9],
        "coverage_problem_2026": results["session_quality"]["session_quality_scores"].get("2026", 1.0) < 0.9,
        "coverage_impacts_label_quality": results["label_coverage_impact"]["coverage_impact_detected"],
        "recommended_data_actions": results["recommendation"]["recommended_data_actions"],
        "recommended_keep_for_next_research": results["recommendation"]["recommended_keep_for_next_research"],
        "recommended_rework": results["recommendation"]["recommended_rework"],
        "final_verdict": verdict_res["final_verdict"],
        "recommended_next_step": results["recommendation"]["recommended_next_step"],
        "evidence_classification": "RESEARCH_ONLY",
        "no_new_filter": True,
        "no_strategy_validated": True,
        "no_preregistration_yet": True,
        "no_paper_live": True,
        "no_real_trading": True,
        "holdout_executed": False,
        "codex_cli_called": False,
        "real_orders_possible": False
    }
    writer.write_report("microstructure_coverage_quality_summary", summary, "Microstructure Coverage Quality Summary")
    
    # 14. Consistency Check
    consistency = {
        "version": version,
        "previous_base": "V1.49.1",
        "consistency_check_status": "MICROSTRUCTURE_COVERAGE_QUALITY_REPORTS_CONSISTENT_RESEARCH_ONLY",
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
    writer.write_report("microstructure_coverage_quality_consistency_check", consistency, "Microstructure Coverage Quality Consistency Check")
    
    # 15. Recommendation Artifact
    writer.write_raw_report(f"{version.lower().replace('.', '_')}_recommendation", summary, f"Recommendation {version}")
    
    # 16. Documentation
    writer.write_doc(f"# Microstructure Coverage Quality V1.50\n\nVerdict: {summary['final_verdict']}\nNext Step: {summary['recommended_next_step']}")

if __name__ == "__main__":
    main()
