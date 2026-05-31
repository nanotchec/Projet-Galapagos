# Commandes V9.44

- `PYTHONPATH=src python -m pytest --collect-only -q` -> `5746 tests collected in 2.41s` (code `0`).
- `PYTHONPATH=src python -m pytest -q tests/research/test_ohlcv_aggtrades_5y_ml_diagnostic_v9_44.py` -> `3 passed in 0.04s` (code `0`).
- `PYTHONPATH=src python -m pytest -q tests/validation/test_ohlcv_aggtrades_5y_ml_diagnostic_v9_44_validator.py` -> `3 passed in 0.02s` (code `0`).
- `python scripts/run_ohlcv_aggtrades_5y_ml_diagnostic_v9_44.py` -> `decision=feature_enrichment_before_more_ml; baseline_clear_wins_count=0; no_clear_edge_vs_shuffled_labels_count=15` (code `0`).
- `python scripts/validate_ohlcv_aggtrades_5y_ml_diagnostic_v9_44.py` -> `passed=true; errors=[]` (code `0`).
- `python scripts/release_audit_lite_zip_v9_44.py` -> `PASS; included_files=41; zip_bytes_estimate=174538` (code `0`).
- `python scripts/audit_audit_lite_zip_v9_44.py --zip projet-galapagos-v9.44-audit-lite.zip` -> `passed=true; errors=[]` (code `0`).
- `python scripts/smoke_audit_lite_zip_v9_44.py --zip projet-galapagos-v9.44-audit-lite.zip` -> `passed=true; errors=[]; full_dataset_required=false` (code `0`).
- Aucun sidecar et aucune empreinte ZIP.
