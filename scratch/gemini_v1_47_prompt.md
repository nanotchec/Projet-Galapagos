Implement Galapagos V1.47: Microstructure Regime Feature Enrichment Research.

Goal: RESEARCH_ONLY / DIAGNOSTIC_ONLY. No strategy validation, no paper live, no preregistration, no real trading, no holdout, no new tradable filter.

Use only real data and causal features. Build and audit microstructure proxies available from the current datasets, assess coverage, missingness, stability, causal availability, and relevance to regime labels. Identify which microstructure proxies to keep / rework / reject. Do not invent unavailable features; list them with reasons.

Requirements:
- Create package src/galapagos/research/microstructure_regime_features/ with loaders, input guard, feature builder, inventory, causal availability, coverage, missingness, stability, regime relevance, quality scorecard, recommendation engine, verdict, report writer.
- Create scripts/run_microstructure_regime_feature_research.py and scripts/validate_microstructure_regime_feature_reports.py.
- Produce JSON+MD reports for input guard, feature inventory/build, causal audit, coverage, missingness, stability, regime relevance, scorecard, recommendation, summary, consistency check, recommendation, docs.
- Update PROJECT_STATE, latest_metrics, latest_summary, implementation_report, REPORT_INDEX.
- Ensure consistency check has issues = [], project_state/latest_metrics/latest_summary aligned, all_json_values_finite = true, required reports present, safety flags aligned, recommendation aligned, release reports present, status_field_policy = REMOVED, status_field_present = false.
- Versioning: V1.47, previous_base = V1.46.3, canonical base V1.37.2, regime data quality base V1.46.3, feature ablation base V1.45.1.
- Canonical recommendation: high_priority_enrichment_gaps and recommended_feature_gaps_high_priority must be ["microstructure"], recommended_data_enrichment_next = "improve microstructure regime features", recommended_next_research_step and recommended_next_step = "improve data enrichment / regime labels before new modeling".
- Final verdict must be one of the allowed non-validated research verdicts and must not mention validation, preregistration, paper live, or real trading.
- Add tests for causal availability, validator, NaN/Infinity rejection, forbidden outcomes/model outputs/EV proxies, and safety flags.
- Run pytest on relevant tests, ruff if available, validate reports, release clean zip, audit, smoke test.
- Produce projet-galapagos-v1.47-clean.zip.

Do not use mocks/scratch/devnull for final results. Keep code in English, docs/reports in French.
