Implement Galapagos V1.46.3 in /Users/lilianserre/Documents/projets/projet-galapagos.

Goal: fix recommendation alignment only, without rerunning research.

Requirements:
- Create V1.46.3 reports and update PROJECT_STATE/latest/docs/release artifacts.
- Set version=V1.46.3 and previous_base=V1.46.2 everywhere relevant.
- Keep scientific results unchanged from V1.46.2.
- Canonical recommendation must be exactly:
  high_priority_enrichment_gaps=["microstructure"]
  recommended_feature_gaps_high_priority=["microstructure"]
  recommended_data_enrichment_next="improve microstructure regime features"
  recommended_next_research_step="improve data enrichment / regime labels before new modeling"
  recommended_next_step="improve data enrichment / regime labels before new modeling"
- Update summary, PROJECT_STATE, latest_metrics, latest_summary, recommendation JSON/MD, consistency check JSON/MD, docs.
- Hard-enforce the recommendation alignment in scripts/validate_regime_data_quality_reports.py.
- Regenerate clean zip, audit, smoke for projet-galapagos-v1.46.3-clean.zip.

Constraints:
- No new research.
- No strategy validation.
- No paper live.
- No preregistration.
- No real trading.
- No holdout.
- No Codex CLI.
- No network.
- Keep evidence classification RESEARCH_ONLY or DIAGNOSTIC_ONLY.

Return only the concrete implementation and release artifacts.
