Corrige uniquement le reporting V1.46, sans changer la recherche.

Problemes observes :
1. `reports/PROJECT_STATE.json` et `reports/current/latest_metrics.json` sont trop pauvres. Ils contiennent seulement version/previous_base/no_real_trading/holdout/codex/evidence. Ils doivent inclure les champs du summary V1.46.
2. `reports/research/v1_46_recommendation.json` ne contient pas les champs de securite obligatoires.

Tache :
- Lire `reports/research/regime_data_quality_summary_v1_46.json`.
- Mettre a jour `reports/PROJECT_STATE.json`, `reports/PROJECT_STATE.md`, `reports/current/latest_metrics.json`, `reports/current/latest_summary.md`.
- Mettre a jour `reports/research/v1_46_recommendation.json/md`.
- Regenerer `python scripts/validate_regime_data_quality_reports.py --version v1.46`.
- Regenerer `python scripts/release_clean_zip.py --version v1.46`.

Champs minimum attendus dans PROJECT_STATE.json et latest_metrics.json :
- version = V1.46
- previous_base = V1.45.1
- feature_ablation_base_version = V1.45.1
- regime_aware_feature_base_version = V1.44.4
- regime_feature_base_version = V1.43.4
- payoff_target_base_version = V1.42.3
- payoff_failure_base_version = V1.41
- ev_degradation_base_version = V1.39
- canonical_base_version = V1.37.2
- final_verdict = REGIME_DATA_QUALITY_INCONCLUSIVE
- recommended_next_step
- evidence_classification = RESEARCH_ONLY
- consistency_check_status = REGIME_DATA_QUALITY_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY
- input_guard_status = REGIME_DATA_QUALITY_INPUT_GUARD_PASSED
- causal_availability_status = REGIME_CAUSAL_AVAILABILITY_PASSED
- no_new_filter = true
- no_strategy_validated = true
- no_preregistration_yet = true
- no_paper_live = true
- no_real_trading = true
- holdout_executed = false
- codex_cli_called = false
- release_ready_for_external_review = true
- status_field_policy = REMOVED
- status_field_present = false

Champs minimum attendus dans v1_46_recommendation.json :
- version = V1.46
- recommended_next_step
- evidence_classification = RESEARCH_ONLY
- no_new_filter = true
- no_strategy_validated = true
- no_preregistration_yet = true
- no_paper_live = true
- no_money_deployment = true
- no_real_trading = true
- holdout_executed = false
- codex_cli_called = false
- release_ready_for_external_review = true

Ne pas dire strategie validee.
Ne pas proposer paper live.
Ne pas proposer argent reel.
Ne pas appeler Codex CLI.
Ne pas executer holdout.
Ne pas passer d'ordre reel.
