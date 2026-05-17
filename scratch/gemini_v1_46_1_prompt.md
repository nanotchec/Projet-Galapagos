Implement Galapagos V1.46.1 as a reporting/state hardening pass only.

Scope:
- migrate V1.46 to V1.46.1;
- harden `reports/research/regime_data_quality_consistency_check_v1_46_1.json/md` with explicit fields:
  `issues = []`, `project_state_aligned = true`, `latest_metrics_aligned = true`, `latest_summary_aligned = true`, `all_json_values_finite = true`, `status_field_policy = REMOVED`, `status_field_present = false`, `required_reports_present = true`, `safety_flags_aligned = true`, `recommendation_aligned = true`, `release_reports_present = true`;
- update `reports/PROJECT_STATE.json/md` and `reports/current/latest_metrics.json/md` to V1.46.1 with the same scientific verdict as V1.46;
- update `reports/research/v1_46_1_recommendation.json/md` and `docs/regime_data_quality_research_v1_46_1.md`;
- rerun validator and clean zip release for `v1.46.1`.

Do not change scientific results.
Do not rerun research.
Do not create strategy, holdout, paper live, preregistration, real trading, or Codex CLI usage.
Use only real workspace files, no scratch/mock/devnull for final outputs.

Required versioning:
- version = V1.46.1
- previous_base = V1.46
- feature_ablation_base_version = V1.45.1
- regime_aware_feature_base_version = V1.44.4
- regime_feature_base_version = V1.43.4
- payoff_target_base_version = V1.42.3
- payoff_failure_base_version = V1.41
- ev_degradation_base_version = V1.39
- canonical_base_version = V1.37.2

Keep:
- final_verdict = REGIME_DATA_QUALITY_INCONCLUSIVE
- recommended_next_step = improve data enrichment / regime labels before new modeling
- evidence_classification = RESEARCH_ONLY
- no_new_filter = true
- no_strategy_validated = true
- no_preregistration_yet = true
- no_paper_live = true
- no_real_trading = true
- holdout_executed = false
- codex_cli_called = false
- release_ready_for_external_review = true
- best_regime_label_candidates = ["vol_regime"]
- weak_regime_label_candidates = ["trend_regime"]
- high_priority_enrichment_gaps = ["microstructure"]

Reports to create or migrate to V1.46.1:
- regime_data_quality_input_guard_v1_46_1.json/md
- regime_label_inventory_v1_46_1.json/md
- regime_label_quality_v1_46_1.json/md
- regime_proxy_quality_v1_46_1.json/md
- regime_temporal_coverage_audit_v1_46_1.json/md
- regime_missingness_audit_v1_46_1.json/md
- regime_feature_enrichment_gap_analysis_v1_46_1.json/md
- regime_separability_analysis_v1_46_1.json/md
- regime_transition_analysis_v1_46_1.json/md
- regime_label_stability_v1_46_1.json/md
- regime_causal_availability_audit_v1_46_1.json/md
- regime_data_enrichment_recommendation_v1_46_1.json/md
- regime_data_quality_summary_v1_46_1.json/md
- regime_data_quality_consistency_check_v1_46_1.json/md
- v1_46_1_recommendation.json/md
- docs/regime_data_quality_research_v1_46_1.md

Must validate:
- no NaN/Infinity in JSON;
- required JSON and MD reports present;
- PROJECT_STATE and latest metrics aligned;
- consistency check has `issues = []` and the explicit alignment fields above;
- zip excludes `data/`, `scratch/`, `.venv/`, caches, secrets, parquet/csv/jsonl/db/sqlite.

Expected final artifacts:
- `projet-galapagos-v1.46.1-clean.zip`
- `reports/release_zip_v1_46_1.json/md`
- `reports/zip_audit_v1_46_1.json/md`
- `reports/zip_smoke_test_v1_46_1.json/md`

Run:
1. `pytest` for regime_data_quality and related validators.
2. `ruff check src/galapagos/research/regime_data_quality scripts/validate_regime_data_quality_reports.py` if available.
3. `python scripts/validate_regime_data_quality_reports.py --version v1.46.1`
4. `python scripts/release_clean_zip.py --version v1.46.1`

Return only a factual report with:
- model used;
- whether fallback was used;
- number of Gemini CLI calls;
- tests;
- zip path;
- audit/smoke;
- safety status;
- confirmation that no trading-related behavior was added.

If blocked, return `V1461_BLOCKED`.
