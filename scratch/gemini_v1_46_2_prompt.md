Implement Galapagos V1.46.2 in /Users/lilianserre/Documents/projets/projet-galapagos.

Goal: fix the regime data quality consistency/reporting state only, without rerunning research.

Must produce V1.46.2 reports and updates:
- reports/research/regime_data_quality_consistency_check_v1_46_2.json/md must include:
  version=V1.46.2, previous_base=V1.46.1, consistency_check_status=REGIME_DATA_QUALITY_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY, issues=[], project_state_aligned=true, latest_metrics_aligned=true, latest_summary_aligned=true, all_json_values_finite=true, required_reports_present=true, required_markdown_reports_present=true, safety_flags_aligned=true, recommendation_aligned=true, release_reports_present=true, status_field_policy=REMOVED, status_field_present=false, no_new_filter=true, no_strategy_validated=true, no_preregistration_yet=true, no_paper_live=true, no_real_trading=true, holdout_executed=false, codex_cli_called=false.
- Update reports/PROJECT_STATE.json/md and reports/current/latest_metrics.json/latest_summary.md to V1.46.2, previous_base=V1.46.1, and align with the same flags.
- Update reports/research/regime_data_quality_summary_v1_46_2.json/md, v1_46_2_recommendation.json/md, docs/regime_data_quality_research_v1_46_2.md.
- Harden scripts/validate_regime_data_quality_reports.py so it rejects minimal consistency checks and requires all fields above.
- Regenerate clean zip, audit, smoke: projet-galapagos-v1.46.2-clean.zip.

Constraints:
- No new research.
- No strategy validation.
- No paper live.
- No preregistration.
- No real trading.
- No holdout.
- No Codex CLI.
- No network.
- Keep scientific results unchanged from V1.46 / V1.46.1 except reporting/state fixes.

Return only the actual implementation, updated reports, tests, and clean release artifacts.
