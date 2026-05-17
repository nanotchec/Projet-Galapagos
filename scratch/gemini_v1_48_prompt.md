Tu travailles dans /Users/lilianserre/Documents/projets/projet-galapagos.

Mission: implémenter Galapagos V1.48: Integrate Microstructure Proxies into Regime Label Diagnostics.

Contexte à préserver:
- V1.47 est validée.
- état validé: version V1.47, previous_base V1.46.3, regime_data_quality_base_version V1.46.3, feature_ablation_base_version V1.45.1, canonical_base_version V1.37.2.
- final_verdict = MICROSTRUCTURE_REGIME_FEATURES_ACTIONABLE_BUT_UNVALIDATED.
- evidence_classification = RESEARCH_ONLY.
- consistency_check_status = MICROSTRUCTURE_REGIME_FEATURE_REPORTS_CONSISTENT_RESEARCH_ONLY.
- built_microstructure_features = [amihud_illiquidity, intraday_range, realized_vol_proxy, volume_vol_ratio].
- best_microstructure_candidates = [amihud_illiquidity, realized_vol_proxy].
- weak_microstructure_candidates = [intraday_range, volume_vol_ratio].
- recommended_keep_for_next_research = [amihud_illiquidity, realized_vol_proxy].
- recommended_rework = [intraday_range, volume_vol_ratio].
- recommended_next_step = improve data enrichment / regime labels before new modeling.
- recommended_data_enrichment_next = improve microstructure regime features.
- no_new_filter = true, no_strategy_validated = true, no_preregistration_yet = true, no_paper_live = true, no_real_trading = true, holdout_executed = false, codex_cli_called = false.

Goal V1.48:
- Create a RESEARCH_ONLY / DIAGNOSTIC_ONLY phase that integrates the two best microstructure proxies from V1.47 (amihud_illiquidity and realized_vol_proxy) into regime label diagnostics.
- Build enriched regime labels only causally.
- Compare enriched labels versus V1.46/V1.43 labels.
- Measure separability, stability, 2026 drift, relevance to losses/regimes.
- Produce a research recommendation. No tradable strategy.

Hard constraints:
- No real order, no paper live, no preregistration, no holdout, no Codex CLI, no network, no model validation, no invented results.
- Evidence classification must remain RESEARCH_ONLY or DIAGNOSTIC_ONLY.
- Zip must be clean and final name must be projet-galapagos-v1.48-clean.zip.

Required work:
1) Create package src/galapagos/research/microstructure_regime_labels/ with the specified modules.
2) Create scripts run_microstructure_regime_label_research.py and validate_microstructure_regime_label_reports.py.
3) Create all V1.48 JSON+MD reports listed below.
4) Create docs/microstructure_regime_label_research_v1_48.md.
5) Update reports/PROJECT_STATE.json, reports/PROJECT_STATE.md, reports/current/latest_metrics.json, reports/current/latest_summary.md, reports/implementation_report.md, reports/REPORT_INDEX.md.
6) Update packaging scripts if necessary.
7) Add tests covering causal availability, global lookahead rejection, validation guards, and no real trading.
8) Run pytest for microstructure_regime_labels and validators, ruff if available, validate report generator, then release_clean_zip --version v1.48.

Reports to create in JSON and MD:
- microstructure_regime_label_input_guard_v1_48
- microstructure_proxy_load_report_v1_48
- microstructure_regime_label_build_report_v1_48
- microstructure_enriched_label_inventory_v1_48
- microstructure_label_quality_comparison_v1_48
- microstructure_separability_comparison_v1_48
- microstructure_stability_comparison_v1_48
- microstructure_transition_comparison_v1_48
- microstructure_drift_2026_analysis_v1_48
- microstructure_loss_slice_relevance_v1_48
- microstructure_label_causal_availability_audit_v1_48
- microstructure_regime_label_recommendation_v1_48
- microstructure_regime_label_summary_v1_48
- microstructure_regime_label_consistency_check_v1_48
- v1_48_recommendation

Required summary fields:
- version = V1.48
- previous_base = V1.47
- microstructure_feature_base_version = V1.47
- regime_data_quality_base_version = V1.46.3
- canonical_base_version = V1.37.2
- all status fields for the new reports
- built_microstructure_regime_labels
- unavailable_microstructure_regime_labels
- best_microstructure_regime_labels
- weak_microstructure_regime_labels
- improves_over_v1_46_labels
- improves_stability_2026
- improves_separability_2026
- final_verdict in {MICROSTRUCTURE_REGIME_LABELS_ACTIONABLE_BUT_UNVALIDATED, MICROSTRUCTURE_REGIME_LABELS_INCONCLUSIVE, MICROSTRUCTURE_REGIME_LABELS_WEAK, MICROSTRUCTURE_REGIME_LABELS_BLOCKED_BY_CAUSALITY}
- recommended_next_step must stay exploratory only and must not mention preregistration, paper live, or real trading.
- recommendation alignment fields must match across summary / PROJECT_STATE / latest / recommendation.

Consistency check must include:
- version = V1.48
- previous_base = V1.47
- issues = []
- project_state_aligned = true
- latest_metrics_aligned = true
- latest_summary_aligned = true
- all_json_values_finite = true
- required_reports_present = true
- required_markdown_reports_present = true
- safety_flags_aligned = true
- recommendation_aligned = true
- release_reports_present = true
- status_field_policy = REMOVED
- status_field_present = false
- consistency_check_status = MICROSTRUCTURE_REGIME_LABEL_REPORTS_CONSISTENT_RESEARCH_ONLY

Use only causal, available data. Do not use outcomes, forward returns, MFE/MAE, targets, model outputs, EV proxies, or global lookahead thresholds.

Return a concise summary of what you changed and confirm no strategy validation, no paper live, no preregistration, no holdout, no real trading, no Codex CLI.
