Tu es dans le projet local `/Users/lilianserre/Documents/projets/projet-galapagos`.

Tu dois implementer Galapagos V1.46 : Data Enrichment + Regime Label Quality Research.

Contraintes absolues :
- Aucun ordre reel.
- Aucun Codex CLI.
- Aucun holdout.
- Aucun reviewer LLM.
- Aucun reseau.
- Aucun capital reel.
- Aucun paper live.
- Aucun pre-enregistrement.
- Aucun nouveau filtre declare valide.
- Aucun seuil optimise presente comme strategie.
- Aucun resultat invente.
- Evidence classification = RESEARCH_ONLY ou DIAGNOSTIC_ONLY.
- Code en anglais technique.
- Rapports/docs en francais.
- Zip clean + audit + smoke final via pipeline standard.
- Zip attendu : `projet-galapagos-v1.46-clean.zip`.

Base validee V1.45.1 :
- version = V1.45.1
- previous_base = V1.45
- regime_aware_feature_base_version = V1.44.4
- regime_feature_base_version = V1.43.4
- payoff_target_base_version = V1.42.3
- payoff_failure_base_version = V1.41
- ev_degradation_base_version = V1.39
- canonical_base_version = V1.37.2
- final_verdict = FEATURE_ABLATION_IMPORTANCE_RESEARCH_INCONCLUSIVE
- recommended_next_step = improve data enrichment / regime labels before new modeling
- evidence_classification = RESEARCH_ONLY
- consistency_check_status = FEATURE_ABLATION_IMPORTANCE_REPORTS_CONSISTENT_RESEARCH_ONLY
- input_guard_status = FEATURE_ABLATION_INPUT_GUARD_PASSED
- source_contract_status = FEATURE_ABLATION_SOURCE_CONTRACT_PASSED
- best_family_observed = regime_proxy
- worst_family_observed = alpha_score_family
- stable_families = microstructure, price_return, regime_proxy, trend_momentum, volatility, volume_liquidity, other_remaining
- unstable_families = alpha_score_family
- recommended_keep_for_next_research = microstructure, price_return, regime_proxy, trend_momentum, volatility, volume_liquidity, other_remaining
- recommended_drop_or_rework = alpha_score_family
- improves_over_v1_44_4 = false
- no_new_filter = true
- no_strategy_validated = true
- no_preregistration_yet = true
- no_paper_live = true
- no_real_trading = true
- holdout_executed = false
- codex_cli_called = false

Objectif V1.46 :
Creer une phase de recherche DIAGNOSTIC_ONLY / RESEARCH_ONLY pour evaluer et ameliorer la qualite :
1. des labels de regime ;
2. des proxies de regime ;
3. de l'enrichissement des donnees causales disponibles ;
4. de la couverture temporelle et des trous de donnees ;
5. des features candidates a enrichir avant de relancer un modele.

Lis avant de coder :
- reports/PROJECT_STATE.json
- reports/PROJECT_STATE.md
- reports/current/latest_metrics.json
- reports/current/latest_summary.md
- reports/research/feature_ablation_input_guard_v1_45_1.json
- reports/research/feature_ablation_source_contract_v1_45_1.json
- reports/research/feature_ablation_family_registry_v1_45_1.json
- reports/research/feature_ablation_plan_v1_45_1.json
- reports/research/feature_ablation_results_v1_45_1.json
- reports/research/feature_permutation_importance_v1_45_1.json
- reports/research/feature_temporal_importance_v1_45_1.json
- reports/research/feature_regime_importance_v1_45_1.json
- reports/research/feature_ablation_stability_audit_v1_45_1.json
- reports/research/feature_ablation_leakage_safety_audit_v1_45_1.json
- reports/research/feature_ablation_baseline_comparison_v1_45_1.json
- reports/research/feature_importance_scorecard_v1_45_1.json
- reports/research/feature_ablation_importance_summary_v1_45_1.json
- reports/research/feature_ablation_importance_consistency_check_v1_45_1.json
- reports/research/v1_45_1_recommendation.json
- reports/research/regime_aware_feature_set_summary_v1_44_4.json
- reports/research/regime_aware_feature_source_contract_v1_44_4.json
- reports/research/regime_aware_feature_sets_v1_44_4.json
- reports/research/regime_feature_diagnostic_summary_v1_43_4.json
- reports/research/regime_feature_inventory_v1_43_4.json
- reports/research/regime_feature_stability_scorecard_v1_43_4.json
- reports/research/payoff_target_research_summary_v1_42_3.json
- reports/research/payoff_objective_failure_diagnostic_summary_v1_41.json
- reports/research/ev_degradation_diagnostic_summary_v1_39.json
- reports/research/canonical_universe_summary_v1_37_2.json

Donnees reelles a utiliser uniquement :
- data/gold/ml_predictions/BTC/4h/ml_predictions_v1_16_3.parquet
- data/gold/research_dataset/BTC/4h/research_dataset.parquet
- data/gold/research_dataset/BTC/4h/research_dataset_with_alpha_scores.parquet
- data/silver/intrabar/binance/BTCUSDT/5m/history_5m_v1_22.parquet

Ne jamais utiliser mock/scratch/devnull/tmp/test parquet pour les resultats finaux.

Creer le package :
`src/galapagos/research/regime_data_quality/`
avec :
- __init__.py
- data_loader.py
- input_guard.py
- regime_label_inventory.py
- regime_label_quality.py
- regime_proxy_quality.py
- temporal_coverage_audit.py
- missingness_audit.py
- feature_enrichment_gap_analysis.py
- regime_separability_analysis.py
- regime_transition_analysis.py
- regime_label_stability.py
- causal_availability_audit.py
- enrichment_recommendation_engine.py
- diagnostic_verdict.py
- report_writer.py

Creer les scripts :
- scripts/run_regime_data_quality_research.py
- scripts/validate_regime_data_quality_reports.py

Rapports JSON + MD obligatoires :
- reports/research/regime_data_quality_input_guard_v1_46.json/md
- reports/research/regime_label_inventory_v1_46.json/md
- reports/research/regime_label_quality_v1_46.json/md
- reports/research/regime_proxy_quality_v1_46.json/md
- reports/research/regime_temporal_coverage_audit_v1_46.json/md
- reports/research/regime_missingness_audit_v1_46.json/md
- reports/research/regime_feature_enrichment_gap_analysis_v1_46.json/md
- reports/research/regime_separability_analysis_v1_46.json/md
- reports/research/regime_transition_analysis_v1_46.json/md
- reports/research/regime_label_stability_v1_46.json/md
- reports/research/regime_causal_availability_audit_v1_46.json/md
- reports/research/regime_data_enrichment_recommendation_v1_46.json/md
- reports/research/regime_data_quality_summary_v1_46.json/md
- reports/research/regime_data_quality_consistency_check_v1_46.json/md
- reports/research/v1_46_recommendation.json/md
- docs/regime_data_quality_research_v1_46.md

Contenu attendu :

Input guard :
- feature_ablation_base_version = V1.45.1
- regime_aware_feature_base_version = V1.44.4
- regime_feature_base_version = V1.43.4
- payoff_target_base_version = V1.42.3
- payoff_failure_base_version = V1.41
- ev_degradation_base_version = V1.39
- canonical_base_version = V1.37.2
- V1.45.1 final_verdict = FEATURE_ABLATION_IMPORTANCE_RESEARCH_INCONCLUSIVE
- V1.45.1 consistency_check_status = FEATURE_ABLATION_IMPORTANCE_REPORTS_CONSISTENT_RESEARCH_ONLY
- V1.45.1 no_strategy_validated = true
- V1.45.1 no_preregistration_yet = true
- V1.45.1 no_paper_live = true
- V1.45.1 no_real_trading = true
- holdout_executed = false
- codex_cli_called = false
- data paths reels uniquement
- no mock/scratch/devnull
- input_guard_status = REGIME_DATA_QUALITY_INPUT_GUARD_PASSED

Regime label inventory :
- identifier les colonnes/proxies de regime possibles ;
- categoriser : volatility_regime_proxy, trend_regime_proxy, liquidity_regime_proxy, volume_regime_proxy, momentum_regime_proxy, funding_or_derivatives_proxy, alpha_score_proxy, unknown_or_unclassified ;
- exclure outcomes, forward returns, MFE/MAE, targets, model outputs, EV proxies.

Regime label quality :
- label_balance, label_entropy, regime_persistence, transition_rate, average_duration, short_lived_regime_rate, regime_flip_rate, missing_label_rate, 2026_label_distribution_shift.

Regime proxy quality :
- redondance, drift, outlier sensitivity, causal availability, stabilite pre-2026 vs 2026.

Temporal coverage / missingness :
- coverage_by_year, coverage_by_month, missing_months, sparse_periods, data_gap_count, missing_rate_by_feature, missing_rate_by_family, missingness_2026_vs_history.

Feature enrichment gap analysis :
- volatility, liquidity, trend, microstructure, funding/derivatives, macro proxy, session/time features, cross-asset context, regime transitions.

Regime separability / transitions / stability :
- separabilite des regimes, overlap, transitions frequentes, transitions liees aux pertes 2026, stabilite des labels dans le temps.

Causal availability audit :
- forbidden_columns_used = []
- model_outputs_used = []
- ev_proxies_used = []
- outcome_columns_used = []
- future_columns_used = []
- causal_availability_status = REGIME_CAUSAL_AVAILABILITY_PASSED

Recommendation :
- recommended_regime_labels_to_keep
- recommended_regime_labels_to_rework
- recommended_regime_labels_to_drop
- recommended_feature_gaps_high_priority
- recommended_data_enrichment_next
- recommended_next_research_step

Summary V1.46 obligatoire :
- version = V1.46
- feature_ablation_base_version = V1.45.1
- regime_aware_feature_base_version = V1.44.4
- regime_feature_base_version = V1.43.4
- payoff_target_base_version = V1.42.3
- payoff_failure_base_version = V1.41
- ev_degradation_base_version = V1.39
- canonical_base_version = V1.37.2
- input_guard_status
- regime_label_inventory_status
- regime_label_quality_status
- regime_proxy_quality_status
- temporal_coverage_status
- missingness_status
- enrichment_gap_status
- separability_status
- transition_status
- label_stability_status
- causal_availability_status
- recommendation_status
- best_regime_label_candidates
- weak_regime_label_candidates
- high_priority_enrichment_gaps
- final_verdict
- recommended_next_step
- evidence_classification = RESEARCH_ONLY ou DIAGNOSTIC_ONLY
- no_new_filter = true
- no_strategy_validated = true
- no_preregistration_yet = true
- no_paper_live = true
- no_real_trading = true
- holdout_executed = false
- codex_cli_called = false

Verdicts possibles :
- REGIME_DATA_QUALITY_ACTIONABLE_BUT_UNVALIDATED
- REGIME_DATA_QUALITY_INCONCLUSIVE
- REGIME_DATA_QUALITY_WEAK
- REGIME_DATA_QUALITY_BLOCKED_BY_COVERAGE

Validator :
Creer `scripts/validate_regime_data_quality_reports.py`.
Il doit produire `reports/research/regime_data_quality_consistency_check_v1_46.json/md` avec :
`consistency_check_status = REGIME_DATA_QUALITY_REPORTS_CONSISTENT_DIAGNOSTIC_ONLY`
Il doit echouer si :
- V1.45.1 pas alignee ;
- rapport obligatoire manquant ;
- JSON avec NaN/Infinity ;
- causal availability failed ;
- forbidden column utilisee ;
- model output utilisee comme regime principal ;
- EV proxy utilisee ;
- outcome utilisee ;
- final_verdict contient VALIDATED ;
- recommended_next_step contient preregistration / paper live / real trading ;
- no_strategy_validated != true ;
- no_preregistration_yet != true ;
- no_paper_live != true ;
- no_real_trading != true ;
- holdout_executed != false ;
- codex_cli_called != false ;
- PROJECT_STATE/latest divergents.

Mettre a jour :
- reports/PROJECT_STATE.json
- reports/PROJECT_STATE.md
- reports/current/latest_metrics.json
- reports/current/latest_summary.md
- reports/implementation_report.md
- reports/REPORT_INDEX.md

Packaging :
Mettre a jour si necessaire :
- scripts/make_clean_zip.py
- scripts/audit_clean_zip.py
- scripts/release_clean_zip.py
- scripts/smoke_test_clean_zip.py
Le zip V1.46 doit inclure tous les rapports V1.46, la doc, PROJECT_STATE, latest, release/audit/smoke, v1_46_recommendation.
Exclure data/, .venv/, caches/, secrets/, parquet/csv/jsonl/db/sqlite.

Tests a ajouter :
- input guard rejects missing V1.45.1.
- causal availability rejects future/outcome/model output/EV proxy.
- validator rejects VALIDATED verdict.
- validator rejects preregistration next step.
- validator rejects paper live true.
- validator rejects real trading true.
- validator rejects holdout true.
- validator rejects NaN/Infinity.
- no Codex CLI.
- no real trading.

Execution obligatoire :
1. pytest tests lies a regime_data_quality et validateurs.
2. Si disponible : `ruff check src/galapagos/research/regime_data_quality scripts/validate_regime_data_quality_reports.py`
3. Lancer :
python scripts/run_regime_data_quality_research.py \
  --predictions data/gold/ml_predictions/BTC/4h/ml_predictions_v1_16_3.parquet \
  --dataset data/gold/research_dataset/BTC/4h/research_dataset.parquet \
  --alpha-dataset data/gold/research_dataset/BTC/4h/research_dataset_with_alpha_scores.parquet \
  --intrabar data/silver/intrabar/binance/BTCUSDT/5m/history_5m_v1_22.parquet \
  --feature-ablation-summary reports/research/feature_ablation_importance_summary_v1_45_1.json \
  --feature-ablation-scorecard reports/research/feature_importance_scorecard_v1_45_1.json \
  --regime-aware-summary reports/research/regime_aware_feature_set_summary_v1_44_4.json \
  --regime-feature-inventory reports/research/regime_feature_inventory_v1_43_4.json \
  --canonical-summary reports/research/canonical_universe_summary_v1_37_2.json \
  --version v1.46
4. `python scripts/validate_regime_data_quality_reports.py --version v1.46`
5. `python scripts/release_clean_zip.py --version v1.46`

Rapport final attendu de toi :
- targeted_tests_status
- ruff
- version
- feature_ablation_base_version
- regime_aware_feature_base_version
- regime_feature_base_version
- payoff_target_base_version
- payoff_failure_base_version
- ev_degradation_base_version
- canonical_base_version
- input_guard_status
- regime_label_inventory_status
- regime_label_quality_status
- regime_proxy_quality_status
- temporal_coverage_status
- missingness_status
- enrichment_gap_status
- separability_status
- transition_status
- label_stability_status
- causal_availability_status
- recommendation_status
- best_regime_label_candidates
- weak_regime_label_candidates
- high_priority_enrichment_gaps
- final_verdict
- recommended_next_step
- evidence_classification
- consistency_check_status
- no_new_filter
- no_strategy_validated
- no_preregistration_yet
- no_paper_live
- no_real_trading
- holdout_executed
- codex_cli_called
- zip path
- forbidden_count
- secret_hits
- missing_required_files
- smoke_test_passed
- release_ready_for_external_review
- Gemini model used = gemini-3.1-pro
- Gemini fallback used = false
- Codex CLI non appele
- holdout non execute
- aucun ordre reel
- confirmation : "Le systeme V1.46 ne peut toujours pas passer d'ordre reel."

Ne dis jamais qu'une strategie est validee. Ne propose pas de paper live. Ne propose pas d'argent reel.
