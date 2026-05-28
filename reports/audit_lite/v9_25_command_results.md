# Commandes V9.25

- `git branch --show-current` : `PASS` - main
- `git status --short --branch` : `PASS` - ## main...origin/main [ahead 6]
- `PYTHONPATH=src python -m pytest --collect-only -q` : `PASS` - 5532 tests collected in 2.40s
- `PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_post_v9_completion_campaign_v9_25.py` : `PASS` - 10 passed in 0.33s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_post_v9_completion_campaign_v9_25_validator.py` : `PASS` - 7 passed in 0.04s
- `python scripts/run_aggtrades_post_v9_completion_campaign_v9_25.py` : `PASS` - decision=aggtrades_post_v9_remaining_window_collection_failed_storage; batches_executed=1; days_downloaded=57; days_normalized=57; days_complete=57; coverage=2024-05-05->2025-02-02; complete_collection_reached=False; storage_warning=free_disk_below_60gb_stop_before_collection
- `python scripts/validate_aggtrades_post_v9_completion_campaign_v9_25.py` : `PASS` - passed=true; errors=[]
- `python scripts/release_audit_lite_zip_v9_25.py` : `PASS` - zip=projet-galapagos-v9.25-audit-lite.zip; included_files=58; zip_bytes_is_authoritative=false; no sidecars; no ZIP fingerprints
- `python scripts/audit_audit_lite_zip_v9_25.py --zip projet-galapagos-v9.25-audit-lite.zip` : `PASS` - passed=true; errors=[]
- `python scripts/smoke_audit_lite_zip_v9_25.py --zip projet-galapagos-v9.25-audit-lite.zip` : `PASS` - passed=true; errors=[]; import_timeout=20s; pytest_collect_timeout=60s; tests_timeout=90s; audit_timeout=30s

Decision campagne : `aggtrades_post_v9_remaining_window_collection_failed_storage`.
Couverture locale : `2024-05-05` -> `2025-02-02`.
- Aucun sidecar et aucune empreinte ZIP.
