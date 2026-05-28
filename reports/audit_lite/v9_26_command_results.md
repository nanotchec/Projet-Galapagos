# Commandes V9.26

- `git branch --show-current` : `PASS` - main
- `git status --short --branch` : `PASS` - initial clean state: ## main...origin/main [ahead 8]
- `df -h /Users/lilianserre/Documents/projets/projet-galapagos` : `PASS` - project mount /System/Volumes/Data; free 59.862 GiB
- `df -h /Users/lilianserre/Documents/projets/projet-galapagos/data || true` : `PASS` - data mount /System/Volumes/Data; free 59.862 GiB
- `du -sh /Users/lilianserre/Documents/projets/projet-galapagos/data/raw 2>/dev/null || true` : `PASS` - raw_bytes_current=10563620520
- `du -sh /Users/lilianserre/Documents/projets/projet-galapagos/data/silver 2>/dev/null || true` : `PASS` - silver_bytes_current=10552728837
- `du -sh /Users/lilianserre/Documents/projets/projet-galapagos/data/quarantine 2>/dev/null || true` : `PASS` - quarantine_bytes_current=405010278
- `PYTHONPATH=src python -m pytest --collect-only -q` : `PASS` - 5557 tests collected in 3.37s
- `PYTHONPATH=src python -m pytest -q tests/data/test_aggtrades_post_v9_storage_resume_campaign_v9_26.py` : `PASS` - 7 passed in 0.03s
- `PYTHONPATH=src python -m pytest -q tests/validation/test_aggtrades_post_v9_storage_resume_campaign_v9_26_validator.py` : `PASS` - 4 passed in 0.04s
- `python scripts/run_aggtrades_post_v9_storage_resume_campaign_v9_26.py` : `PASS` - resume_collection_not_executed_storage_blocker; no network; no download; no ingestion
- `python scripts/validate_aggtrades_post_v9_storage_resume_campaign_v9_26.py` : `PASS` - V9.26 validation passed with no errors
- `python scripts/release_audit_lite_zip_v9_26.py` : `PASS` - audit-lite ZIP built; no sidecars or ZIP fingerprints; zip_bytes_estimate is non-authoritative
- `python scripts/audit_audit_lite_zip_v9_26.py --zip projet-galapagos-v9.26-audit-lite.zip` : `PASS` - ZIP audit passed with no errors
- `python scripts/smoke_audit_lite_zip_v9_26.py --zip projet-galapagos-v9.26-audit-lite.zip` : `PASS` - ZIP smoke passed with imports, collect-only, tests and self-audit

- Aucun sidecar et aucune empreinte ZIP crees.
