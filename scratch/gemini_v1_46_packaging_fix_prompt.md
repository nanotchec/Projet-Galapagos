Corrige uniquement la release V1.46.

Etat observe par Codex :
- Les rapports `reports/research/*v1_46*.json/md` existent dans le workspace.
- `projet-galapagos-v1.46-clean.zip` existe mais n'inclut aucun rapport `reports/research/*v1_46*`.
- `reports/release_zip_v1_46.json` indique `recommendation_json_included=false`, `recommendation_md_included=false`, `final_smoke_passed=false`, `release_ready_for_external_review=false`.
- Le smoke test echoue dans le zip sur `scripts/validate_regime_data_quality_reports.py --version V1.46`, probablement parce que les rapports V1.46 manquent dans l'archive.

Tache stricte :
1. Mettre a jour le packaging pour inclure tous les rapports V1.46 demandes :
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
2. Regenerer :
   - `python scripts/validate_regime_data_quality_reports.py --version v1.46`
   - `python scripts/release_clean_zip.py --version v1.46`
3. Verifier que :
   - `reports/release_zip_v1_46.json` a `release_ready_for_external_review=true`
   - `reports/zip_audit_v1_46.json` a `forbidden_count=0`, `secret_hits=[]`, `missing_required_files=[]`
   - `reports/zip_smoke_test_v1_46.json` a `smoke_test_passed=true`
   - `unzip -l projet-galapagos-v1.46-clean.zip` montre les rapports V1.46.

Ne change pas la recherche de fond.
Ne cree pas de strategie.
Ne fais pas de holdout.
Ne passe aucun ordre reel.
Ne lance pas Codex CLI.
Si tu es bloque, reponds `PACKAGING_FIX_BLOCKED`.
