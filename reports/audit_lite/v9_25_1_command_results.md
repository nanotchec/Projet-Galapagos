# Commandes V9.25.1

- `git branch --show-current` : `PASS` - main
- `git status --short --branch` : `PASS` - working tree V9.25 dirty repaired by local commit 6b537ae4, then V9.25.1 started from clean state ahead 7
- `PYTHONPATH=src python -m pytest --collect-only -q` : `PASS` - 5546 tests collected in 4.03s
- `PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_post_v9_resume_campaign_v9_25_1.py` : `PASS` - 7 passed in 0.05s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_post_v9_resume_campaign_v9_25_1_validator.py` : `PASS` - 7 passed in 0.05s
- `python scripts/run_aggtrades_post_v9_resume_campaign_v9_25_1.py` : `PASS` - resume_collection_partial_storage_warning; downloaded/normalized/validated 1 day; local coverage 2024-05-05 -> 2025-02-03
- `python scripts/validate_aggtrades_post_v9_resume_campaign_v9_25_1.py` : `PASS` - V9.25.1 validation passed with no errors
- `python scripts/release_audit_lite_zip_v9_25_1.py` : `PASS` - audit-lite ZIP built; no sidecars or ZIP fingerprints; zip_bytes_estimate is non-authoritative
- `python scripts/audit_audit_lite_zip_v9_25_1.py --zip projet-galapagos-v9.25.1-audit-lite.zip` : `PASS` - ZIP audit passed with no errors
- `python scripts/smoke_audit_lite_zip_v9_25_1.py --zip projet-galapagos-v9.25.1-audit-lite.zip` : `PASS` - ZIP smoke passed with imports, collect-only, tests and self-audit

- Aucun sidecar et aucune empreinte ZIP crees.
