# Commandes V9.45

- `git branch --show-current` -> `0` : main
- `git status --short --branch` -> `0` : initial clean before V9.45; current V9.45 files pending
- `GALAPAGOS_V9_45_WORKERS=12 python scripts/run_aggtrades_exact_5y_feature_enrichment_v9_45.py` -> `0` : completed long 12-core feature generation; first report was partial due signed-imbalance validation bug; feature files written
- `PYTHONPATH=src python -m pytest -q tests/features/test_aggtrades_exact_5y_feature_enrichment_v9_45.py` -> `0` : 5 passed in 0.37s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_exact_5y_feature_enrichment_v9_45_validator.py` -> `0` : 3 passed in 0.29s
- `python scripts/run_aggtrades_exact_5y_feature_enrichment_v9_45.py` -> `0` : reused existing feature files, refreshed reports; decision=aggtrades_exact_5y_feature_enrichment_created_with_warnings; quality_status=PASS; runtime_seconds=1.327
- `PYTHONPATH=src python -m pytest --collect-only -q` -> `0` : 5754 tests collected in 2.42s
- `PYTHONPATH=src python -m pytest -q tests/features/test_aggtrades_exact_5y_feature_enrichment_v9_45.py` -> `0` : 5 passed in 0.37s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_exact_5y_feature_enrichment_v9_45_validator.py` -> `0` : 3 passed in 0.29s
- `python scripts/validate_aggtrades_exact_5y_feature_enrichment_v9_45.py` -> `0` : passed=true; errors=[]
- `python scripts/release_audit_lite_zip_v9_45.py` -> `0` : PASS; included_files=46; no sidecars; no ZIP fingerprints
- `python scripts/release_audit_lite_zip_v9_45.py` -> `0` : PASS; included_files=46; no sidecars; no ZIP fingerprints; regenerated after command_results update
- `python scripts/audit_audit_lite_zip_v9_45.py --zip projet-galapagos-v9.45-audit-lite.zip` -> `0` : passed=true; errors=[]
- `python scripts/smoke_audit_lite_zip_v9_45.py --zip projet-galapagos-v9.45-audit-lite.zip` -> `0` : passed=true; errors=[]; full_dataset_required=false
- `git diff --check` -> `0` : no whitespace errors

- Aucun sidecar et aucune empreinte ZIP.
