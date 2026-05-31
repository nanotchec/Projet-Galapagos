# Commandes V9.46

- `git branch --show-current` -> `0` : main
- `git status --short --branch` -> `0` : ## main...origin/main [ahead 2]
- `PYTHONPATH=src python -m pytest -q tests/features/test_aggtrades_exact_5y_feature_enrichment_validation_v9_46.py` -> `0` : 5 passed in 0.28s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_exact_5y_feature_enrichment_validation_v9_46_validator.py` -> `0` : 3 passed in 0.29s
- `python scripts/run_aggtrades_exact_5y_feature_enrichment_validation_v9_46.py` -> `0` : decision=aggtrades_exact_5y_feature_enrichment_validated_with_non_blocking_warnings; validation_mode=full-local; quality_status=PASS; runtime_seconds=2.84
- `PYTHONPATH=src python -m pytest --collect-only -q` -> `0` : 5762 tests collected in 1.85s
- `PYTHONPATH=src python -m pytest -q tests/features/test_aggtrades_exact_5y_feature_enrichment_validation_v9_46.py` -> `0` : 5 passed in 0.28s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_exact_5y_feature_enrichment_validation_v9_46_validator.py` -> `0` : 3 passed in 0.29s
- `python scripts/validate_aggtrades_exact_5y_feature_enrichment_validation_v9_46.py` -> `0` : passed=true; errors=[]
- `python scripts/release_audit_lite_zip_v9_46.py` -> `0` : PASS; included_files=46; no sidecars; no ZIP fingerprints
- `python scripts/audit_audit_lite_zip_v9_46.py --zip projet-galapagos-v9.46-audit-lite.zip` -> `0` : passed=true; errors=[]
- `python scripts/smoke_audit_lite_zip_v9_46.py --zip projet-galapagos-v9.46-audit-lite.zip` -> `1` : initial smoke failed because V9.45 support modules were missing from audit-lite ZIP; packaging corrected
- `python scripts/release_audit_lite_zip_v9_46.py` -> `0` : PASS; included_files=48 after adding required V9.45 support modules
- `python scripts/audit_audit_lite_zip_v9_46.py --zip projet-galapagos-v9.46-audit-lite.zip` -> `0` : passed=true; errors=[]
- `python scripts/smoke_audit_lite_zip_v9_46.py --zip projet-galapagos-v9.46-audit-lite.zip` -> `0` : passed=true; errors=[]; sample_checks_passed=true; full_dataset_required=false

- Aucun sidecar et aucune empreinte ZIP.
